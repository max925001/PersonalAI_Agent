'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as zod from 'zod';
import { motion } from 'framer-motion';
import { Lock, Mail, Sparkles, AlertCircle } from 'lucide-react';
import { api } from '@/services/api';
import { useAdminStore } from '@/stores/useAdminStore';

// Login Validation Schema
const loginSchema = zod.object({
  email: zod.string().email('Invalid email address'),
  password: zod.string().min(6, 'Password must be at least 6 characters'),
});

type LoginFormData = zod.infer<typeof loginSchema>;

export default function LoginPage() {
  const router = useRouter();
  const { setAuthenticated } = useAdminStore();
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginFormData) => {
    setIsLoading(true);
    setError(null);

    try {
      // Calls POST /auth/login which sets HttpOnly cookies on response
      await api.post('/auth/login', {
        email: data.email,
        password: data.password,
      });

      setAuthenticated(true, data.email);
      router.push('/admin/dashboard');
    } catch (err: any) {
      console.error(err);
      setError(
        err.response?.data?.detail || 
        'Login failed. Please verify your credentials and try again.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex-1 flex items-center justify-center min-h-[60vh] px-4">
      <motion.div
        className="w-full max-w-md glass-panel rounded-3xl p-8 border border-white/[0.05] space-y-6"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center space-x-2 rounded-full border border-purple-500/30 bg-purple-500/10 px-3 py-1 text-xs font-semibold tracking-wide text-purple-400">
            <Sparkles className="h-3.5 w-3.5" />
            <span>SECURE CONSOLE</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight">Admin Console</h1>
          <p className="text-xs text-muted-foreground">
            Sign in to configure Shivam's digital twin parameters.
          </p>
        </div>

        {error && (
          <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-4 flex items-start space-x-3 text-red-400 text-xs">
            <AlertCircle className="h-5 w-5 flex-shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* Email input */}
          <div className="space-y-1">
            <label htmlFor="email" className="text-xs font-semibold text-muted-foreground block">
              Admin Email
            </label>
            <div className="relative">
              <Mail className="absolute left-3.5 top-3 h-4 w-4 text-muted-foreground" />
              <input
                id="email"
                type="email"
                placeholder="shivam@example.com"
                {...register('email')}
                className="w-full bg-white/[0.02] border border-white/[0.08] rounded-xl py-2.5 pl-10 pr-4 text-sm text-foreground placeholder-muted-foreground focus:outline-none focus:border-purple-500 focus:bg-white/[0.04] transition-all"
              />
            </div>
            {errors.email && <p className="text-xs text-destructive">{errors.email.message}</p>}
          </div>

          {/* Password input */}
          <div className="space-y-1">
            <label htmlFor="password" className="text-xs font-semibold text-muted-foreground block">
              Password
            </label>
            <div className="relative">
              <Lock className="absolute left-3.5 top-3 h-4 w-4 text-muted-foreground" />
              <input
                id="password"
                type="password"
                placeholder="••••••••"
                {...register('password')}
                className="w-full bg-white/[0.02] border border-white/[0.08] rounded-xl py-2.5 pl-10 pr-4 text-sm text-foreground placeholder-muted-foreground focus:outline-none focus:border-purple-500 focus:bg-white/[0.04] transition-all"
              />
            </div>
            {errors.password && <p className="text-xs text-destructive">{errors.password.message}</p>}
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={isLoading}
            className="w-full rounded-xl bg-purple-600 py-3 text-sm font-semibold text-white hover:bg-purple-500 disabled:bg-purple-600/50 flex items-center justify-center space-x-2 transition-all duration-200"
          >
            {isLoading ? <span>Signing In...</span> : <span>Sign In</span>}
          </button>
        </form>
      </motion.div>
    </div>
  );
}
