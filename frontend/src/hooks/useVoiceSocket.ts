'use client';

import { useState, useRef, useEffect, useCallback } from 'react';

export type VoiceState = 'IDLE' | 'CONNECTING' | 'LISTENING' | 'THINKING' | 'SPEAKING' | 'DISCONNECTED';

export interface TranscriptLog {
  sender: 'recruiter' | 'agent';
  text: string;
}

export function useVoiceSocket() {
  const [transcripts, setTranscripts] = useState<TranscriptLog[]>([]);
  const [latency, setLatency] = useState<number>(0);
  const [errorState, setErrorState] = useState<string | null>(null);

  const socketRef = useRef<WebSocket | null>(null);
  
  // Audio Input (Recording) refs
  const audioContextInputRef = useRef<AudioContext | null>(null);
  const micStreamRef = useRef<MediaStream | null>(null);
  const processorNodeRef = useRef<ScriptProcessorNode | null>(null);
  const sourceNodeRef = useRef<MediaStreamAudioSourceNode | null>(null);
  
  // Audio Output (Playback) refs
  const audioContextOutputRef = useRef<AudioContext | null>(null);
  const nextPlayTimeRef = useRef<number>(0);
  const playbackBuffersQueueRef = useRef<AudioBuffer[]>([]);
  const isPlayingAudioRef = useRef<boolean>(false);
  const checkSpeakingIntervalRef = useRef<any>(null);

  // Synchronous VAD and state tracking refs
  const stateRef = useRef<VoiceState>('IDLE');
  const isSpeakingRef = useRef<boolean>(false);
  const silenceStartRef = useRef<number | null>(null);
  const lastRmsLogTimeRef = useRef<number>(0);
  const rmsHistoryRef = useRef<number[]>([]);

  // React state hook
  const [state, _setState] = useState<VoiceState>('IDLE');

  // Unified state setter to keep ref and React state in sync
  const setState = useCallback((newState: VoiceState) => {
    stateRef.current = newState;
    if (newState === 'LISTENING') {
      isSpeakingRef.current = false;
      silenceStartRef.current = null;
    }
    _setState(newState);
  }, []);

  // Helper to append log
  const appendLog = useCallback((sender: 'recruiter' | 'agent', text: string) => {
    setTranscripts((prev) => [...prev, { sender, text }]);
  }, []);

  // Playback scheduler loop
  const schedulePlayback = useCallback(() => {
    const ctx = audioContextOutputRef.current;
    if (!ctx) return;

    if (ctx.state === 'suspended') {
      ctx.resume().then(() => {
        schedulePlayback();
      }).catch(e => console.error("Failed to resume audio context:", e));
      return;
    }

    while (playbackBuffersQueueRef.current.length > 0) {
      const audioBuffer = playbackBuffersQueueRef.current.shift();
      if (!audioBuffer) continue;

      const source = ctx.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(ctx.destination);

      // Transition to SPEAKING state when audio playback starts
      isPlayingAudioRef.current = true;
      setState('SPEAKING');

      // Schedule play time
      const startTime = Math.max(ctx.currentTime, nextPlayTimeRef.current);
      source.start(startTime);
      
      // Update next scheduled time based on buffer duration
      const endTime = startTime + audioBuffer.duration;
      nextPlayTimeRef.current = endTime;

      source.onended = () => {
        // If nextPlayTimeRef.current hasn't been updated further, this was the last buffer in the queue
        if (nextPlayTimeRef.current <= endTime) {
          isPlayingAudioRef.current = false;
          setState('LISTENING');
        }
      };
    }
  }, [setState]);

  // Process incoming base64 encoded audio (e.g. MP3) from FastAPI
  const handleIncomingAudio = useCallback((base64Audio: string) => {
    try {
      const binaryString = window.atob(base64Audio);
      const len = binaryString.length;
      const bytes = new Uint8Array(len);
      for (let i = 0; i < len; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }

      // Initialize audio context for output if needed
      if (!audioContextOutputRef.current) {
        const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
        audioContextOutputRef.current = new AudioContextClass();
        nextPlayTimeRef.current = audioContextOutputRef.current.currentTime;
      }

      const ctx = audioContextOutputRef.current;
      
      // Decode compressed audio format (MP3) natively in the browser
      ctx.decodeAudioData(bytes.buffer.slice(0), (audioBuffer) => {
        playbackBuffersQueueRef.current.push(audioBuffer);
        schedulePlayback();
      }, (err) => {
        console.error("decodeAudioData error:", err);
      });
    } catch (e) {
      console.error("Failed to parse or play incoming speech audio:", e);
    }
  }, [schedulePlayback]);

  // Web Speech API fallback for when cloud TTS (ElevenLabs) fails or is rate-limited
  const speakTextFallback = useCallback((text: string) => {
    if (!('speechSynthesis' in window)) {
      console.warn("Web Speech API not supported in this browser.");
      setState('LISTENING');
      return;
    }
    
    // Stop any active speech before starting new utterance
    window.speechSynthesis.cancel();
    
    // Clean text: remove emoji codes or remaining formatting
    const cleanedText = text.replace(/[\uE000-\uF8FF]|\uD83C[\uDC00-\uDFFF]|\uD83D[\uDC00-\uDFFF]|[\u2011-\u26FF]|\uD83E[\uDD10-\uDDFF]/g, "");
    
    const utterance = new SpeechSynthesisUtterance(cleanedText);
    
    // Configure voice properties
    const voices = window.speechSynthesis.getVoices();
    
    // Prioritize high-quality Indian English voices
    let selectedVoice = voices.find(v => v.lang === 'en-IN');
    if (!selectedVoice) {
      selectedVoice = voices.find(v => v.lang.startsWith('en'));
    }
    
    if (selectedVoice) {
      utterance.voice = selectedVoice;
      console.log("SpeechSynthesis using voice:", selectedVoice.name, "| lang:", selectedVoice.lang);
    }
    
    utterance.onstart = () => {
      setState('SPEAKING');
    };
    
    utterance.onend = () => {
      setState('LISTENING');
    };
    
    utterance.onerror = (e) => {
      console.error("SpeechSynthesis error:", e);
      setState('LISTENING');
    };
    
    window.speechSynthesis.speak(utterance);
  }, [setState]);

  // Downsample mic input buffer to 16kHz and convert to 16-bit Int16 PCM
  const downsampleAndSend = useCallback((buffer: Float32Array, inputSampleRate: number) => {
    const targetSampleRate = 16000;
    const ratio = inputSampleRate / targetSampleRate;
    const newLength = Math.round(buffer.length / ratio);
    const result = new Float32Array(newLength);
    
    // Simple interpolation downsampler
    for (let i = 0; i < newLength; i++) {
      result[i] = buffer[Math.round(i * ratio)];
    }

    // Convert float32 array to 16-bit signed PCM bytes
    const pcmBytes = new Int16Array(result.length);
    for (let i = 0; i < result.length; i++) {
      const s = Math.max(-1, Math.min(1, result[i]));
      pcmBytes[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
    }

    // Base64 encode PCM bytes
    const uint8Bytes = new Uint8Array(pcmBytes.buffer);
    let binary = '';
    for (let i = 0; i < uint8Bytes.byteLength; i++) {
      binary += String.fromCharCode(uint8Bytes[i]);
    }
    const base64Audio = window.btoa(binary);

    // Send chunk via WebSocket
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({
        event: 'audio_chunk',
        audio: base64Audio
      }));
    }
  }, []);

  // Cleanup helper
  const stopAudio = useCallback(() => {
    // 1. Close WebSocket
    if (socketRef.current) {
      if (socketRef.current.readyState === WebSocket.OPEN) {
        try {
          socketRef.current.send(JSON.stringify({ event: 'end_session' }));
        } catch (_) {}
      }
      socketRef.current.close();
      socketRef.current = null;
    }

    // 2. Stop recording processor nodes
    if (processorNodeRef.current) {
      processorNodeRef.current.disconnect();
      processorNodeRef.current = null;
    }
    if (sourceNodeRef.current) {
      sourceNodeRef.current.disconnect();
      sourceNodeRef.current = null;
    }
    if (micStreamRef.current) {
      micStreamRef.current.getTracks().forEach((track) => track.stop());
      micStreamRef.current = null;
    }
    if (audioContextInputRef.current) {
      audioContextInputRef.current.close();
      audioContextInputRef.current = null;
    }

    // 3. Clear Playback Context
    if (audioContextOutputRef.current) {
      audioContextOutputRef.current.close();
      audioContextOutputRef.current = null;
    }
    playbackBuffersQueueRef.current = [];
    isPlayingAudioRef.current = false;
    nextPlayTimeRef.current = 0;

    // 4. Clear VAD status
    isSpeakingRef.current = false;
    silenceStartRef.current = null;

    // 5. Clear intervals
    if (checkSpeakingIntervalRef.current) {
      clearInterval(checkSpeakingIntervalRef.current);
      checkSpeakingIntervalRef.current = null;
    }
  }, []);

  const endConversation = useCallback(() => {
    stopAudio();
    setState('DISCONNECTED');
    appendLog('agent', 'Conversation ended.');
  }, [stopAudio, appendLog, setState]);

  const startTalking = useCallback(async () => {
    // Step 0: Synchronously initialize AudioContext output on the user click gesture before any async boundary
    if (!audioContextOutputRef.current) {
      const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
      audioContextOutputRef.current = new AudioContextClass();
      nextPlayTimeRef.current = audioContextOutputRef.current.currentTime;
      console.log("Initialized output AudioContext on click. State:", audioContextOutputRef.current.state, "Sample Rate:", audioContextOutputRef.current.sampleRate);
    } else if (audioContextOutputRef.current.state === 'suspended') {
      audioContextOutputRef.current.resume();
      console.log("Resumed output AudioContext. State:", audioContextOutputRef.current.state);
    }

    setState('CONNECTING');
    setTranscripts([]);
    setLatency(0);
    setErrorState(null);

    try {
      // Step 1: Request Mic Permissions
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });
      micStreamRef.current = stream;

      // Step 2: Open WebSocket
      const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/api/v1/voice/stream';
      const socket = new WebSocket(wsUrl);
      socketRef.current = socket;

      socket.onopen = () => {
        console.log("WebSocket voice connection established.");
        setState('LISTENING');
        
        // Trigger start session and initial agent greeting
        socket.send(JSON.stringify({ event: 'start_talking' }));

        // Step 3: Initialize Input Audio Recording (downsampling PCM)
        const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
        const inputCtx = new AudioContextClass();
        audioContextInputRef.current = inputCtx;

        sourceNodeRef.current = inputCtx.createMediaStreamSource(stream);
        
        // 2048 buffer size script processor node
        processorNodeRef.current = inputCtx.createScriptProcessor(2048, 1, 1);
        
        processorNodeRef.current.onaudioprocess = (e) => {
          if (stateRef.current !== 'LISTENING') return;

          const inputBuffer = e.inputBuffer.getChannelData(0);
          
          // Stream chunk
          downsampleAndSend(inputBuffer, inputCtx.sampleRate);

          // VAD Silence Detection
          let sum = 0;
          for (let i = 0; i < inputBuffer.length; i++) {
            sum += inputBuffer[i] * inputBuffer[i];
          }
          const rms = Math.sqrt(sum / inputBuffer.length);
          
          // Smooth RMS values using a 5-buffer moving average to filter out short transient noise spikes
          rmsHistoryRef.current.push(rms);
          if (rmsHistoryRef.current.length > 5) {
            rmsHistoryRef.current.shift();
          }
          const avgRms = rmsHistoryRef.current.reduce((a, b) => a + b, 0) / rmsHistoryRef.current.length;
          
          const rmsThreshold = 0.015; // Set to 0.015 to ignore low-level ambient noise floor
          const silenceDuration = 3000; // 3.0s

          // Periodically log VAD metrics every 2 seconds for debugging
          if (Date.now() - lastRmsLogTimeRef.current > 2000) {
            console.log("VAD Mic Volume - Current RMS:", rms.toFixed(5), "| Smoothed Avg RMS:", avgRms.toFixed(5), "| Threshold:", rmsThreshold);
            lastRmsLogTimeRef.current = Date.now();
          }
          
          if (avgRms > rmsThreshold) {
            if (!isSpeakingRef.current) {
              console.log("Speech detected! Smoothed RMS:", avgRms);
            }
            isSpeakingRef.current = true;
            silenceStartRef.current = null;
          } else if (isSpeakingRef.current) {
            if (silenceStartRef.current === null) {
              silenceStartRef.current = Date.now();
              console.log("Silence started... Smoothed RMS:", avgRms);
            } else if (Date.now() - silenceStartRef.current > silenceDuration) {
              console.log("Silence threshold met (3s). Sending speech_done. Final silence duration:", Date.now() - silenceStartRef.current);
              isSpeakingRef.current = false;
              silenceStartRef.current = null;
              rmsHistoryRef.current = []; // Clear history
              
              if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
                socketRef.current.send(JSON.stringify({ event: 'speech_done' }));
                setState('THINKING');
              }
            }
          }
        };

        sourceNodeRef.current.connect(processorNodeRef.current);
        processorNodeRef.current.connect(inputCtx.destination);
      };

      socket.onmessage = (event) => {
        const payload = JSON.parse(event.data);
        const event_type = payload.event;
        const start = Date.now();

        if (event_type === 'session_started') {
          console.log(`Voice session id: ${payload.session_id}`);
        } else if (event_type === 'agent_thinking') {
          setState('THINKING');
        } else if (event_type === 'agent_response_text') {
          appendLog('agent', payload.text);
          setLatency(Date.now() - start); // measure event loop latency roughly
          if (payload.audio_fallback) {
            speakTextFallback(payload.text);
          }
        } else if (event_type === 'audio_chunk') {
          handleIncomingAudio(payload.audio);
        } else if (event_type === 'transcript') {
          appendLog('recruiter', payload.text);
        } else if (event_type === 'silence_detected') {
          setState('LISTENING');
        } else if (event_type === 'session_ended') {
          endConversation();
        } else if (event_type === 'error') {
          console.error("Server error:", payload.message);
          setErrorState(payload.message);
          endConversation();
        }
      };

      socket.onerror = (e) => {
        console.error("WebSocket error:", e);
        setErrorState("WebSocket connection failed.");
        endConversation();
      };

      socket.onclose = () => {
        console.log("WebSocket voice connection closed.");
      };

    } catch (e: any) {
      console.error("Failed to start voice stream:", e);
      setErrorState(e.message || "Microphone permission denied or device busy.");
      setState('DISCONNECTED');
    }
  }, [downsampleAndSend, handleIncomingAudio, appendLog, endConversation, setState]);

  // Monitor silence / speaking bounds in background
  useEffect(() => {
    return () => {
      stopAudio();
    };
  }, [stopAudio]);

  return {
    state,
    transcripts,
    latency,
    error: errorState,
    startTalking,
    endConversation
  };
}
