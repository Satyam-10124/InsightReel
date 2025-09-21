"use client";
import { useState } from "react";
import { useSummarize } from "@/hooks/useSummarize";
import type { UserProfile } from "@/types/insightreel";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { DownloadReportButton } from "@/components/pdf/DownloadReportButton";

const userTypes = [
  { value: "student", label: "🎓 Student" },
  { value: "professional", label: "💼 Professional" },
  { value: "developer", label: "🔧 Developer" },
  { value: "entrepreneur", label: "🚀 Entrepreneur" },
  { value: "researcher", label: "📚 Researcher" },
  { value: "general", label: "🌟 General" },
] as const;

const lengths = [
  { value: "quick", label: "⚡ Quick" },
  { value: "standard", label: "📋 Standard" },
  { value: "detailed", label: "📖 Detailed" },
] as const;

export default function Home() {
  const [url, setUrl] = useState("");
  const [profile, setProfile] = useState<UserProfile>({ type: "developer", name: "Developer", icon: "🔧", length: "standard" });
  const [focus, setFocus] = useState("");
  const { mutate, data, isPending, error } = useSummarize();

  return (
    <main className="mx-auto max-w-6xl px-4">
      <section className="mt-10 md:mt-16">
        <div className="glass rounded-2xl p-6 md:p-10 relative overflow-hidden">
          <div className="absolute -top-24 -right-24 size-96 rounded-full bg-gradient-conic from-iris-600 via-cyan-400 to-emerald-400 opacity-20 animate-shimmer" />
          <h1 className="text-3xl md:text-5xl font-bold tracking-tight mb-3">Creative YouTube Summaries</h1>
          <p className="text-white/70 max-w-2xl">Personalized, AI-ready summaries, transcripts, and key concepts. Export beautiful PDF reports for your audience or team.</p>

          <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-2">
              <label className="label">YouTube URL</label>
              <input className="input" placeholder="https://www.youtube.com/watch?v=..." value={url} onChange={(e) => setUrl(e.target.value)} />
            </div>
            <div>
              <label className="label">Summary Length</label>
              <select
                className="input"
                value={profile.length}
                onChange={(e) => setProfile((p) => ({ ...p, length: e.target.value as any }))}
              >
                {lengths.map((l) => (
                  <option key={l.value} value={l.value}>{l.label}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="label">Profile</label>
              <select
                className="input"
                value={profile.type}
                onChange={(e) => {
                  const sel = userTypes.find((u) => u.value === e.target.value)!;
                  setProfile((p) => ({ ...p, type: sel.value as any, name: sel.label.split(" ")[1], icon: sel.label.split(" ")[0] }));
                }}
              >
                {userTypes.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </div>
            <div className="md:col-span-2">
              <label className="label">Focus (optional)</label>
              <input className="input" placeholder="e.g., focus on code architecture, main frameworks..." value={focus} onChange={(e) => setFocus(e.target.value)} />
            </div>
          </div>

          <div className="mt-6 flex items-center gap-3">
            <button
              className="btn"
              onClick={() => mutate({ url, profile: { ...profile, focus: focus || null }, sample_max_minutes: 20 })}
              disabled={!url || isPending}
            >
              {isPending ? "Summarizing..." : "Summarize"}
            </button>
            <span className="text-sm text-white/60">API: {process.env.NEXT_PUBLIC_INSIGHTREEL_API || "http://localhost:8000"}</span>
          </div>
        </div>
      </section>

      {error && (
        <div className="mt-6 glass rounded-xl p-4 border border-red-500/30 text-red-300">
          <div className="font-medium">Something went wrong</div>
          <div className="text-sm opacity-80">{String(error.message)}</div>
        </div>
      )}

      {data && data.success && (
        <section className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="md:col-span-2 glass rounded-2xl p-6">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-xl font-semibold">Summary</h2>
              <DownloadReportButton data={data} />
            </div>
            <article className="prose prose-invert max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{data.summary}</ReactMarkdown>
            </article>
          </div>

          <aside className="glass rounded-2xl p-6 space-y-3">
            <div className="badge">⏱ Duration: {data.duration}</div>
            <div className="badge">📺 Channel: {data.channel}</div>
            <div className="badge">🧩 Segments: {data.segments}</div>
            <div className="badge">✨ AI Enhanced: {data.ai_enhanced ? "Yes" : "No"}</div>
            <div className="mt-4">
              <div className="text-sm text-white/70 mb-1">Top Keywords</div>
              <div className="flex flex-wrap gap-2">
                {data.key_concepts.keywords.slice(0, 8).map(([k, c]) => (
                  <div key={k} className="badge">{k} ({c})</div>
                ))}
              </div>
            </div>
          </aside>
        </section>
      )}
    </main>
  );
}
