import type { Metadata } from 'next';
import { Outfit, JetBrains_Mono } from 'next/font/google';
import './globals.css';
import { ThemeProvider } from '@/providers/theme-provider';
import QueryProvider from '@/providers/query-provider';
import Navbar from '@/components/shared/Navbar';
import Footer from '@/components/shared/Footer';

const outfit = Outfit({
  variable: '--font-outfit',
  subsets: ['latin'],
});

const jetbrainsMono = JetBrains_Mono({
  variable: '--font-mono',
  subsets: ['latin'],
});

export const metadata: Metadata = {
  title: 'AI Shivam | Interactive Digital Twin Platform',
  description: 'Explore Shivam\'s experience, projects, and skills through his voice-enabled AI digital twin. Chat in real time, talk over voice, or schedule an interview.',
  keywords: 'Shivam, AI Digital Twin, Recruiter Chat, Voice Agent, RAG Portfolio, Next.js, FastAPI',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${outfit.variable} ${jetbrainsMono.variable} font-sans min-h-screen flex flex-col antialiased bg-background text-foreground transition-colors duration-300`}>
        <QueryProvider>
          <ThemeProvider>
            <Navbar />
            <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col justify-start">
              {children}
            </main>
            <Footer />
          </ThemeProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
