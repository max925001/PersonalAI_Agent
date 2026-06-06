import { create } from 'zustand';
import { Citation } from '../services/chatService';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: Citation[];
  confidence?: string;
  timestamp: string;
  isStreaming?: boolean;
}

interface ChatState {
  messages: ChatMessage[];
  sessionId: string;
  isLoading: boolean;
  error: string | null;
  addMessage: (message: Omit<ChatMessage, 'id' | 'timestamp'>) => void;
  updateMessageContent: (id: string, content: string) => void;
  setSessionId: (id: string) => void;
  setLoading: (loading: boolean) => void;
  setError: (err: string | null) => void;
  clearChat: () => void;
  loadSession: () => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  sessionId: '',
  isLoading: false,
  error: null,

  addMessage: (message) => {
    const newMessage: ChatMessage = {
      ...message,
      id: crypto.randomUUID(),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
    set((state) => ({
      messages: [...state.messages, newMessage],
      error: null,
    }));
  },

  updateMessageContent: (id, content) => {
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === id ? { ...msg, content } : msg
      ),
    }));
  },

  setSessionId: (id) => {
    if (typeof window !== 'undefined') {
      sessionStorage.setItem('chat_session_id', id);
    }
    set({ sessionId: id });
  },

  setLoading: (loading) => set({ isLoading: loading }),
  setError: (err) => set({ error: err }),

  clearChat: () => {
    set({ messages: [], error: null });
  },

  loadSession: () => {
    if (typeof window !== 'undefined') {
      let id = sessionStorage.getItem('chat_session_id');
      if (!id) {
        id = crypto.randomUUID();
        sessionStorage.setItem('chat_session_id', id);
      }
      set({ sessionId: id });
    }
  },
}));
