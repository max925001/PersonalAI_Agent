'use client';

import React, { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  MessageSquare,
  Send,
  Trash2,
  Sparkles,
  ExternalLink,
  RefreshCw,
  AlertCircle,
  FileText,
  Github
} from 'lucide-react';
import { useChatStore, ChatMessage } from '@/stores/useChatStore';
import { chatService } from '@/services/chatService';

export default function ChatPage() {
  const {
    messages,
    sessionId,
    isLoading,
    error,
    addMessage,
    updateMessageContent,
    loadSession,
    clearChat,
    setLoading,
    setError,
  } = useChatStore();

  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [retryPayload, setRetryPayload] = useState<string | null>(null);

  // Initialize session
  useEffect(() => {
    loadSession();
  }, [loadSession]);

  // Auto scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSend = async (messageText: string) => {
    if (!messageText.trim() || isLoading) return;

    setInput('');
    setRetryPayload(null);
    setError(null);

    // 1. Add User Message
    addMessage({
      role: 'user',
      content: messageText,
    });

    await executeChatQuery(messageText);
  };

  const executeChatQuery = async (queryText: string) => {
    setLoading(true);

    // Create a streaming message placeholder in UI
    const assistantMessageId = crypto.randomUUID();
    const tempMessage: ChatMessage = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      isStreaming: true,
    };
    
    useChatStore.setState((state) => ({
      messages: [...state.messages, tempMessage],
    }));

    try {
      const response = await chatService.sendMessage({
        message: queryText,
        session_id: sessionId,
      });

      // Update the message with real reply, citations and confidence
      useChatStore.setState((state) => ({
        messages: state.messages.map((m) =>
          m.id === assistantMessageId
            ? {
                ...m,
                content: response.answer,
                sources: response.sources,
                confidence: response.confidence,
                isStreaming: false,
              }
            : m
        ),
      }));
    } catch (err: any) {
      // Remove the empty streaming message and show error retry option
      useChatStore.setState((state) => ({
        messages: state.messages.filter((m) => m.id !== assistantMessageId),
      }));
      setError('Connection timeout or backend failure. Would you like to retry?');
      setRetryPayload(queryText);
    } finally {
      setLoading(false);
    }
  };

  const handleRetry = () => {
    if (retryPayload) {
      executeChatQuery(retryPayload);
      setRetryPayload(null);
      setError(null);
    }
  };

  return (
    <div className="flex-1 flex flex-col md:flex-row gap-6 max-h-[85vh] min-h-[75vh]">
      {/* Sidebar Panel */}
      <div className="w-full md:w-64 flex flex-col glass-panel rounded-3xl p-6 justify-between border border-white/[0.05]">
        <div className="space-y-6">
          <div className="space-y-2">
            <span className="block text-xs uppercase font-semibold text-purple-400">Context Panel</span>
            <h2 className="text-xl font-bold tracking-tight">AI Twin Chat</h2>
          </div>
          <p className="text-xs text-muted-foreground leading-relaxed">
            Shivam's twin queries a vector index populated from his personal CV, live GitHub syncs, and supplementary info.
          </p>
          <div className="rounded-2xl border border-white/[0.05] bg-white/[0.01] p-4 text-xs space-y-2 text-muted-foreground">
            <span className="block font-semibold text-foreground">Sample Questions:</span>
            <button
              onClick={() => handleSend("What are Shivam's technical strengths?")}
              className="block hover:text-purple-400 text-left transition-colors"
            >
              • Tell me about his tech stack
            </button>
            <button
              onClick={() => handleSend("What projects did he build?")}
              className="block hover:text-purple-400 text-left transition-colors"
            >
              • Describe his projects
            </button>
            <button
              onClick={() => handleSend("Tell me about his past experiences")}
              className="block hover:text-purple-400 text-left transition-colors"
            >
              • Tell me about his experience
            </button>
          </div>
        </div>

        {/* Clear Chat */}
        <button
          onClick={clearChat}
          disabled={messages.length === 0}
          className="w-full flex items-center justify-center space-x-2 rounded-xl border border-red-500/30 bg-red-500/5 py-2.5 text-xs font-semibold text-red-400 hover:bg-red-500/15 disabled:opacity-40 disabled:hover:bg-transparent transition-all"
        >
          <Trash2 className="h-4 w-4" />
          <span>Clear Conversation</span>
        </button>
      </div>

      {/* Main Chat Panel */}
      <div className="flex-1 flex flex-col glass-panel rounded-3xl overflow-hidden border border-white/[0.05]">
        {/* Header */}
        <div className="border-b border-white/[0.05] px-6 py-4 flex items-center justify-between bg-white/[0.01]">
          <div className="flex items-center space-x-3">
            <div className="relative">
              <div className="h-3 w-3 rounded-full bg-purple-500 animate-ping absolute" />
              <div className="h-3 w-3 rounded-full bg-purple-500" />
            </div>
            <div>
              <span className="block text-sm font-bold">Shivam's Twin</span>
              <span className="block text-xs text-muted-foreground">Active RAG Session</span>
            </div>
          </div>
        </div>

        {/* Messages List Area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 no-scrollbar min-h-[45vh]">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center space-y-4 py-20">
              <div className="h-12 w-12 rounded-2xl bg-purple-500/10 flex items-center justify-center text-purple-400">
                <MessageSquare className="h-6 w-6 animate-pulse" />
              </div>
              <div className="space-y-1">
                <p className="text-sm font-semibold">Start a conversation</p>
                <p className="text-xs text-muted-foreground max-w-xs">
                  Ask me anything about Shivam's professional background, skills, or projects.
                </p>
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
                >
                  <div
                    className={`max-w-[85%] rounded-2xl p-4 text-sm leading-relaxed ${
                      msg.role === 'user'
                        ? 'bg-purple-600 text-white rounded-br-none'
                        : 'bg-white/[0.03] border border-white/[0.06] rounded-bl-none text-foreground'
                    }`}
                  >
                    {msg.isStreaming ? (
                      <div className="flex items-center space-x-1.5 py-1">
                        <div className="h-2 w-2 rounded-full bg-purple-400 animate-bounce" style={{ animationDelay: '0ms' }} />
                        <div className="h-2 w-2 rounded-full bg-purple-400 animate-bounce" style={{ animationDelay: '150ms' }} />
                        <div className="h-2 w-2 rounded-full bg-purple-400 animate-bounce" style={{ animationDelay: '300ms' }} />
                      </div>
                    ) : (
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                    )}
                  </div>

                  {/* Message Meta Info (Confidence & Citations) */}
                  {msg.role === 'assistant' && !msg.isStreaming && (
                    <div className="mt-2 flex flex-wrap gap-2 text-[10px] text-muted-foreground items-center">
                      <span className="text-muted-foreground">{msg.timestamp}</span>
                      
                      {msg.confidence && (
                        <span className={`px-2 py-0.5 rounded-full font-semibold border ${
                          msg.confidence === 'high' ? 'border-emerald-500/20 bg-emerald-500/5 text-emerald-400' :
                          msg.confidence === 'medium' ? 'border-yellow-500/20 bg-yellow-500/5 text-yellow-400' :
                          'border-red-500/20 bg-red-500/5 text-red-400'
                        }`}>
                          {msg.confidence.toUpperCase()} CONFIDENCE
                        </span>
                      )}

                      {/* Source Citations */}
                      {msg.sources && msg.sources.length > 0 && (
                        <div className="flex items-center space-x-1.5 border border-white/[0.05] bg-white/[0.02] rounded-full px-2 py-0.5">
                          <span>Sources:</span>
                          {msg.sources.map((src, i) => (
                            <span key={i} className="inline-flex items-center space-x-0.5 text-purple-400">
                              {src.source_type === 'resume' ? <FileText className="h-3 w-3" /> : <Github className="h-3 w-3" />}
                              <span>{src.source_type === 'repository' && src.repository_name ? src.repository_name : src.source_type}</span>
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {msg.role === 'user' && (
                    <span className="mt-1 block text-[10px] text-muted-foreground">{msg.timestamp}</span>
                  )}
                </div>
              ))}
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Connection Failure Error & Retry */}
        <AnimatePresence>
          {error && (
            <motion.div
              className="mx-6 mb-4 p-4 border border-red-500/20 bg-red-500/5 rounded-2xl flex items-center justify-between"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 10 }}
            >
              <div className="flex items-center space-x-3 text-red-400 text-xs">
                <AlertCircle className="h-5 w-5 flex-shrink-0" />
                <span>{error}</span>
              </div>
              <button
                onClick={handleRetry}
                className="flex items-center space-x-1 border border-red-500/30 rounded-lg px-3 py-1 text-[11px] font-semibold text-red-400 hover:bg-red-500/10 transition"
              >
                <RefreshCw className="h-3.5 w-3.5" />
                <span>Retry</span>
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Input Area */}
        <div className="border-t border-white/[0.05] p-4 bg-white/[0.01]">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend(input);
            }}
            className="flex items-center space-x-3"
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={isLoading}
              placeholder="Ask a question about Shivam..."
              className="flex-1 bg-white/[0.02] border border-white/[0.08] rounded-xl px-4 py-3 text-sm text-foreground placeholder-muted-foreground focus:outline-none focus:border-purple-500 focus:bg-white/[0.04] disabled:opacity-55 transition-all"
            />
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="h-11 w-11 rounded-xl bg-purple-600 flex items-center justify-center text-white hover:bg-purple-500 disabled:opacity-40 disabled:hover:bg-purple-600 transition-all duration-200"
            >
              <Send className="h-4 w-4" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
