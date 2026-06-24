"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { isAuthenticated } from "@/lib/auth";
import { Stethoscope, ArrowRight, Activity, ShieldCheck, Sparkles, BookOpen } from "lucide-react";

export default function LandingPage() {
  const [isAuthed, setIsAuthed] = useState(false);

  useEffect(() => {
    setIsAuthed(isAuthenticated());
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col relative overflow-hidden">
      {/* Decorative Glow Effects */}
      <div className="absolute top-0 left-1/4 -translate-x-1/2 w-[500px] h-[500px] rounded-full bg-emerald-500/5 blur-[120px] pointer-events-none"></div>
      <div className="absolute bottom-0 right-1/4 translate-x-1/2 w-[500px] h-[500px] rounded-full bg-teal-500/5 blur-[120px] pointer-events-none"></div>

      {/* Navigation Header */}
      <header className="border-b border-slate-900 bg-slate-950/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="h-9 w-9 rounded-lg bg-gradient-to-tr from-emerald-500 to-teal-400 flex items-center justify-center shadow-lg shadow-emerald-500/10">
              <Stethoscope className="h-5 w-5 text-slate-950" />
            </div>
            <span className="font-bold tracking-wide text-lg bg-gradient-to-r from-emerald-400 to-teal-300 bg-clip-text text-transparent">
              MedBot
            </span>
          </div>

          <div className="flex items-center gap-4">
            {isAuthed ? (
              <Link
                href="/chat"
                className="bg-gradient-to-r from-emerald-500 to-teal-500 text-slate-950 text-sm font-semibold px-4 py-2 rounded-lg hover:opacity-95 shadow-md shadow-emerald-500/10 transition-all cursor-pointer"
              >
                Go to Workspace
              </Link>
            ) : (
              <>
                <Link
                  href="/login"
                  className="text-slate-300 hover:text-emerald-400 text-sm font-medium transition-all cursor-pointer"
                >
                  Sign In
                </Link>
                <Link
                  href="/register"
                  className="bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-sm font-semibold px-4 py-2 rounded-lg transition-all cursor-pointer"
                >
                  Create Account
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col justify-center py-20 relative z-10">
        <div className="max-w-3xl">
          {/* Clinic Badge */}
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-emerald-500/20 bg-emerald-500/5 text-emerald-400 text-xs font-semibold uppercase tracking-wider mb-6">
            <Activity className="h-3.5 w-3.5 animate-pulse text-emerald-400" />
            Empowered by Gale Encyclopedia of Medicine
          </div>

          <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight leading-tight">
            AI-Powered Clinical{" "}
            <span className="bg-gradient-to-r from-emerald-400 via-teal-300 to-emerald-500 bg-clip-text text-transparent">
              Medical Encyclopedia
            </span>
          </h1>

          <p className="mt-6 text-base sm:text-lg text-slate-400 leading-relaxed max-w-2xl">
            MedBot combines local Large Language Models (Qwen) with Retrieval-Augmented Generation (RAG) to provide fast, reliable, and source-cited medical intelligence directly from the world’s most trusted health references.
          </p>

          <div className="mt-10 flex flex-wrap gap-4">
            {isAuthed ? (
              <Link
                href="/chat"
                className="flex items-center gap-2 bg-gradient-to-r from-emerald-500 to-teal-500 text-slate-950 text-base font-semibold px-6 py-3 rounded-lg hover:shadow-lg hover:shadow-emerald-500/20 transition-all hover:scale-[1.01] cursor-pointer"
              >
                Enter Medical Workspace
                <ArrowRight className="h-5 w-5 text-slate-950" />
              </Link>
            ) : (
              <>
                <Link
                  href="/register"
                  className="flex items-center gap-2 bg-gradient-to-r from-emerald-500 to-teal-500 text-slate-950 text-base font-semibold px-6 py-3 rounded-lg hover:shadow-lg hover:shadow-emerald-500/20 transition-all hover:scale-[1.01] cursor-pointer"
                >
                  Get Started
                  <ArrowRight className="h-5 w-5 text-slate-950" />
                </Link>
                <Link
                  href="/login"
                  className="flex items-center justify-center text-slate-300 hover:text-emerald-400 border border-slate-800 hover:border-emerald-500/20 bg-slate-900/30 px-6 py-3 rounded-lg text-base font-semibold transition-all cursor-pointer"
                >
                  Sign In
                </Link>
              </>
            )}
          </div>
        </div>

        {/* Feature Cards Section */}
        <div className="mt-24 grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="p-6 rounded-2xl border border-slate-900 bg-slate-900/20 backdrop-blur-sm">
            <div className="h-10 w-10 rounded-lg bg-emerald-500/10 flex items-center justify-center text-emerald-400 mb-4 border border-emerald-500/20">
              <Sparkles className="h-5 w-5" />
            </div>
            <h3 className="text-lg font-bold text-slate-100 mb-2">Local AI Inference</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Powered entirely by private, locally hosted LLMs (`qwen2.5-coder:7b`) to protect user queries and keep computation cost-effective.
            </p>
          </div>

          <div className="p-6 rounded-2xl border border-slate-900 bg-slate-900/20 backdrop-blur-sm">
            <div className="h-10 w-10 rounded-lg bg-teal-500/10 flex items-center justify-center text-teal-400 mb-4 border border-teal-500/20">
              <BookOpen className="h-5 w-5" />
            </div>
            <h3 className="text-lg font-bold text-slate-100 mb-2">Source Citations</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Every query triggers exact vector searches on the Gale Encyclopedia of Medicine, returning results with matching book page numbers.
            </p>
          </div>

          <div className="p-6 rounded-2xl border border-slate-900 bg-slate-900/20 backdrop-blur-sm">
            <div className="h-10 w-10 rounded-lg bg-emerald-500/10 flex items-center justify-center text-emerald-400 mb-4 border border-emerald-500/20">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <h3 className="text-lg font-bold text-slate-100 mb-2">Secure & Compliant</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Access is protected via JWT credentials linked to a remote Supabase DB storing transaction history, message chains, and logs.
            </p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 py-8 bg-slate-950 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-xs text-slate-500">
            &copy; {new Date().getFullYear()} MedBot AI Medical Assistant. All rights reserved.
          </p>
          <div className="flex gap-6 text-xs text-slate-400">
            <span className="hover:text-emerald-400 cursor-pointer">Security Protocol</span>
            <span className="hover:text-emerald-400 cursor-pointer">Privacy Charter</span>
            <span className="hover:text-emerald-400 cursor-pointer">Medical Disclaimer</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
