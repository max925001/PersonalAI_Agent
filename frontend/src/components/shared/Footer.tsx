import React from 'react';
import Link from 'next/link';

export default function Footer() {
  return (
    <footer className="w-full border-t border-white/[0.05] py-8 bg-background/50 backdrop-blur-sm mt-auto">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between space-y-4 md:space-y-0">
        <div className="text-sm text-muted-foreground">
          © {new Date().getFullYear()} AI Shivam. All rights reserved.
        </div>
        <div className="flex space-x-6 text-sm text-muted-foreground">
          <Link href="/" className="hover:text-purple-400 transition-colors duration-200">
            Platform Info
          </Link>
          <Link href="/chat" className="hover:text-purple-400 transition-colors duration-200">
            Interactive Chat
          </Link>
          <Link href="/voice" className="hover:text-purple-400 transition-colors duration-200">
            Voice Agent
          </Link>
          <Link href="/schedule" className="hover:text-purple-400 transition-colors duration-200">
            Book Recruiter Slot
          </Link>
        </div>
      </div>
    </footer>
  );
}
