'use client';

import React from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { MessageSquare, PhoneCall, Calendar, Sparkles, Terminal, Code2, Cpu, GitFork } from 'lucide-react';

export default function LandingPage() {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.15 },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 30 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.6, ease: 'easeOut' },
    },
  };

  const skills = [
    { name: 'RAG & AI Agents', icon: Cpu, desc: 'LangGraph orchestrations, Qdrant vectors, context extraction.' },
    { name: 'Backend Systems', icon: Terminal, desc: 'FastAPI, Beanie ODM, MongoDB, secure credentials architecture.' },
    { name: 'Frontend Engineering', icon: Code2, desc: 'Next.js App Router, Tailwind CSS, Zustand, responsive UI.' },
    { name: 'Digital Twin Sync', icon: GitFork, desc: 'GitHub webhook sync pipelines, resume parsing workers.' },
  ];

  return (
    <div className="flex flex-col items-center justify-center space-y-20 py-12 md:py-20">
      {/* 1. Hero Section */}
      <motion.section
        className="w-full text-center max-w-4xl px-4 flex flex-col items-center space-y-6"
        initial={{ opacity: 0, y: -40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: 'easeOut' }}
      >
        {/* Futuristic Badge */}
        <div className="inline-flex items-center space-x-2 rounded-full border border-purple-500/30 bg-purple-500/10 px-4 py-1.5 text-xs font-semibold tracking-wide text-purple-400">
          <Sparkles className="h-4.5 w-4.5 animate-spin" style={{ animationDuration: '3s' }} />
          <span>MEET MY DIGITAL REPRESENTATIVE</span>
        </div>

        {/* Heading */}
        <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight">
          Shivam's{' '}
          <span className="bg-gradient-to-r from-purple-400 via-pink-500 to-indigo-500 bg-clip-text text-transparent glow-text">
            AI Digital Twin
          </span>
        </h1>

        {/* Description */}
        <p className="text-lg sm:text-xl text-muted-foreground max-w-2xl leading-relaxed">
          Step into a production-grade portfolio platform. Chat with Shivam's AI twin, hold a real-time voice call, or book an interview slot directly.
        </p>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row items-center gap-4 pt-6">
          <Link
            href="/chat"
            className="w-full sm:w-auto flex items-center justify-center space-x-2 rounded-xl bg-purple-600 px-8 py-4 text-sm font-semibold text-white shadow-lg hover:bg-purple-500 hover:shadow-purple-500/20 active:scale-95 transition-all duration-200"
          >
            <MessageSquare className="h-4.5 w-4.5" />
            <span>Chat With AI</span>
          </Link>
          <Link
            href="/voice"
            className="w-full sm:w-auto flex items-center justify-center space-x-2 rounded-xl border border-white/[0.08] bg-white/[0.03] px-8 py-4 text-sm font-semibold text-muted-foreground hover:text-foreground hover:bg-white/[0.06] hover:border-white/[0.12] active:scale-95 transition-all duration-200"
          >
            <PhoneCall className="h-4.5 w-4.5" />
            <span>Talk To AI</span>
          </Link>
          <Link
            href="/schedule"
            className="w-full sm:w-auto flex items-center justify-center space-x-2 rounded-xl border border-purple-500/30 bg-purple-500/5 px-8 py-4 text-sm font-semibold text-purple-400 hover:bg-purple-500/10 active:scale-95 transition-all duration-200"
          >
            <Calendar className="h-4.5 w-4.5" />
            <span>Schedule Interview</span>
          </Link>
        </div>
      </motion.section>

      {/* 2. Interactive Highlights & Introduction */}
      <motion.section
        className="w-full max-w-6xl px-4 grid grid-cols-1 md:grid-cols-2 gap-12 items-center"
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, margin: '-100px' }}
        variants={containerVariants}
      >
        {/* Pitch Card */}
        <motion.div className="glass-panel rounded-3xl p-8 md:p-10 space-y-6" variants={itemVariants}>
          <div className="h-12 w-12 rounded-2xl bg-purple-600/10 flex items-center justify-center text-purple-400">
            <Cpu className="h-6 w-6" />
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight">The AI Representative</h2>
          <p className="text-muted-foreground leading-relaxed">
            This digital representative is built on a full production-grade Retrieval-Augmented Generation (RAG) system. It reads Shivam's sync'd GitHub commits, parsed resume content, and additional data stored in a Qdrant vector collection to give accurate, contextual, and professional replies.
          </p>
          <p className="text-muted-foreground leading-relaxed">
            No hallucinated credentials, no robotic prompt loops—just crisp facts and responsive scheduling.
          </p>
        </motion.div>

        {/* Right side Grid: Skills list */}
        <motion.div className="grid grid-cols-1 sm:grid-cols-2 gap-6" variants={containerVariants}>
          {skills.map((skill, index) => {
            const Icon = skill.icon;
            return (
              <motion.div
                key={index}
                className="border border-white/[0.05] bg-white/[0.02] rounded-2xl p-6 hover:bg-white/[0.04] transition-all duration-300"
                variants={itemVariants}
              >
                <div className="h-10 w-10 rounded-xl bg-purple-500/10 flex items-center justify-center text-purple-400 mb-4">
                  <Icon className="h-5 w-5" />
                </div>
                <h3 className="text-base font-bold mb-2">{skill.name}</h3>
                <p className="text-xs text-muted-foreground leading-relaxed">{skill.desc}</p>
              </motion.div>
            );
          })}
        </motion.div>
      </motion.section>

      {/* 3. Call To Action section */}
      <motion.section
        className="w-full max-w-5xl px-4 text-center py-12 rounded-3xl bg-gradient-to-br from-purple-900/10 via-background to-indigo-900/10 border border-purple-500/20"
        initial={{ opacity: 0, scale: 0.95 }}
        whileInView={{ opacity: 1, scale: 1 }}
        viewport={{ once: true }}
        transition={{ duration: 0.6 }}
      >
        <h2 className="text-2xl sm:text-4xl font-bold tracking-tight mb-4">Ready to test the digital twin?</h2>
        <p className="text-muted-foreground max-w-xl mx-auto mb-8 leading-relaxed">
          Open a chat console, speak to Shivam directly, or pick one of his available calendar slots to schedule a real meeting.
        </p>
        <div className="flex flex-wrap items-center justify-center gap-4">
          <Link
            href="/chat"
            className="flex items-center space-x-2 rounded-xl bg-purple-600 px-6 py-3 text-sm font-semibold text-white shadow-md hover:bg-purple-500 transition-all duration-200"
          >
            <span>Start Chat Console</span>
          </Link>
          <Link
            href="/voice"
            className="flex items-center space-x-2 rounded-xl border border-white/[0.08] bg-white/[0.03] px-6 py-3 text-sm font-semibold text-muted-foreground hover:text-foreground hover:bg-white/[0.06] transition-all duration-200"
          >
            <span>Voice Call</span>
          </Link>
        </div>
      </motion.section>
    </div>
  );
}
