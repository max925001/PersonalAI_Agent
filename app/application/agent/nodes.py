import uuid
import re
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from loguru import logger
from app.application.agent.state import AgentState
from app.application.agent.prompts import SYSTEM_INSTRUCTION, RAG_PROMPT_TEMPLATE, SLOT_EXTRACTION_PROMPT
from app.application.chat.retriever_service import RetrieverService
from app.application.chat.memory_service import MemoryService
from app.application.chat.rag_service import RAGService
from app.application.interfaces.llm_port import ILLMPort

class AgentNodes:
    """Class encapsulating all LangGraph node functions with injected dependency services."""

    def __init__(
        self,
        retriever_service: RetrieverService,
        memory_service: MemoryService,
        rag_service: RAGService,
        llm_port: ILLMPort,
        scheduling_service: Any = None,
        profile_repo: Any = None
    ):
        self.retriever_service = retriever_service
        self.memory_service = memory_service
        self.rag_service = rag_service
        self.llm_port = llm_port
        self.scheduling_service = scheduling_service
        self.profile_repo = profile_repo

    async def load_memory(self, state: AgentState) -> Dict[str, Any]:
        logger.info(f"Loading chat history for session: {state['session_id']}")
        session_uuid = uuid.UUID(state["session_id"])
        history = await self.memory_service.load_chat_history(session_uuid)
        return {"chat_history": history}

    async def detect_intent(self, state: AgentState) -> Dict[str, Any]:
        """Classifies request intent into greeting, schedule_list, schedule_book, or RAG path.

        Priority order:
          1. Greeting  — short messages with a greeting word
          2. RAG override — if the message is primarily asking about Shivam (experience,
             skills, projects, etc.), route to RAG even if 'interview'/'schedule' appears
          3. Schedule-book — scheduling keywords + a specific date/time
          4. Schedule-list — scheduling keywords with no info-seeking phrases
          5. RAG (default)
        """
        msg_lower = state["message"].lower().strip()
        words = msg_lower.split()

        # ── 1. Greeting ──────────────────────────────────────────────────────
        greetings = ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening"]
        if len(words) <= 3 and any(w in msg_lower for w in greetings):
            logger.info("Detected greeting intent.")
            return {"intent": "greeting"}

        # ── 2. RAG-priority check ────────────────────────────────────────────
        # These phrases indicate the user is asking ABOUT Shivam, even if they
        # also mention "interview" or "schedule" in passing.
        rag_priority_phrases = [
            "tell me about", "know more about", "know about",
            "experience", "skills", "projects", "background",
            "qualification", "education", "resume", "portfolio",
            "what does", "what did", "who is", "describe",
            "worked on", "built", "technologies", "tech stack",
            "strengths", "expertise", "certifications", "achievements",
            "give details", "give me details", "more about shivam",
            "about him", "about his", "before schedul", "before interview",
            "want to know", "learn about", "interested in knowing",
        ]
        has_rag_signal = any(phrase in msg_lower for phrase in rag_priority_phrases)

        # ── 3. Schedule detection ────────────────────────────────────────────
        schedule_keywords = ["schedule", "availab", "book", "slot"]
        # "interview" alone is too ambiguous — only count it when it's the
        # primary action, not when paired with info-seeking phrases.
        has_schedule_keyword = any(w in msg_lower for w in schedule_keywords)
        # Also treat standalone "interview" as schedule ONLY if no RAG signal
        if not has_schedule_keyword and "interview" in msg_lower and not has_rag_signal:
            has_schedule_keyword = True

        if has_schedule_keyword and not has_rag_signal:
            # Sub-classify: booking vs. listing
            booking_indicators = [
                "i schedule", "i want to book", "let's book", "book the",
                "confirm", "i'd like to schedule", "i would like to schedule",
                "let's go with", "go with", "that works", "sounds good",
                "i'll take", "are fine", "is fine", "works for me",
                "please book", "book it", "lock in", "reserve",
            ]
            has_date_pattern = bool(re.search(
                r'(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)'
                r'|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{1,2}'
                r'|\d{1,2}[:/]\d{2}\s*(?:am|pm)'
                r'|\d{4}-\d{2}-\d{2}',
                msg_lower
            ))
            is_booking = any(ind in msg_lower for ind in booking_indicators) and has_date_pattern

            if is_booking:
                logger.info("Detected schedule_book intent (user wants to book a specific slot).")
                return {"intent": "schedule_book"}
            else:
                logger.info("Detected schedule_list intent (user is asking about availability).")
                return {"intent": "schedule_list"}

        # ── 4. Default: RAG ──────────────────────────────────────────────────
        logger.info("Detected RAG intent.")
        return {"intent": "rag"}

    async def retrieve_context(self, state: AgentState) -> Dict[str, Any]:
        """Node for query embedding generation and Qdrant semantic search."""
        if state.get("intent") in ["schedule_list", "schedule_book", "greeting"]:
            # Skip vector search for scheduling and greeting intents
            return {"retrieved_context": [], "sources": [], "confidence_score": "high"}

        logger.info(f"Retrieving context for query: '{state['message']}'")
        raw_chunks = await self.retriever_service.retrieve_context(state["message"])

        context_str, sources = self.rag_service.build_context(raw_chunks)
        confidence = self.rag_service.calculate_confidence(raw_chunks)

        return {
            "retrieved_context": [{"content": context_str}],
            "sources": sources,
            "confidence_score": confidence
        }

    # ── Private helpers for scheduling ───────────────────────────────────────

    async def _get_profile_and_slots(self):
        """Fetches the current profile and available slots. Returns (profile, slots) or (None, [])."""
        if not self.profile_repo or not self.scheduling_service:
            return None, []
        try:
            profile = await self.profile_repo.get_current()
            if not profile:
                return None, []
            slots = await self.scheduling_service.get_available_slots(profile.id)
            return profile, slots or []
        except Exception:
            logger.exception("Failed to retrieve profile or availability slots.")
            return None, []

    def _format_slots(self, slots) -> str:
        """Formats a list of Availability entities into a human-readable numbered list."""
        if not slots:
            return "No available interview slots at this time. Please check back later."
        lines = []
        for idx, s in enumerate(slots):
            time_str = s.slot.strftime("%A, %B %d, %Y at %I:%M %p")
            lines.append(f"{idx + 1}. {time_str}")
        return "\n".join(lines)

    def _format_slots_voice(self, slots) -> str:
        """Formats a list of Availability entities into a conversational list for voice synthesis."""
        if not slots:
            return "no available interview slots at this time."
        time_strs = []
        for s in slots:
            day = s.slot.strftime("%A, %B %d")
            time_part = s.slot.strftime("at %I:%M %p")
            time_strs.append(f"{day} {time_part}")
        if len(time_strs) == 1:
            return f"on {time_strs[0]}"
        elif len(time_strs) == 2:
            return f"on {time_strs[0]} or {time_strs[1]}"
        else:
            return "on " + ", ".join(time_strs[:-1]) + ", or " + time_strs[-1]

    async def _extract_requested_datetime(self, user_message: str, available_slots_str: str) -> Optional[str]:
        """Uses the LLM to extract the exact ISO datetime the user wants to book."""
        extraction_prompt = SLOT_EXTRACTION_PROMPT.format(
            user_message=user_message,
            available_slots=available_slots_str
        )
        try:
            result = await self.llm_port.generate_response(
                prompt=extraction_prompt,
                system_instruction="You are a date extraction assistant. Return ONLY the ISO 8601 datetime string matching the user's request from the available slots. Return NONE if no match.",
                temperature=0.0,
                max_output_tokens=100,
            )
            cleaned = result.strip().strip('"').strip("'")
            logger.info(f"LLM extracted datetime: '{cleaned}'")
            if cleaned.upper() == "NONE" or not cleaned:
                return None
            return cleaned
        except Exception:
            logger.exception("LLM datetime extraction failed.")
            return None

    def _fuzzy_match_slot(self, requested_iso: str, slots) -> Optional[Any]:
        """Attempts to parse the LLM-extracted ISO string and match it to an available slot."""
        try:
            # Try parsing with several common formats the LLM might return
            parsed = None
            for fmt in [
                "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M%z",
                "%Y-%m-%dT%H:%M",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M",
            ]:
                try:
                    parsed = datetime.strptime(requested_iso, fmt)
                    break
                except ValueError:
                    continue

            if parsed is None:
                logger.warning(f"Could not parse extracted datetime: {requested_iso}")
                return None

            # Match against available slots (compare date + hour + minute only)
            for slot_obj in slots:
                s_time = slot_obj.slot
                if (
                    s_time.year == parsed.year
                    and s_time.month == parsed.month
                    and s_time.day == parsed.day
                    and s_time.hour == parsed.hour
                    and s_time.minute == parsed.minute
                ):
                    return slot_obj
            return None
        except Exception:
            logger.exception("Fuzzy match against slots failed.")
            return None

    # ── Response generation ──────────────────────────────────────────────────

    async def generate_response(self, state: AgentState) -> Dict[str, Any]:
        """Node invoking Groq/Gemini LLM with context, prompts, and conversation history."""
        intent = state.get("intent")
        voice_mode = state.get("voice_mode", False)

        # ── Greeting ─────────────────────────────────────────────────────────
        if intent == "greeting":
            if voice_mode:
                resp = (
                    "Hello! I'm Shivam's AI assistant. I can tell you about his background, "
                    "projects, and skills, or help you schedule an interview. What would you like to know?"
                )
            else:
                resp = (
                    "Hello! Thanks for reaching out. I'm Shivam's AI assistant — think of me as "
                    "his digital representative. I can tell you about Shivam's technical experience, "
                    "projects he's built, the skills he brings to the table, and his professional background. "
                    "I can also help you find a convenient time to schedule an interview with him.\n\n"
                    "What would you like to know about Shivam?"
                )
            return {"response": resp}

        # ── Schedule: List Availability ──────────────────────────────────────
        if intent == "schedule_list":
            _, slots = await self._get_profile_and_slots()
            if voice_mode:
                slots_str = self._format_slots_voice(slots)
                resp = (
                    "Great to hear you want to connect! Shivam is actively exploring new opportunities. "
                    f"He has availability {slots_str}. "
                    "Which of those times works best for you?"
                )
            else:
                slots_str = self._format_slots(slots)
                resp = (
                    "Great to hear you're interested in speaking with Shivam! "
                    "He is actively exploring new opportunities and would love to connect. "
                    "Here are the interview slots he has available:\n\n"
                    f"{slots_str}\n\n"
                    "Just let me know which slot works best for you and I'll get it booked right away. "
                    "For example, you can say: \"Let's go with Friday, July 10, 2026 at 09:00 AM\"."
                )
            return {"response": resp}

        # ── Schedule: Book a Specific Slot ───────────────────────────────────
        if intent == "schedule_book":
            profile, slots = await self._get_profile_and_slots()

            if not profile:
                return {"response": "I apologize, but I'm having trouble accessing Shivam's profile at the moment. Could you please try again shortly?"}

            if not slots:
                if voice_mode:
                    resp = (
                        "Thank you for your interest! Unfortunately, all of Shivam's interview slots have been booked. "
                        "He updates his availability regularly, so please try again soon or ask me any questions about his background."
                    )
                else:
                    resp = (
                        "Thank you for your interest in scheduling an interview with Shivam! "
                        "Unfortunately, all of his current interview slots have been booked. "
                        "Shivam updates his availability regularly, so please check back soon "
                        "or feel free to ask me anything else about his background in the meantime."
                    )
                return {"response": resp}

            slots_str = self._format_slots(slots)

            # Step 1: Use LLM to extract the requested date/time from natural language
            extracted_iso = await self._extract_requested_datetime(state["message"], slots_str)

            if not extracted_iso:
                if voice_mode:
                    voice_slots = self._format_slots_voice(slots)
                    resp = (
                        "I'd love to get that interview set up, but I couldn't match that time with Shivam's slots. "
                        f"He is available {voice_slots}. Which one works best?"
                    )
                else:
                    resp = (
                        "I'd love to get that interview set up for you! However, I couldn't quite "
                        "match a specific slot from your message. Here are Shivam's available times:\n\n"
                        f"{slots_str}\n\n"
                        "Could you let me know which one works best? "
                        "For example: \"Let's go with Friday, July 10, 2026 at 09:00 AM\"."
                    )
                return {"response": resp}

            # Step 2: Match extracted datetime against available slots
            matched_slot = self._fuzzy_match_slot(extracted_iso, slots)

            if not matched_slot:
                if voice_mode:
                    voice_slots = self._format_slots_voice(slots)
                    resp = (
                        "Unfortunately, that time doesn't match any of Shivam's open slots. "
                        f"He has times available {voice_slots}. Would any of those work?"
                    )
                else:
                    resp = (
                        f"I appreciate your interest! Unfortunately, the time you mentioned "
                        f"({extracted_iso}) doesn't match any of Shivam's currently available slots. "
                        f"Here are the times he has open:\n\n"
                        f"{slots_str}\n\n"
                        "Would any of these work for you instead?"
                    )
                return {"response": resp}

            # Step 3: Execute the booking
            try:
                await self.scheduling_service.book_interview_slot(profile.id, matched_slot.slot)
                booked_str = matched_slot.slot.strftime("%A, %B %d, %Y at %I:%M %p")
                if voice_mode:
                    resp = (
                        f"Perfect! The interview is confirmed for {booked_str}. "
                        "Shivam is excited to connect with you. If you need anything else, just ask!"
                    )
                else:
                    resp = (
                        f"Excellent! The interview has been confirmed. ✅\n\n"
                        f"📅 {booked_str}\n\n"
                        "Shivam is excited to connect with you and discuss how he can contribute "
                        "to your team. If you need to reschedule or have any other questions about "
                        "his experience, just let me know — I'm happy to help!"
                    )
                return {"response": resp}
            except Exception as e:
                logger.exception("Interview booking execution failed.")
                if voice_mode:
                    resp = (
                        f"I apologize, but I ran into an issue while booking that slot. "
                        "Could you please try again, or pick a different time?"
                    )
                else:
                    resp = (
                        f"I apologize, but I ran into an issue while booking that slot: {str(e)}. "
                        "Could you please try again, or would you like to pick a different time?"
                    )
                return {"response": resp}

        # ── RAG (Default) ────────────────────────────────────────────────────
        chat_history_str = ""
        for msg in state["chat_history"]:
            chat_history_str += f"{msg['role'].capitalize()}: {msg['content']}\n"

        context_str = state["retrieved_context"][0]["content"] if state["retrieved_context"] else ""

        # Format prompts
        prompt = RAG_PROMPT_TEMPLATE.format(
            chat_history=chat_history_str if chat_history_str else "No prior history.",
            context=context_str if context_str else "No context available.",
            question=state["message"]
        )

        system_instruction = SYSTEM_INSTRUCTION
        if voice_mode:
            voice_directive = (
                "\n\nVOICE INTERACTION DIRECTIVE:\n"
                "- The user is talking to you over a voice interface. Your response will be synthesized directly to speech.\n"
                "- Do NOT use ANY Markdown formatting, bolding, italics, asterisks, bullet points, headers, or lists.\n"
                "- Keep your response extremely concise, natural, and conversational (ideally 1 to 3 short sentences, max 50 words).\n"
                "- Avoid abbreviations or technical jargon that sounds robotic when read aloud.\n"
                "- Structure your answer into clear, simple sentences so they can be spoken naturally."
            )
            system_instruction += voice_directive

        # Call Groq/Gemini
        response_text = await self.llm_port.generate_response(
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=0.0
        )

        return {"response": response_text}

    async def save_messages(self, state: AgentState) -> Dict[str, Any]:
        """Node logging user query and generated assistant response in MongoDB in a single parallel operation."""
        session_uuid = uuid.UUID(state["session_id"])
        user_content = state["message"]
        assistant_content = state.get("response") or ""

        await self.memory_service.save_interaction(session_uuid, user_content, assistant_content)
        return {}
