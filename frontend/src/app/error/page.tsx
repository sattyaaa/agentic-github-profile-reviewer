"use client";

import React, { Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { ShieldAlert, RotateCcw, Code2 } from "lucide-react";

function ErrorContent() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const code = searchParams.get("code") || "500";
  const message = searchParams.get("message") || "An unexpected error occurred during agent orchestration.";

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-slate-950 text-white">
      {/* Header Nav */}
      <header className="border-b border-white/5 py-4 px-6 md:px-12 bg-slate-950/40 backdrop-blur-md w-full">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-gradient-to-r from-teal-500 to-indigo-500 p-2 rounded-xl text-slate-950">
              <Code2 size={24} className="stroke-[2.5]" />
            </div>
            <div>
              <h1 className="font-bold text-lg md:text-xl tracking-tight bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
                Agentic GitHub Reviewer
              </h1>
              <p className="text-[10px] text-teal-400 uppercase tracking-widest font-semibold">Multi-Agent System</p>
            </div>
          </div>
        </div>
      </header>

      {/* Error Container */}
      <main className="flex-1 flex items-center justify-center p-4 min-h-[70vh] animate-slide-up">
        <div className="max-w-md w-full glass-panel p-8 rounded-3xl border border-rose-500/20 text-center relative overflow-hidden shadow-2xl bg-slate-900/40 backdrop-blur-md">
          <div className="absolute top-0 right-0 w-32 h-32 bg-rose-500/5 rounded-full blur-2xl -z-10 animate-pulse-slow"></div>
          
          <div className="inline-flex p-4 rounded-full bg-rose-500/10 text-rose-500 mb-6 border border-rose-500/20">
            <ShieldAlert size={48} className="stroke-[1.5]" />
          </div>

          <h2 className="text-3xl font-extrabold tracking-tight mb-2 text-rose-400">
            Error {code}
          </h2>
          
          <p className="text-slate-300 text-sm leading-relaxed mb-8">
            {message}
          </p>

          <div className="flex justify-center">
            <button
              onClick={() => router.push("/")}
              className="bg-gradient-to-r from-teal-500 to-indigo-600 hover:from-teal-400 hover:to-indigo-500 text-slate-950 font-bold px-6 py-3 rounded-xl transition duration-300 active:scale-95 flex items-center justify-center gap-2 text-sm cursor-pointer shadow-lg shadow-teal-500/10"
            >
              <RotateCcw size={16} />
              Try Again
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}

export default function ErrorPage() {
  return (
    <Suspense fallback={
      <div className="flex-1 flex items-center justify-center min-h-screen bg-slate-950 text-slate-400">
        Loading error details...
      </div>
    }>
      <ErrorContent />
    </Suspense>
  );
}
