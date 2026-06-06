'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import {
  User,
  Github,
  Upload,
  Calendar,
  Layers,
  Settings,
  Sparkles,
  RefreshCw,
  LogOut,
  CheckCircle,
  XCircle,
  FileText
} from 'lucide-react';
import { useAdminStore } from '@/stores/useAdminStore';
import { api } from '@/services/api';

export default function DashboardPage() {
  const router = useRouter();
  const { isAuthenticated, isAdminLoading, setAuthenticated, logout } = useAdminStore();

  // Active Tab
  const [activeTab, setActiveTab] = useState<'profile' | 'status' | 'slots'>('profile');

  // Form states
  const [githubUrl, setGithubUrl] = useState('https://github.com/shivam');
  const [additionalInfo, setAdditionalInfo] = useState('');
  const [slotsInput, setSlotsInput] = useState<string[]>([
    '2026-07-10T09:00',
    '2026-07-11T10:30',
    '2026-07-12T14:00',
    '2026-07-13T16:00',
    '2026-07-14T11:00',
  ]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // Operation indicators
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitSuccess, setSubmitSuccess] = useState<boolean>(false);
  const [activeProfileId, setActiveProfileId] = useState<string | null>(null);

  // Poll status interval state
  const [pipelineStatus, setPipelineStatus] = useState<any>(null);

  // Verify auth session
  useEffect(() => {
    api.get('/auth/verify')
      .then((res) => {
        if (res.data.authenticated) {
          setAuthenticated(true);
        } else {
          setAuthenticated(false);
          router.push('/admin/login');
        }
      })
      .catch(() => {
        setAuthenticated(false);
        router.push('/admin/login');
      });
  }, [setAuthenticated, router]);

  // Load last saved profile ID to poll pipeline status if any
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const savedId = localStorage.getItem('last_profile_id');
      if (savedId) {
        setActiveProfileId(savedId);
      }
    }
  }, []);

  // Poll processing status every 4 seconds if a profile job is active
  useEffect(() => {
    if (!activeProfileId || !isAuthenticated) return;

    const fetchStatus = () => {
      api.get(`/admin/profile/status?profile_id=${activeProfileId}`)
        .then((res) => {
          setPipelineStatus(res.data);
          if (res.data.status === 'COMPLETED' || res.data.status === 'FAILED') {
            // Stop polling or slow it down
          }
        })
        .catch((err) => {
          console.error("Failed to fetch pipeline status:", err);
        });
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 4000);
    return () => clearInterval(interval);
  }, [activeProfileId, isAuthenticated]);

  // Fetch slots to show booked status
  const { data: adminSlots, refetch: refetchSlots } = useQuery({
    queryKey: ['adminSlots'],
    queryFn: async () => {
      const res = await api.get('/scheduling/slots');
      return res.data;
    },
    enabled: isAuthenticated,
  });

  const handleLogout = async () => {
    try {
      await api.post('/auth/logout');
      logout();
      router.push('/admin/login');
    } catch (err) {
      console.error(err);
    }
  };

  const handleSlotChange = (index: number, value: string) => {
    const nextSlots = [...slotsInput];
    nextSlots[index] = value;
    setSlotsInput(nextSlots);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setSubmitError('Please select a PDF resume file to upload.');
      return;
    }
    
    setIsSubmitting(true);
    setSubmitError(null);
    setSubmitSuccess(false);

    try {
      const formData = new FormData();
      formData.append('resume_file', selectedFile);
      formData.append('github_url', githubUrl);
      formData.append('additional_information', additionalInfo);
      
      // Convert availability inputs to standard ISO strings
      const isoSlots = slotsInput.map(s => {
        // Appending UTC offset
        return new Date(s).toISOString();
      });
      formData.append('availability', JSON.stringify(isoSlots));

      const response = await api.post('/admin/profile', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      const newProfileId = response.data.id;
      setActiveProfileId(newProfileId);
      if (typeof window !== 'undefined') {
        localStorage.setItem('last_profile_id', newProfileId);
      }

      setSubmitSuccess(true);
      setActiveTab('status'); // switch to track status
      refetchSlots();
    } catch (err: any) {
      console.error(err);
      setSubmitError(err.response?.data?.detail || 'Failed to submit profile data.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isAdminLoading || !isAuthenticated) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <RefreshCw className="h-10 w-10 animate-spin text-purple-500" />
      </div>
    );
  }

  return (
    <div className="flex-1 py-8 px-4 space-y-8 max-w-6xl mx-auto">
      {/* Dashboard Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-white/[0.05] pb-6">
        <div className="space-y-1">
          <div className="inline-flex items-center space-x-2 rounded-full border border-purple-500/30 bg-purple-500/10 px-3 py-1 text-xs font-semibold tracking-wide text-purple-400">
            <Sparkles className="h-3.5 w-3.5" />
            <span>CONTROL CENTER</span>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight">Console Dashboard</h1>
        </div>
        <button
          onClick={handleLogout}
          className="flex items-center space-x-2 rounded-xl border border-red-500/30 bg-red-500/5 px-4 py-2.5 text-xs font-semibold text-red-400 hover:bg-red-500/15 transition"
        >
          <LogOut className="h-4 w-4" />
          <span>Sign Out</span>
        </button>
      </div>

      {/* Tabs Layout */}
      <div className="flex border-b border-white/[0.05] gap-4 text-sm font-semibold">
        <button
          onClick={() => setActiveTab('profile')}
          className={`pb-4 border-b-2 transition-all ${
            activeTab === 'profile' ? 'border-purple-500 text-purple-400' : 'border-transparent text-muted-foreground'
          }`}
        >
          Profile Settings
        </button>
        <button
          onClick={() => setActiveTab('status')}
          className={`pb-4 border-b-2 transition-all flex items-center space-x-2 ${
            activeTab === 'status' ? 'border-purple-500 text-purple-400' : 'border-transparent text-muted-foreground'
          }`}
        >
          <span>Ingestion Tracker</span>
          {pipelineStatus && pipelineStatus.status === 'PROCESSING' && (
            <span className="h-2 w-2 rounded-full bg-yellow-400 animate-ping" />
          )}
        </button>
        <button
          onClick={() => {
            setActiveTab('slots');
            refetchSlots();
          }}
          className={`pb-4 border-b-2 transition-all ${
            activeTab === 'slots' ? 'border-purple-500 text-purple-400' : 'border-transparent text-muted-foreground'
          }`}
        >
          Interview & Bookings
        </button>
      </div>

      {/* Tab Panels */}
      <div className="pt-6">
        {/* Tab 1: Profile Setup */}
        {activeTab === 'profile' && (
          <form onSubmit={handleSubmit} className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2 space-y-6">
              {/* GitHub Settings */}
              <div className="glass-panel rounded-3xl p-6 space-y-4">
                <h2 className="text-lg font-bold flex items-center space-x-2">
                  <Github className="h-5 w-5 text-purple-400" />
                  <span>GitHub Sync Url</span>
                </h2>
                <input
                  type="url"
                  value={githubUrl}
                  onChange={(e) => setGithubUrl(e.target.value)}
                  placeholder="https://github.com/shivam"
                  className="w-full bg-white/[0.02] border border-white/[0.08] rounded-xl px-4 py-2.5 text-sm text-foreground focus:outline-none focus:border-purple-500"
                />
              </div>

              {/* Resume File Upload */}
              <div className="glass-panel rounded-3xl p-6 space-y-4">
                <h2 className="text-lg font-bold flex items-center space-x-2">
                  <Upload className="h-5 w-5 text-purple-400" />
                  <span>Upload PDF Resume</span>
                </h2>
                <div className="border border-dashed border-white/10 rounded-2xl p-8 text-center hover:bg-white/[0.01] transition-all relative">
                  <input
                    type="file"
                    accept=".pdf"
                    onChange={(e) => {
                      if (e.target.files && e.target.files[0]) {
                        setSelectedFile(e.target.files[0]);
                      }
                    }}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                  />
                  <FileText className="mx-auto h-12 w-12 text-muted-foreground opacity-50 mb-3" />
                  <p className="text-sm font-semibold">
                    {selectedFile ? selectedFile.name : 'Drag & drop or click to upload resume PDF'}
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">PDF format only (Max 10 MB)</p>
                </div>
              </div>

              {/* Additional Information */}
              <div className="glass-panel rounded-3xl p-6 space-y-4">
                <h2 className="text-lg font-bold flex items-center space-x-2">
                  <Layers className="h-5 w-5 text-purple-400" />
                  <span>Additional Information</span>
                </h2>
                <textarea
                  rows={6}
                  value={additionalInfo}
                  onChange={(e) => setAdditionalInfo(e.target.value)}
                  placeholder="Paste cover letters, portfolio text, bio descriptions, or additional credentials Shivam wants the AI twin to know..."
                  className="w-full bg-white/[0.02] border border-white/[0.08] rounded-xl px-4 py-3 text-sm text-foreground placeholder-muted-foreground focus:outline-none focus:border-purple-500"
                />
              </div>
            </div>

            {/* Availability Slots setup */}
            <div className="lg:col-span-1 space-y-6">
              <div className="glass-panel rounded-3xl p-6 space-y-4">
                <h2 className="text-lg font-bold flex items-center space-x-2">
                  <Calendar className="h-5 w-5 text-purple-400" />
                  <span>Availability (Exactly 5 slots)</span>
                </h2>
                <div className="space-y-3">
                  {slotsInput.map((slot, index) => (
                    <div key={index} className="space-y-1">
                      <label className="text-[10px] uppercase font-semibold text-muted-foreground block">
                        Slot {index + 1}
                      </label>
                      <input
                        type="datetime-local"
                        value={slot}
                        onChange={(e) => handleSlotChange(index, e.target.value)}
                        className="w-full bg-white/[0.02] border border-white/[0.08] rounded-xl px-3 py-2 text-xs text-foreground focus:outline-none focus:border-purple-500"
                      />
                    </div>
                  ))}
                </div>
              </div>

              {submitError && (
                <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-4 text-xs text-red-400">
                  {submitError}
                </div>
              )}

              {submitSuccess && (
                <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4 text-xs text-emerald-400">
                  Profile sync request submitted successfully! Ingestion triggered.
                </div>
              )}

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full rounded-2xl bg-purple-600 py-3.5 text-sm font-semibold text-white hover:bg-purple-500 shadow-md hover:shadow-purple-500/10 active:scale-[0.98] transition-all disabled:opacity-50"
              >
                {isSubmitting ? 'Syncing...' : 'Sync & Reprocess Ingestion'}
              </button>
            </div>
          </form>
        )}

        {/* Tab 2: Ingestion Status Tracker */}
        {activeTab === 'status' && (
          <div className="max-w-3xl mx-auto glass-panel rounded-3xl p-8 border border-white/[0.05] space-y-6">
            <h2 className="text-xl font-bold tracking-tight">Active Ingestion Pipeline</h2>
            
            {pipelineStatus ? (
              <div className="space-y-6">
                {/* Status Indicator */}
                <div className="flex items-center justify-between">
                  <div>
                    <span className="block text-xs text-muted-foreground uppercase font-semibold">Status State</span>
                    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold mt-1 border ${
                      pipelineStatus.status === 'COMPLETED' ? 'border-emerald-500/20 bg-emerald-500/5 text-emerald-400' :
                      pipelineStatus.status === 'FAILED' ? 'border-red-500/20 bg-red-500/5 text-red-400' :
                      'border-yellow-500/20 bg-yellow-500/5 text-yellow-400'
                    }`}>
                      {pipelineStatus.status}
                    </span>
                  </div>
                  <div>
                    <span className="block text-xs text-muted-foreground uppercase font-semibold text-right">Progress</span>
                    <span className="block text-lg font-bold text-purple-400 text-right mt-1">
                      {Math.round(pipelineStatus.progress * 100)}%
                    </span>
                  </div>
                </div>

                {/* Progress bar */}
                <div className="w-full bg-white/5 h-2 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-purple-600 rounded-full transition-all duration-500"
                    style={{ width: `${pipelineStatus.progress * 100}%` }}
                  />
                </div>

                {/* Processing Steps */}
                <div className="bg-white/[0.02] border border-white/[0.05] rounded-2xl p-5 space-y-4">
                  <div className="flex items-start justify-between">
                    <span className="text-xs uppercase font-semibold text-muted-foreground">Current Step Node</span>
                    <span className="text-xs font-semibold text-foreground">{pipelineStatus.current_step}</span>
                  </div>
                  <div className="flex items-start justify-between">
                    <span className="text-xs uppercase font-semibold text-muted-foreground">Last Updated</span>
                    <span className="text-xs text-muted-foreground">
                      {new Date(pipelineStatus.last_updated).toLocaleString()}
                    </span>
                  </div>
                </div>

                {pipelineStatus.status === 'FAILED' && pipelineStatus.error_message && (
                  <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-4 flex items-start space-x-3 text-red-400 text-xs">
                    <XCircle className="h-5 w-5 flex-shrink-0 mt-0.5" />
                    <div>
                      <span className="font-semibold block mb-0.5">Ingestion Error</span>
                      <p>{pipelineStatus.error_message}</p>
                    </div>
                  </div>
                )}

                {pipelineStatus.status === 'COMPLETED' && (
                  <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4 flex items-start space-x-3 text-emerald-400 text-xs">
                    <CheckCircle className="h-5 w-5 flex-shrink-0 mt-0.5" />
                    <div>
                      <span className="font-semibold block mb-0.5">Pipeline Complete</span>
                      <p>Shivam's knowledge documents, chunkings, embeddings, and Qdrant index synced successfully.</p>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-12 text-muted-foreground border border-dashed border-white/10 rounded-2xl space-y-2">
                <RefreshCw className="mx-auto h-8 w-8 text-muted-foreground opacity-50" />
                <p className="text-sm">No active ingestion pipeline found.</p>
                <p className="text-[10px]">Configure your profile settings and click Sync to initiate.</p>
              </div>
            )}
          </div>
        )}

        {/* Tab 3: Slots & Bookings */}
        {activeTab === 'slots' && (
          <div className="glass-panel rounded-3xl p-6 border border-white/[0.05] space-y-6">
            <h2 className="text-xl font-bold tracking-tight">Interview Scheduling Manager</h2>
            
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm border-collapse">
                <thead>
                  <tr className="border-b border-white/10 text-muted-foreground text-xs uppercase font-semibold">
                    <th className="py-3 px-4">Date & Time</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4">Recruiter Name</th>
                    <th className="py-3 px-4">Recruiter Email</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.05]">
                  {adminSlots && adminSlots.length > 0 ? (
                    adminSlots.map((slot: any) => (
                      <tr key={slot.id} className="hover:bg-white/[0.01]">
                        <td className="py-4 px-4 font-medium text-foreground">
                          {new Date(slot.slot).toLocaleString([], {
                            year: 'numeric',
                            month: 'short',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit'
                          })}
                        </td>
                        <td className="py-4 px-4">
                          <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold ${
                            slot.is_booked
                              ? 'bg-red-500/10 text-red-400 border border-red-500/20'
                              : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                          }`}>
                            {slot.is_booked ? 'Booked' : 'Available'}
                          </span>
                        </td>
                        <td className="py-4 px-4 text-muted-foreground">
                          {slot.booked_by_name || '—'}
                        </td>
                        <td className="py-4 px-4 text-muted-foreground">
                          {slot.booked_by_email || '—'}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={4} className="py-8 text-center text-muted-foreground">
                        No availability slots seeded. Set availability in Profile Settings.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
