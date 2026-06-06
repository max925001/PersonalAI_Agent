'use client';

import React, { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, PhoneOff, Radio, RefreshCw, Sparkles, Volume2, AlertCircle } from 'lucide-react';
import { useVoiceSocket, VoiceState } from '@/hooks/useVoiceSocket';

export default function VoicePage() {
  const { state, transcripts, latency, error, startTalking, endConversation } = useVoiceSocket();
  const logsEndRef = useRef<HTMLDivElement>(null);

  // Auto scroll transcript log
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [transcripts]);

  // Color mappings for state badge
  const stateConfig: Record<VoiceState, { label: string; color: string; ringColor: string }> = {
    IDLE: { label: 'Idle', color: 'bg-white/10 text-muted-foreground border-white/15', ringColor: 'border-white/5' },
    CONNECTING: { label: 'Connecting...', color: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20', ringColor: 'border-yellow-500/10 animate-ping' },
    LISTENING: { label: 'Listening', color: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20', ringColor: 'border-emerald-500/20' },
    THINKING: { label: 'Thinking...', color: 'bg-purple-500/10 text-purple-400 border-purple-500/20', ringColor: 'border-purple-500/15 animate-pulse' },
    SPEAKING: { label: 'Speaking', color: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20', ringColor: 'border-indigo-500/25' },
    DISCONNECTED: { label: 'Ended', color: 'bg-red-500/10 text-red-400 border-red-500/20', ringColor: 'border-red-500/5' },
  };

  const currentStatus = stateConfig[state] || stateConfig.IDLE;

  return (
    <div className="flex-1 flex flex-col md:flex-row gap-8 py-6 max-h-[85vh] min-h-[70vh]">
      {/* 1. Left Column: Avatar & Waveform Animation */}
      <div className="flex-1 flex flex-col items-center justify-center glass-panel rounded-3xl p-8 border border-white/[0.05] min-h-[40vh]">
        
        {/* Status Badge */}
        <div className="mb-8 flex items-center space-x-2">
          <span className={`inline-flex items-center rounded-full border px-3 py-1 text-xs font-semibold tracking-wide ${currentStatus.color}`}>
            <span className="relative mr-1.5 flex h-2 w-2">
              <span className={`absolute inline-flex h-full w-full rounded-full opacity-75 ${state === 'CONNECTING' || state === 'THINKING' ? 'animate-ping bg-current' : 'bg-current'}`} />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-current" />
            </span>
            {currentStatus.label}
          </span>
          {latency > 0 && (
            <span className="text-[10px] text-muted-foreground border border-white/[0.05] bg-white/[0.02] rounded-full px-2 py-0.5">
              {latency}ms latency
            </span>
          )}
        </div>

        {/* Central Agent Avatar */}
        <div className="relative mb-10">
          {/* Animated Glow Rings around Avatar */}
          <AnimatePresence>
            {(state === 'LISTENING' || state === 'SPEAKING' || state === 'THINKING') && (
              <motion.div
                className={`absolute inset-0 rounded-full border-2 ${
                  state === 'SPEAKING' ? 'border-purple-500/30' :
                  state === 'LISTENING' ? 'border-emerald-500/30' :
                  'border-indigo-500/30'
                }`}
                initial={{ scale: 1, opacity: 0.8 }}
                animate={{
                  scale: [1, 1.3, 1],
                  opacity: [0.8, 0, 0.8]
                }}
                exit={{ opacity: 0 }}
                transition={{
                  duration: state === 'SPEAKING' ? 1.5 : 2.5,
                  repeat: Infinity,
                  ease: 'easeInOut'
                }}
              />
            )}
          </AnimatePresence>

          {/* Core Avatar Sphere */}
          <div className={`h-40 w-40 rounded-full border flex items-center justify-center transition-all duration-500 ${
            state === 'SPEAKING' ? 'border-purple-500/30 bg-gradient-to-br from-purple-900/20 to-indigo-900/20 shadow-lg shadow-purple-500/10' :
            state === 'LISTENING' ? 'border-emerald-500/30 bg-gradient-to-br from-emerald-900/20 to-teal-900/20 shadow-lg shadow-emerald-500/10' :
            state === 'THINKING' ? 'border-indigo-500/30 bg-gradient-to-br from-indigo-900/20 to-slate-900/20' :
            'border-white/10 bg-white/[0.02]'
          }`}>
            {state === 'SPEAKING' ? (
              <Volume2 className="h-16 w-16 text-purple-400 animate-pulse" />
            ) : state === 'LISTENING' ? (
              <Mic className="h-16 w-16 text-emerald-400 animate-bounce" />
            ) : state === 'THINKING' ? (
              <RefreshCw className="h-16 w-16 text-indigo-400 animate-spin" style={{ animationDuration: '2.5s' }} />
            ) : (
              <Radio className="h-16 w-16 text-muted-foreground opacity-40" />
            )}
          </div>
        </div>

        {/* Audio Waveforms Animation */}
        <div className="h-12 flex items-center gap-1.5 justify-center mb-8 w-full">
          {state === 'SPEAKING' && (
            // Tall purple speaking bars
            [...Array(9)].map((_, i) => (
              <motion.div
                key={i}
                className="w-1.5 rounded-full bg-purple-500"
                animate={{ height: [12, Math.random() * 45 + 15, 12] }}
                transition={{ duration: 0.35 + i * 0.05, repeat: Infinity, ease: 'easeInOut' }}
              />
            ))
          )}

          {state === 'LISTENING' && (
            // Gentle green listening waves
            [...Array(9)].map((_, i) => (
              <motion.div
                key={i}
                className="w-1.5 rounded-full bg-emerald-500"
                animate={{ height: [8, Math.random() * 20 + 8, 8] }}
                transition={{ duration: 0.5 + i * 0.07, repeat: Infinity, ease: 'easeInOut' }}
              />
            ))
          )}

          {state === 'THINKING' && (
            // Scanning loading dots
            <div className="flex items-center space-x-1.5">
              <div className="h-3.5 w-3.5 rounded-full bg-indigo-500 animate-bounce" style={{ animationDelay: '0ms' }} />
              <div className="h-3.5 w-3.5 rounded-full bg-indigo-500 animate-bounce" style={{ animationDelay: '150ms' }} />
              <div className="h-3.5 w-3.5 rounded-full bg-indigo-500 animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          )}

          {state === 'IDLE' && (
            // Flat grey line
            <div className="h-1 w-24 bg-white/10 rounded-full" />
          )}

          {state === 'DISCONNECTED' && (
            <span className="text-xs text-muted-foreground">Session Ended</span>
          )}
        </div>

        {/* Action Controls */}
        <div className="w-full max-w-sm">
          {state === 'IDLE' || state === 'DISCONNECTED' ? (
            <button
              onClick={startTalking}
              className="w-full flex items-center justify-center space-x-2 rounded-2xl bg-purple-600 py-4 text-sm font-semibold text-white shadow-lg hover:bg-purple-500 hover:shadow-purple-500/20 active:scale-[0.98] transition-all duration-200"
            >
              <Mic className="h-5 w-5" />
              <span>START TALKING</span>
            </button>
          ) : (
            <button
              onClick={endConversation}
              className="w-full flex items-center justify-center space-x-2 rounded-2xl border border-red-500/30 bg-red-500/10 py-4 text-sm font-semibold text-red-400 hover:bg-red-500/20 active:scale-[0.98] transition-all duration-200"
            >
              <PhoneOff className="h-5 w-5" />
              <span>END CONVERSATION</span>
            </button>
          )}
        </div>
      </div>

      {/* 2. Right Column: Live Transcript Area */}
      <div className="w-full md:w-96 flex flex-col glass-panel rounded-3xl overflow-hidden border border-white/[0.05] max-h-[50vh] md:max-h-full">
        {/* Header */}
        <div className="border-b border-white/[0.05] px-6 py-4 bg-white/[0.01]">
          <span className="block text-xs uppercase font-semibold text-purple-400">Audio logs</span>
          <h2 className="text-base font-bold tracking-tight">Live Transcript</h2>
        </div>

        {/* Scrollable logs */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4 no-scrollbar min-h-[30vh]">
          {error && (
            <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-4 flex items-start space-x-3 text-red-400 text-xs">
              <AlertCircle className="h-5 w-5 flex-shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {transcripts.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center space-y-2 py-10 opacity-40">
              <Sparkles className="h-8 w-8 text-muted-foreground mb-2" />
              <p className="text-xs font-semibold">Ready to record</p>
              <p className="text-[10px] text-muted-foreground">Click Start Talking to connect.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {transcripts.map((log, index) => (
                <div
                  key={index}
                  className={`flex flex-col ${log.sender === 'recruiter' ? 'items-end' : 'items-start'}`}
                >
                  <span className="text-[9px] uppercase tracking-wide text-muted-foreground mb-1 block">
                    {log.sender === 'recruiter' ? 'You' : 'Shivam'}
                  </span>
                  <div className={`max-w-[90%] rounded-xl p-3 text-xs leading-relaxed ${
                    log.sender === 'recruiter'
                      ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-tr-none'
                      : 'bg-white/[0.03] border border-white/[0.05] text-foreground rounded-tl-none'
                  }`}>
                    {log.text}
                  </div>
                </div>
              ))}
              <div ref={logsEndRef} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
