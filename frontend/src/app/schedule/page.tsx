'use client';

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { Calendar, Clock, User, Mail, CheckCircle2, AlertCircle, Sparkles } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as zod from 'zod';
import { schedulingService, Slot } from '@/services/schedulingService';

// Zod validation schema
const bookingSchema = zod.object({
  name: zod.string().min(1, 'Name is required').max(100, 'Name must be less than 100 characters'),
  email: zod.string().email('Invalid corporate email address'),
});

type BookingFormData = zod.infer<typeof bookingSchema>;

export default function SchedulePage() {
  const queryClient = useQueryClient();
  const [selectedSlot, setSelectedSlot] = useState<Slot | null>(null);
  const [isSuccessState, setIsSuccessState] = useState(false);
  const [confirmedTime, setConfirmedTime] = useState<string>('');

  // 1. Fetch available slots
  const { data: slots, isLoading, error } = useQuery({
    queryKey: ['availableSlots'],
    queryFn: schedulingService.getAvailableSlots,
  });

  // 2. React Hook Form setup
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<BookingFormData>({
    resolver: zodResolver(bookingSchema),
  });

  // 3. Book Slot Mutation
  const bookMutation = useMutation({
    mutationFn: schedulingService.bookSlot,
    onSuccess: (data) => {
      // Refresh available slots query
      queryClient.invalidateQueries({ queryKey: ['availableSlots'] });
      // Show success screen
      if (selectedSlot) {
        const dateStr = new Date(selectedSlot.slot).toLocaleString([], {
          weekday: 'long',
          year: 'numeric',
          month: 'long',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
        });
        setConfirmedTime(dateStr);
      }
      setIsSuccessState(true);
      setSelectedSlot(null);
      reset();
    },
  });

  const onSubmit = (data: BookingFormData) => {
    if (!selectedSlot) return;
    bookMutation.mutate({
      slot: selectedSlot.slot,
      name: data.name,
      email: data.email,
    });
  };

  const formatDate = (isoStr: string) => {
    return new Date(isoStr).toLocaleDateString([], {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
    });
  };

  const formatTime = (isoStr: string) => {
    return new Date(isoStr).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (isSuccessState) {
    return (
      <div className="flex items-center justify-center min-h-[60vh] px-4">
        <motion.div
          className="w-full max-w-lg glass-panel rounded-3xl p-8 md:p-10 text-center space-y-6 border border-emerald-500/20"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
        >
          <div className="mx-auto h-16 w-16 rounded-full bg-emerald-500/10 flex items-center justify-center text-emerald-400">
            <CheckCircle2 className="h-10 w-10 animate-bounce" />
          </div>
          <h1 className="text-3xl font-bold tracking-tight">Interview Confirmed! ✅</h1>
          <div className="bg-white/[0.02] border border-white/[0.05] rounded-2xl p-6 text-left space-y-4">
            <div className="flex items-start space-x-3 text-muted-foreground">
              <Calendar className="h-5 w-5 text-purple-400 mt-0.5" />
              <div>
                <span className="block text-xs uppercase font-semibold text-purple-400">Date & Time</span>
                <span className="text-sm font-medium text-foreground">{confirmedTime}</span>
              </div>
            </div>
            <div className="flex items-start space-x-3 text-muted-foreground">
              <User className="h-5 w-5 text-purple-400 mt-0.5" />
              <div>
                <span className="block text-xs uppercase font-semibold text-purple-400">Candidate</span>
                <span className="text-sm font-medium text-foreground">Shivam (AI Developer)</span>
              </div>
            </div>
          </div>
          <p className="text-sm text-muted-foreground leading-relaxed">
            Shivam is excited to connect with you and discuss how he can contribute to your team. A calendar invitation has been generated and flagged in the repository.
          </p>
          <button
            onClick={() => setIsSuccessState(false)}
            className="w-full rounded-xl bg-purple-600 py-3 text-sm font-semibold text-white hover:bg-purple-500 transition-all duration-200"
          >
            Schedule Another Slot
          </button>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl py-8 px-4 space-y-8">
      {/* Page Header */}
      <div className="text-center max-w-2xl mx-auto space-y-3">
        <div className="inline-flex items-center space-x-2 rounded-full border border-purple-500/30 bg-purple-500/10 px-3 py-1 text-xs font-semibold tracking-wide text-purple-400">
          <Sparkles className="h-3.5 w-3.5" />
          <span>REAL-TIME CALENDAR INTEGRATION</span>
        </div>
        <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight">Schedule an Interview</h1>
        <p className="text-sm sm:text-base text-muted-foreground leading-relaxed">
          Shivam is currently exploring new engineering roles. Select one of his open availability slots below to book a discussion.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Calendar Slots Grid */}
        <div className="lg:col-span-2 space-y-4">
          <h2 className="text-lg font-bold tracking-tight">Available Slots</h2>
          
          {isLoading && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="h-28 rounded-2xl bg-white/[0.02] border border-white/[0.05] animate-pulse" />
              ))}
            </div>
          )}

          {error && (
            <div className="rounded-2xl border border-destructive/20 bg-destructive/10 p-6 text-center space-y-3 text-destructive">
              <AlertCircle className="mx-auto h-8 w-8" />
              <p className="text-sm font-medium">Failed to retrieve interview slots. Please try again later.</p>
            </div>
          )}

          {!isLoading && !error && slots?.length === 0 && (
            <div className="rounded-2xl border border-white/[0.05] bg-white/[0.01] p-12 text-center space-y-3">
              <Calendar className="mx-auto h-10 w-10 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">Shivam is fully booked or hasn't updated his availability slots recently. Please check back later!</p>
            </div>
          )}

          {!isLoading && !error && slots && slots.length > 0 && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {slots.map((slot) => (
                <button
                  key={slot.id}
                  onClick={() => setSelectedSlot(slot)}
                  className={`flex items-center justify-between p-5 rounded-2xl border transition-all duration-300 ${
                    selectedSlot?.id === slot.id
                      ? 'border-purple-500 bg-purple-500/10 shadow-lg shadow-purple-500/10'
                      : 'border-white/[0.05] bg-white/[0.02] hover:bg-white/[0.05] hover:border-white/[0.1]'
                  }`}
                >
                  <div className="text-left space-y-1">
                    <span className="block text-sm font-bold text-foreground">{formatDate(slot.slot)}</span>
                    <span className="block text-xs text-muted-foreground flex items-center space-x-1">
                      <Clock className="h-3.5 w-3.5 text-purple-400 inline mr-1" />
                      {formatTime(slot.slot)}
                    </span>
                  </div>
                  <div className="rounded-lg bg-purple-500/10 px-3 py-1 text-xs font-semibold text-purple-400">
                    Book Slot
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Booking Form Card */}
        <div className="lg:col-span-1">
          <div className="sticky top-24 glass-panel rounded-3xl p-6 space-y-6">
            <h2 className="text-lg font-bold tracking-tight">Confirm Details</h2>
            
            {selectedSlot ? (
              <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                <div className="rounded-xl border border-purple-500/20 bg-purple-500/5 p-4 space-y-1">
                  <span className="block text-xs text-purple-400 uppercase font-semibold">Selected Time</span>
                  <span className="block text-sm font-bold text-foreground">
                    {formatDate(selectedSlot.slot)} at {formatTime(selectedSlot.slot)}
                  </span>
                </div>

                {/* Name Input */}
                <div className="space-y-1">
                  <label htmlFor="name" className="text-xs font-semibold text-muted-foreground block">
                    Full Name
                  </label>
                  <div className="relative">
                    <User className="absolute left-3.5 top-3 h-4 w-4 text-muted-foreground" />
                    <input
                      id="name"
                      type="text"
                      placeholder="Jane Doe"
                      {...register('name')}
                      className="w-full bg-white/[0.02] border border-white/[0.08] rounded-xl py-2.5 pl-10 pr-4 text-sm text-foreground placeholder-muted-foreground focus:outline-none focus:border-purple-500 focus:bg-white/[0.04] transition-all"
                    />
                  </div>
                  {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
                </div>

                {/* Email Input */}
                <div className="space-y-1">
                  <label htmlFor="email" className="text-xs font-semibold text-muted-foreground block">
                    Corporate Email
                  </label>
                  <div className="relative">
                    <Mail className="absolute left-3.5 top-3 h-4 w-4 text-muted-foreground" />
                    <input
                      id="email"
                      type="email"
                      placeholder="jane.doe@microsoft.com"
                      {...register('email')}
                      className="w-full bg-white/[0.02] border border-white/[0.08] rounded-xl py-2.5 pl-10 pr-4 text-sm text-foreground placeholder-muted-foreground focus:outline-none focus:border-purple-500 focus:bg-white/[0.04] transition-all"
                    />
                  </div>
                  {errors.email && <p className="text-xs text-destructive">{errors.email.message}</p>}
                </div>

                {/* Submit Button */}
                <button
                  type="submit"
                  disabled={bookMutation.isPending}
                  className="w-full rounded-xl bg-purple-600 py-3 text-sm font-semibold text-white hover:bg-purple-500 disabled:bg-purple-600/50 flex items-center justify-center space-x-2 transition-all duration-200"
                >
                  {bookMutation.isPending ? (
                    <span>Booking...</span>
                  ) : (
                    <>
                      <CheckCircle2 className="h-4 w-4" />
                      <span>Confirm Booking</span>
                    </>
                  )}
                </button>

                {bookMutation.isError && (
                  <p className="text-xs text-center text-destructive">
                    {bookMutation.error instanceof Error ? bookMutation.error.message : 'Error confirming booking.'}
                  </p>
                )}
              </form>
            ) : (
              <div className="text-center py-12 text-muted-foreground border border-dashed border-white/10 rounded-2xl space-y-2">
                <Calendar className="mx-auto h-8 w-8 text-muted-foreground opacity-50" />
                <p className="text-sm">Please select a time slot on the left to begin scheduling.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
