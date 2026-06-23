"use client";

import React, { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";

const parseError = (errorMsg: string): { code: string; message: string } => {
  const msg = (errorMsg || "").toLowerCase();
  
  if (msg.includes("429") || msg.includes("resource_exhausted") || msg.includes("quota exceeded")) {
    return {
      code: "429",
      message: "Rate Limit Exceeded. The Gemini API is currently receiving too many requests. Please wait a minute before trying again."
    };
  }
  if (msg.includes("503") || msg.includes("unavailable") || msg.includes("high demand")) {
    return {
      code: "503",
      message: "Service Temporarily Unavailable. The AI models are currently experiencing high demand. Please try again shortly."
    };
  }
  if (msg.includes("404") || msg.includes("not found")) {
    return {
      code: "404",
      message: "Resource Not Found. The GitHub profile URL or backend API endpoint could not be found."
    };
  }
  if (msg.includes("unable to connect") || msg.includes("failed to connect")) {
    return {
      code: "CONNECTION_FAILED",
      message: "Backend Connection Refused. Please check if your FastAPI backend server is running on port 8000."
    };
  }
  
  // Default fallback
  return {
    code: "500",
    message: "An unexpected error occurred during agent orchestration. Please check the backend logs."
  };
};

import {
  Github,
  User,
  Users,
  Award,
  CheckCircle2,
  AlertTriangle,
  Briefcase,
  FileText,
  BookOpen,
  ExternalLink,
  Copy,
  Check,
  RotateCcw,
  Code2,
  ChevronRight,
  TrendingUp,
  Terminal,
  ShieldAlert,
  Loader2
} from "lucide-react";

// Types matching backend response schemas
interface RepositoryReview {
  name: string;
  quality_score: number;
  key_technologies: string[];
  review_comments: string;
  documentation_rating: string;
}

interface GitHubAnalysis {
  portfolio_score: number;
  strengths: string[];
  weaknesses: string[];
  repository_reviews: RepositoryReview[];
  primary_tech_stack: string[];
}

interface ProjectBullet {
  repo_name: string;
  bullets: string[];
}

interface ResumeImprovements {
  general_improvements: string[];
  ats_bullets: ProjectBullet[];
}

interface RoadmapStep {
  step_number: number;
  topic: string;
  skills_to_acquire: string[];
  recommended_resources: string[];
  estimated_time: string;
}

interface RecommendedProject {
  title: string;
  description: string;
  suggested_tech_stack: string[];
  difficulty: string;
}

interface RoleFit {
  role_name: string;
  match_percentage: number;
  reasoning: string;
}

interface CareerAnalysis {
  skills_gap: string[];
  roadmap: RoadmapStep[];
  recommended_projects: RecommendedProject[];
  role_fits: RoleFit[];
}

interface ReviewReport {
  username: string;
  name: string;
  bio: string;
  followers: number;
  avatar_url: string;
  github_url: string;
  github_analysis: GitHubAnalysis;
  resume_improvements: ResumeImprovements;
  career_analysis: CareerAnalysis;
  summary: string;
}

type StepKey = "scraping_github" | "analyzing_repos" | "writing_resume" | "planning_career" | "synthesizing";

interface StepConfig {
  label: string;
  description: string;
}

const STEPS: Record<StepKey, StepConfig> = {
  scraping_github: { label: "GitHub Scraper", description: "Fetching repos, READMEs, and commit history" },
  analyzing_repos: { label: "GitHub Analysis Agent", description: "Evaluating codebase quality and complexity" },
  writing_resume: { label: "Resume Agent", description: "Extracting achievements & writing STAR bullets" },
  planning_career: { label: "Career Agent", description: "Identifying skill gaps and mapping roadmaps" },
  synthesizing: { label: "Coordinator Agent", description: "Consolidating analysis and generating summary" },
};

const STEP_ORDER: StepKey[] = ["scraping_github", "analyzing_repos", "writing_resume", "planning_career", "synthesizing"];

const formatMarkdownText = (text: string) => {
  if (!text) return "";

  // Replace double asterisks **text** with bold strong tags
  const parts = text.split(/\*\*([^*]+)\*\*/g);
  return parts.map((part, index) => {
    if (index % 2 === 1) {
      return (
        <strong key={index} className="font-bold text-slate-100 bg-white/5 px-1.5 py-0.5 rounded border border-white/5">
          {part}
        </strong>
      );
    }
    return part;
  });
};

export default function Home() {
  const router = useRouter();
  const [githubUrl, setGithubUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState<StepKey | "completed" | null>(null);
  const [progressLog, setProgressLog] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<ReviewReport | null>(null);
  const [copiedBullet, setCopiedBullet] = useState<string | null>(null);
  const [copiedIndex, setCopiedIndex] = useState<string | null>(null);

  const eventSourceRef = useRef<EventSource | null>(null);
  const logEndRef = useRef<HTMLDivElement | null>(null);

  const handleError = (rawError: string) => {
    const { code, message } = parseError(rawError);
    setLoading(false);
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }
    router.push(`/error?code=${encodeURIComponent(code)}&message=${encodeURIComponent(message)}`);
  };

  // Auto-scroll progress logs to bottom
  useEffect(() => {
    if (logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [progressLog]);

  // Clean up SSE connection on unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!githubUrl.trim()) return;

    // Reset states
    setLoading(true);
    setError(null);
    setReport(null);
    setProgressLog([]);
    setCurrentStep("scraping_github");

    // Close any existing SSE connections
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const backendBaseUrl = (process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000").replace(/\/$/, "");
    const backendUrl = `${backendBaseUrl}/api/review/stream?github_url=${encodeURIComponent(githubUrl)}`;
    const eventSource = new EventSource(backendUrl);
    eventSourceRef.current = eventSource;

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.status === "failed") {
          handleError(data.message);
          return;
        }

        // Add to execution logs
        if (data.message) {
          setProgressLog((prev) => [...prev, data.message]);
        }

        // Update active stepper state
        if (data.status === "completed") {
          setCurrentStep("completed");
          setReport(data.result);
          setLoading(false);
          eventSource.close();
        } else {
          setCurrentStep(data.status as StepKey);
        }
      } catch (err) {
        console.error("Failed to parse SSE data", err);
        handleError("Invalid stream response from backend server.");
      }
    };

    eventSource.onerror = (err) => {
      console.error("SSE connection error", err);
      handleError("Unable to connect to the backend server. Make sure FastAPI is running on port 8000.");
    };
  };

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedBullet(text);
    setCopiedIndex(id);
    setTimeout(() => {
      setCopiedBullet(null);
      setCopiedIndex(null);
    }, 2000);
  };

  const handleReset = () => {
    setGithubUrl("");
    setReport(null);
    setCurrentStep(null);
    setProgressLog([]);
    setError(null);
  };

  // Helper to determine score color
  const getScoreColorClass = (score: number) => {
    if (score >= 80) return "text-emerald-400 border-emerald-500/30";
    if (score >= 60) return "text-amber-400 border-amber-500/30";
    return "text-rose-400 border-rose-500/30";
  };

  const getScoreBgClass = (score: number) => {
    if (score >= 80) return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
    if (score >= 60) return "bg-amber-500/10 text-amber-400 border-amber-500/20";
    return "bg-rose-500/10 text-rose-400 border-rose-500/20";
  };

  return (
    <div className="flex-1 flex flex-col min-h-screen">
      {/* Header Nav */}
      <header className="border-b border-white/5 py-4 px-6 md:px-12 bg-slate-950/40 backdrop-blur-md sticky top-0 z-50">
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
          <div className="flex items-center gap-3 text-slate-400 text-xs">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span>API Server Online</span>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 md:p-8 flex flex-col justify-center">

        {/* Landing View (Before submit) */}
        {!currentStep && !report && (
          <div className="max-w-2xl mx-auto text-center py-12 md:py-20 animate-slide-up">
            <h2 className="text-4xl md:text-5xl font-extrabold tracking-tight mb-4 leading-tight">
              Get Your GitHub Portfolio Reviewed by{" "}
              <span className="bg-gradient-to-r from-teal-400 via-emerald-400 to-indigo-500 bg-clip-text text-transparent">
                Collaborative AI Agents
              </span>
            </h2>
            <p className="text-slate-400 text-base md:text-lg mb-8 max-w-lg mx-auto">
              Our multi-agent system uses Gemini and Google ADK to fetch your code repositories, evaluate quality, write resume bullet points, and build learning roadmaps.
            </p>

            <form onSubmit={handleSubmit} className="w-full relative group">
              <div className="absolute -inset-0.5 bg-gradient-to-r from-teal-500 to-indigo-500 rounded-2xl blur-lg opacity-30 group-hover:opacity-50 transition duration-1000"></div>
              <div className="relative flex flex-col md:flex-row gap-3 bg-slate-900/90 p-3 rounded-2xl border border-white/10">
                <div className="flex-1 flex items-center gap-3 px-3">
                  <Github className="text-slate-400" size={22} />
                  <input
                    type="text"
                    required
                    placeholder="Enter your GitHub Profile URL (e.g. github.com/octocat)"
                    className="flex-1 bg-transparent border-0 text-white placeholder-slate-500 focus:ring-0 outline-none text-sm md:text-base"
                    value={githubUrl}
                    onChange={(e) => setGithubUrl(e.target.value)}
                  />
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="bg-gradient-to-r from-teal-500 to-indigo-600 hover:from-teal-400 hover:to-indigo-500 text-slate-950 font-bold px-6 py-3 rounded-xl transition-all duration-300 shadow-lg shadow-teal-500/10 active:scale-95 flex items-center justify-center gap-2 text-sm md:text-base whitespace-nowrap cursor-pointer"
                >
                  Analyze Portfolio
                  <ChevronRight size={18} />
                </button>
              </div>
            </form>

            <div className="mt-8 flex flex-wrap justify-center gap-4 text-xs text-slate-500">
              <span className="flex items-center gap-1"><CheckCircle2 size={14} className="text-teal-500" /> Repository reviews</span>
              <span className="flex items-center gap-1"><CheckCircle2 size={14} className="text-teal-500" /> ATS resume bullets</span>
              <span className="flex items-center gap-1"><CheckCircle2 size={14} className="text-teal-500" /> Skills roadmap</span>
              <span className="flex items-center gap-1"><CheckCircle2 size={14} className="text-teal-500" /> Career domain fits</span>
            </div>
          </div>
        )}

        {/* Loading / Progress Stepper View */}
        {currentStep && currentStep !== "completed" && (
          <div className="max-w-3xl mx-auto w-full glass-panel p-6 md:p-8 rounded-3xl animate-slide-up my-8">
            <h3 className="text-xl md:text-2xl font-bold mb-6 text-center">Multi-Agent Review Pipeline</h3>

            {/* Horizontal Stepper */}
            <div className="grid grid-cols-5 gap-2 mb-8 relative">
              <div className="absolute top-5 left-4 right-4 h-0.5 bg-slate-800 z-0"></div>
              {STEP_ORDER.map((step, idx) => {
                const isActive = currentStep === step;
                const isFinished = STEP_ORDER.indexOf(currentStep as StepKey) > idx;

                return (
                  <div key={step} className="flex flex-col items-center relative z-10 text-center">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center border font-bold text-xs transition-all duration-500 ${isActive
                        ? "bg-teal-500 border-teal-400 text-slate-950 shadow-lg shadow-teal-500/30 scale-110"
                        : isFinished
                          ? "bg-indigo-950 border-indigo-500 text-indigo-400"
                          : "bg-slate-950 border-slate-800 text-slate-600"
                      }`}>
                      {isFinished ? <CheckCircle2 size={16} /> : idx + 1}
                    </div>
                    <span className={`text-[10px] md:text-xs mt-2 font-medium hidden md:block ${isActive ? "text-teal-400 font-bold" : "text-slate-500"
                      }`}>
                      {STEPS[step].label}
                    </span>
                  </div>
                );
              })}
            </div>

            {/* Current status alert */}
            <div className="bg-slate-950/60 border border-white/5 rounded-2xl p-5 mb-6 flex items-start gap-4">
              <div className="bg-teal-500/10 p-2 rounded-xl text-teal-400 animate-spin">
                <Loader2 size={20} />
              </div>
              <div className="flex-1">
                <h4 className="text-sm font-semibold text-teal-400">Active Task</h4>
                <p className="text-slate-300 text-xs md:text-sm mt-1">{STEPS[currentStep as StepKey]?.description}...</p>
              </div>
            </div>

            {/* Console Log Output */}
            <div className="bg-black/80 border border-white/10 rounded-2xl p-4 font-mono text-xs text-slate-400 h-64 overflow-y-auto flex flex-col gap-2">
              <div className="text-slate-500 flex items-center gap-2 border-b border-white/5 pb-2 mb-2">
                <Terminal size={14} />
                <span>Agent Logs Console</span>
              </div>

              {progressLog.map((log, index) => (
                <div key={index} className="flex items-start gap-2 leading-relaxed animate-slide-up">
                  <span className="text-slate-600 select-none">&gt;</span>
                  <span>{log}</span>
                </div>
              ))}
              <div ref={logEndRef}></div>
            </div>


          </div>
        )}

        {/* Dashboard Report View (Completed) */}
        {report && (
          <div className="space-y-8 py-6 md:py-8 animate-slide-up">

            {/* Dashboard Header Profile Banner */}
            <div className="glass-panel p-6 rounded-3xl flex flex-col md:flex-row gap-6 items-center justify-between relative overflow-hidden">
              <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/5 rounded-full blur-3xl -z-10 animate-pulse-slow"></div>

              <div className="flex flex-col md:flex-row gap-6 items-center md:items-start text-center md:text-left">
                <img
                  src={report.avatar_url}
                  alt={report.name}
                  className="w-24 h-24 rounded-2xl border border-white/10 shadow-xl shrink-0"
                />
                <div className="space-y-2">
                  <div className="flex flex-wrap items-center justify-center md:justify-start gap-3">
                    <h2 className="text-2xl md:text-3xl font-extrabold">{report.name}</h2>
                    <a
                      href={report.github_url}
                      target="_blank"
                      rel="noreferrer"
                      className="bg-slate-800 hover:bg-slate-700 border border-white/5 text-slate-300 text-xs px-3 py-1 rounded-full flex items-center gap-1.5 transition font-semibold"
                    >
                      <Github size={14} />
                      @{report.username}
                      <ExternalLink size={10} />
                    </a>
                  </div>
                  {report.bio && <p className="text-slate-400 text-sm max-w-2xl">{report.bio}</p>}

                  <div className="flex flex-wrap items-center justify-center md:justify-start gap-4 text-xs text-slate-500 pt-2">
                    <span className="flex items-center gap-1.5"><Users size={14} /> {report.followers} Followers</span>
                    <span>•</span>
                    <span className="flex items-center gap-1.5"><Code2 size={14} /> {report.github_analysis.repository_reviews.length} Evaluated Repos</span>
                  </div>
                </div>
              </div>

              {/* Portfolio Score directly on Profile Card */}
              <div className="flex flex-col items-center justify-center border-t md:border-t-0 md:border-l border-white/5 pt-4 md:pt-0 md:pl-8 md:pr-4 shrink-0">
                <div className="relative w-24 h-24 flex items-center justify-center">
                  <svg className="w-24 h-24 transform -rotate-90">
                    <circle
                      cx="48"
                      cy="48"
                      r="40"
                      className="stroke-slate-800"
                      strokeWidth="6"
                      fill="transparent"
                    />
                    <circle
                      cx="48"
                      cy="48"
                      r="40"
                      className={`stroke-current ${report.github_analysis.portfolio_score >= 80
                          ? "text-emerald-500"
                          : report.github_analysis.portfolio_score >= 60
                            ? "text-amber-500"
                            : "text-rose-500"
                        }`}
                      strokeWidth="6"
                      fill="transparent"
                      strokeDasharray={251.2}
                      strokeDashoffset={251.2 - (251.2 * report.github_analysis.portfolio_score) / 100}
                      strokeLinecap="round"
                    />
                  </svg>
                  <div className="absolute flex flex-col items-center">
                    <span className="text-2xl font-extrabold tracking-tight">{report.github_analysis.portfolio_score}</span>
                    <span className="text-[8px] text-slate-500 font-semibold uppercase tracking-wider">Score</span>
                  </div>
                </div>
                <span className={`mt-2 px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${getScoreBgClass(report.github_analysis.portfolio_score)}`}>
                  {report.github_analysis.portfolio_score >= 80 ? "Premium Rank" : report.github_analysis.portfolio_score >= 60 ? "Solid Dev" : "Needs Work"}
                </span>
              </div>

              {/* Reset review button */}
              <button
                onClick={handleReset}
                className="bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs px-4 py-2.5 rounded-xl font-bold border border-white/5 transition flex items-center gap-1.5 shrink-0 cursor-pointer"
              >
                <RotateCcw size={14} />
                New Analysis
              </button>
            </div>

            {/* Overview / Key Metrics Row */}
            <div className="glass-panel p-6 rounded-3xl space-y-4">
              <h3 className="text-xs font-bold uppercase tracking-widest text-slate-500 flex items-center gap-1.5 border-b border-white/5 pb-2">
                <BookOpen size={14} className="text-teal-400" />
                Agentic Executive Summary
              </h3>

              {/* Point-wise Executive Summary */}
              <div className="space-y-2.5">
                {report.summary.split("\n").filter(line => line.trim()).map((line, i) => {
                  const cleanLine = line.replace(/^\s*[-*•]\s*/, "").trim();
                  if (!cleanLine) return null;
                  return (
                    <div key={i} className="flex items-start gap-2.5 text-slate-300 text-sm leading-relaxed">
                      <span className="text-teal-400 mt-1.5 select-none font-bold text-xs">&bull;</span>
                      <span>{formatMarkdownText(cleanLine)}</span>
                    </div>
                  );
                })}
              </div>

              {/* Primary Tech Stack */}
              <div className="space-y-2 pt-2 border-t border-white/5">
                <h4 className="text-xs font-semibold text-slate-400">Core Technologies Detected</h4>
                <div className="flex flex-wrap gap-2">
                  {report.github_analysis.primary_tech_stack.map((tech) => (
                    <span key={tech} className="bg-indigo-950/40 border border-indigo-500/20 text-indigo-300 text-xs px-2.5 py-1 rounded-lg font-medium">
                      {tech}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* Strengths & Weaknesses Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

              {/* Strengths Card */}
              <div className="glass-panel p-6 rounded-3xl border-emerald-500/10">
                <h3 className="text-sm font-bold text-emerald-400 flex items-center gap-2 border-b border-emerald-500/5 pb-3 mb-4">
                  <CheckCircle2 size={18} className="text-emerald-500" />
                  Key Portfolio Strengths
                </h3>
                <ul className="space-y-3">
                  {report.github_analysis.strengths.map((str, i) => (
                    <li key={i} className="flex gap-3 text-slate-300 text-sm leading-relaxed">
                      <span className="text-emerald-500 font-bold select-none mt-0.5">•</span>
                      <span>{formatMarkdownText(str)}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Weaknesses Card */}
              <div className="glass-panel p-6 rounded-3xl border-rose-500/10">
                <h3 className="text-sm font-bold text-rose-400 flex items-center gap-2 border-b border-rose-500/5 pb-3 mb-4">
                  <AlertTriangle size={18} className="text-rose-500" />
                  Identified Weaknesses & Gaps
                </h3>
                <ul className="space-y-3">
                  {report.github_analysis.weaknesses.map((weak, i) => (
                    <li key={i} className="flex gap-3 text-slate-300 text-sm leading-relaxed">
                      <span className="text-rose-500 font-bold select-none mt-0.5">•</span>
                      <span>{formatMarkdownText(weak)}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Repository-by-Repository Breakdown */}
            <div className="space-y-4">
              <h3 className="text-lg font-bold tracking-tight">Repository-by-Repository Evaluation</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {report.github_analysis.repository_reviews.map((repo) => (
                  <div key={repo.name} className="glass-panel p-5 rounded-2xl space-y-4 flex flex-col justify-between hover:border-slate-700/80 transition duration-300">
                    <div className="space-y-3">
                      <div className="flex justify-between items-start gap-4">
                        <h4 className="font-bold text-base text-slate-100 flex items-center gap-1.5 break-all">
                          <Code2 size={16} className="text-slate-400 shrink-0" />
                          {repo.name}
                        </h4>
                        <span className={`text-xs px-2 py-0.5 rounded-full font-bold border ${getScoreBgClass(repo.quality_score)}`}>
                          Score: {repo.quality_score}
                        </span>
                      </div>

                      <p className="text-slate-400 text-xs md:text-sm leading-relaxed">
                        {formatMarkdownText(repo.review_comments)}
                      </p>
                    </div>

                    <div className="pt-2 border-t border-white/5 flex flex-wrap items-center justify-between gap-3">
                      <div className="flex flex-wrap gap-1.5">
                        {repo.key_technologies.map((tech) => (
                          <span key={tech} className="bg-slate-900 border border-white/5 text-slate-400 text-[10px] px-2 py-0.5 rounded">
                            {tech}
                          </span>
                        ))}
                      </div>

                      <div className="flex items-center gap-2">
                        <span className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider">Docs:</span>
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${repo.documentation_rating === "Excellent" || repo.documentation_rating === "Good"
                            ? "bg-emerald-500/10 text-emerald-400"
                            : "bg-amber-500/10 text-amber-400"
                          }`}>
                          {repo.documentation_rating}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Resume Bullet Suggestions Section */}
            <div className="glass-panel p-6 rounded-3xl space-y-6">
              <div className="border-b border-white/5 pb-4">
                <h3 className="text-lg font-bold flex items-center gap-2">
                  <FileText className="text-teal-400" size={20} />
                  Resume Improvements & ATS STAR Bullets
                </h3>
                <p className="text-slate-400 text-xs mt-1">Suggested general formatting enhancements and pre-written resume bullet points for your projects.</p>
              </div>

              {/* General Resume Tips */}
              <div className="space-y-3">
                <h4 className="text-sm font-semibold text-slate-300">Actionable Resume Refinements</h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {report.resume_improvements.general_improvements.map((tip, i) => (
                    <div key={i} className="bg-slate-950/40 border border-white/5 p-4 rounded-xl text-slate-300 text-xs md:text-sm leading-relaxed">
                      {formatMarkdownText(tip)}
                    </div>
                  ))}
                </div>
              </div>

              {/* Project Bullet Points */}
              <div className="space-y-4">
                <h4 className="text-sm font-semibold text-slate-300">STAR-Format Project Bullets</h4>
                <div className="space-y-6">
                  {report.resume_improvements.ats_bullets.map((proj) => (
                    <div key={proj.repo_name} className="space-y-3 bg-slate-950/30 p-5 rounded-2xl border border-white/5">
                      <h5 className="text-xs font-bold text-teal-400 uppercase tracking-widest flex items-center gap-1.5">
                        <Terminal size={12} />
                        {proj.repo_name}
                      </h5>
                      <div className="space-y-2">
                        {proj.bullets.map((bullet, idx) => {
                          const id = `${proj.repo_name}-${idx}`;
                          const isCopied = copiedBullet === bullet && copiedIndex === id;

                          return (
                            <div key={idx} className="group relative flex gap-3 text-slate-300 text-xs md:text-sm leading-relaxed p-2 hover:bg-slate-900/60 rounded-xl transition duration-150 pr-12">
                              <span className="text-indigo-400 font-bold select-none">&bull;</span>
                              <span>{formatMarkdownText(bullet)}</span>

                              <button
                                onClick={() => handleCopy(bullet, id)}
                                className="absolute right-3 top-2 opacity-0 group-hover:opacity-100 bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white p-1.5 rounded-lg border border-white/5 transition duration-150 cursor-pointer"
                                title="Copy to clipboard"
                              >
                                {isCopied ? <Check size={14} className="text-emerald-400" /> : <Copy size={14} />}
                              </button>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Career Advisor: Roadmap and Learning Gaps */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">

              {/* Timeline Roadmap */}
              <div className="glass-panel p-6 rounded-3xl md:col-span-2 space-y-6">
                <div className="border-b border-white/5 pb-3">
                  <h3 className="text-lg font-bold flex items-center gap-2">
                    <BookOpen className="text-indigo-400" size={20} />
                    Personalized Learning Roadmap
                  </h3>
                  <p className="text-slate-400 text-xs mt-1">Step-by-step pipeline designed by agents to bridge your engineering skill gaps.</p>
                </div>

                <div className="relative pl-6 space-y-6 border-l border-teal-500/30">
                  {report.career_analysis.roadmap.map((step) => (
                    <div key={step.step_number} className="relative space-y-2">
                      {/* Circle Dot indicator */}
                      <span className="absolute -left-[31px] top-1.5 w-4.5 h-4.5 rounded-full bg-slate-950 border-2 border-teal-500 flex items-center justify-center text-[8px] font-bold text-teal-400">
                        {step.step_number}
                      </span>

                      <div className="bg-slate-950/40 border border-white/5 p-4 rounded-2xl">
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <h4 className="font-bold text-sm text-slate-100">{step.topic}</h4>
                          <span className="bg-teal-500/10 border border-teal-500/20 text-teal-400 text-[10px] px-2 py-0.5 rounded-full font-bold">
                            {step.estimated_time}
                          </span>
                        </div>

                        <div className="mt-2 space-y-2">
                          <div className="flex flex-wrap gap-1">
                            {step.skills_to_acquire.map((skill) => (
                              <span key={skill} className="bg-slate-900 text-slate-400 text-[10px] px-2 py-0.5 rounded">
                                {skill}
                              </span>
                            ))}
                          </div>

                          <div className="text-[10px] text-slate-500 flex items-start gap-1 leading-relaxed">
                            <span className="font-semibold text-slate-400 shrink-0">Resources:</span>
                            <span>{step.recommended_resources.join(", ")}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Skill Gap & recommended projects */}
              <div className="space-y-6">

                {/* Skill Gaps Card */}
                <div className="glass-panel p-6 rounded-3xl space-y-4">
                  <h3 className="text-sm font-bold text-indigo-400 flex items-center gap-1.5 border-b border-indigo-500/5 pb-2">
                    <ShieldAlert size={16} />
                    Skill Gaps Identified
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {report.career_analysis.skills_gap.map((gap) => (
                      <span key={gap} className="bg-slate-950 border border-white/5 text-rose-300 text-xs px-2.5 py-1 rounded-lg font-medium">
                        {gap}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Recommended Projects Card */}
                <div className="glass-panel p-6 rounded-3xl space-y-4">
                  <h3 className="text-sm font-bold text-teal-400 flex items-center gap-1.5 border-b border-teal-500/5 pb-2">
                    <TrendingUp size={16} />
                    Recommended Projects
                  </h3>
                  <div className="space-y-4">
                    {report.career_analysis.recommended_projects.map((proj) => (
                      <div key={proj.title} className="bg-slate-950/40 border border-white/5 p-4 rounded-xl space-y-2">
                        <div className="flex justify-between items-start gap-2">
                          <h4 className="font-bold text-xs text-slate-200">{proj.title}</h4>
                          <span className={`text-[9px] font-bold px-1.5 py-0.2 rounded border ${proj.difficulty === "Advanced"
                              ? "bg-rose-500/10 text-rose-400 border-rose-500/20"
                              : proj.difficulty === "Intermediate"
                                ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                                : "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                            }`}>
                            {proj.difficulty}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-400 leading-relaxed">{formatMarkdownText(proj.description)}</p>
                        <div className="flex flex-wrap gap-1 pt-1">
                          {proj.suggested_tech_stack.map((t) => (
                            <span key={t} className="bg-slate-900 text-slate-500 text-[8px] px-1.5 py-0.5 rounded">
                              {t}
                            </span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Career Domain Role Fit Breakdown */}
            <div className="glass-panel p-6 rounded-3xl space-y-6">
              <div className="border-b border-white/5 pb-3">
                <h3 className="text-lg font-bold flex items-center gap-2">
                  <Briefcase className="text-teal-400" size={20} />
                  Career Role Fit Analysis
                </h3>
                <p className="text-slate-400 text-xs mt-1">Evaluation of your profile matching developer job markets.</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {report.career_analysis.role_fits.map((fit) => (
                  <div key={fit.role_name} className="bg-slate-950/40 border border-white/5 p-4 rounded-2xl space-y-3">
                    <div className="flex items-center justify-between gap-4">
                      <h4 className="font-bold text-sm text-slate-200">{fit.role_name}</h4>
                      <span className={`text-xs font-extrabold ${fit.match_percentage >= 85 ? "text-emerald-400" : fit.match_percentage >= 60 ? "text-amber-400" : "text-rose-400"
                        }`}>
                        {fit.match_percentage}% Match
                      </span>
                    </div>

                    {/* Progress bar */}
                    <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-1000 ${fit.match_percentage >= 85 ? "bg-emerald-500" : fit.match_percentage >= 60 ? "bg-amber-500" : "bg-rose-500"
                          }`}
                        style={{ width: `${fit.match_percentage}%` }}
                      ></div>
                    </div>

                    <p className="text-xs text-slate-400 leading-relaxed">{formatMarkdownText(fit.reasoning)}</p>
                  </div>
                ))}
              </div>
            </div>

          </div>
        )}

      </main>

      {/* Footer */}
      <footer className="border-t border-white/5 py-6 px-6 text-center text-xs text-slate-600 bg-slate-950/10">
        <p>&copy; {new Date().getFullYear()} Antigravity Agentic GitHub Portfolio Reviewer. Powered by Google ADK & Gemini.</p>
      </footer>
    </div>
  );
}
