'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useTheme } from 'next-themes';
import { Sun, Moon, Sparkles, LogIn, LayoutDashboard, Menu, X } from 'lucide-react';
import { useAdminStore } from '@/stores/useAdminStore';
import { api } from '@/services/api';

export default function Navbar() {
  const pathname = usePathname();
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const { isAuthenticated, setAuthenticated } = useAdminStore();

  useEffect(() => {
    setMounted(true);
    // Silent verify admin session
    api.get('/auth/verify')
      .then((res) => {
        if (res.data.authenticated) {
          setAuthenticated(true);
        } else {
          setAuthenticated(false);
        }
      })
      .catch(() => setAuthenticated(false));
  }, [setAuthenticated]);

  const navLinks = [
    { name: 'Home', href: '/' },
    { name: 'Chat Twin', href: '/chat' },
    { name: 'Voice Twin', href: '/voice' },
    { name: 'Schedule', href: '/schedule' },
  ];

  return (
    <nav className="sticky top-0 z-50 w-full border-b border-white/[0.05] bg-background/80 backdrop-blur-md transition-colors duration-300">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <div className="flex items-center">
            <Link href="/" className="flex items-center space-x-2 text-xl font-bold tracking-tight">
              <Sparkles className="h-6 w-6 text-purple-500 animate-pulse" />
              <span className="bg-gradient-to-r from-purple-400 via-pink-500 to-indigo-500 bg-clip-text text-transparent glow-text">
                AI Shivam
              </span>
            </Link>
          </div>

          {/* Desktop Nav */}
          <div className="hidden md:flex items-center space-x-8">
            {navLinks.map((link) => {
              const isActive = pathname === link.href;
              return (
                <Link
                  key={link.name}
                  href={link.href}
                  className={`text-sm font-medium transition-colors duration-200 hover:text-purple-400 ${
                    isActive ? 'text-purple-400 font-semibold' : 'text-muted-foreground'
                  }`}
                >
                  {link.name}
                </Link>
              );
            })}
          </div>

          {/* Right section: Dark Mode Toggle & Admin Button */}
          <div className="hidden md:flex items-center space-x-4">
            {/* Theme Toggle */}
            {mounted && (
              <button
                onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
                className="rounded-lg p-2 text-muted-foreground hover:bg-white/[0.05] hover:text-foreground transition-all duration-200"
                aria-label="Toggle Theme"
              >
                {theme === 'dark' ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
              </button>
            )}

            {/* Admin Console Link */}
            {isAuthenticated ? (
              <Link
                href="/admin/dashboard"
                className="flex items-center space-x-1.5 rounded-lg border border-purple-500/30 bg-purple-500/10 px-4 py-2 text-xs font-semibold text-purple-400 hover:bg-purple-500/20 transition-all duration-200"
              >
                <LayoutDashboard className="h-4 w-4" />
                <span>Console</span>
              </Link>
            ) : (
              <Link
                href="/admin/login"
                className="flex items-center space-x-1.5 rounded-lg border border-white/[0.08] px-4 py-2 text-xs font-semibold text-muted-foreground hover:text-foreground hover:bg-white/[0.05] transition-all duration-200"
              >
                <LogIn className="h-4 w-4" />
                <span>Admin Login</span>
              </Link>
            )}
          </div>

          {/* Mobile menu button */}
          <div className="flex md:hidden items-center space-x-3">
            {mounted && (
              <button
                onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
                className="rounded-lg p-2 text-muted-foreground hover:bg-white/[0.05] transition-all duration-200"
                aria-label="Toggle Theme"
              >
                {theme === 'dark' ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
              </button>
            )}
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="rounded-lg p-2 text-muted-foreground hover:bg-white/[0.05] transition-all duration-200"
              aria-label="Main Menu"
            >
              {isOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu */}
      {isOpen && (
        <div className="md:hidden border-t border-white/[0.05] bg-background/95 backdrop-blur-lg px-4 pt-2 pb-4 space-y-2">
          {navLinks.map((link) => {
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.name}
                href={link.href}
                onClick={() => setIsOpen(false)}
                className={`block rounded-lg px-3 py-2 text-base font-medium transition-colors ${
                  isActive ? 'bg-purple-500/10 text-purple-400 font-semibold' : 'text-muted-foreground hover:bg-white/[0.05]'
                }`}
              >
                {link.name}
              </Link>
            );
          })}
          <div className="pt-2 border-t border-white/[0.05]">
            {isAuthenticated ? (
              <Link
                href="/admin/dashboard"
                onClick={() => setIsOpen(false)}
                className="flex items-center space-x-2 rounded-lg bg-purple-500/10 px-3 py-2.5 text-base font-medium text-purple-400"
              >
                <LayoutDashboard className="h-5 w-5" />
                <span>Admin Console</span>
              </Link>
            ) : (
              <Link
                href="/admin/login"
                onClick={() => setIsOpen(false)}
                className="flex items-center space-x-2 rounded-lg px-3 py-2.5 text-base font-medium text-muted-foreground hover:bg-white/[0.05]"
              >
                <LogIn className="h-5 w-5" />
                <span>Admin Login</span>
              </Link>
            )}
          </div>
        </div>
      )}
    </nav>
  );
}
