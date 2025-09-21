import type { Metadata } from "next";
import "./globals.css";
import { Inter } from "next/font/google";
import Providers from "./providers";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "InsightReel — Summarize YouTube Creatively",
  description: "Creative, personalized summaries and transcripts powered by InsightReel",
  metadataBase: new URL("https://example.com"),
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="h-full">
      <body className={`${inter.className} h-full`}>        
        <div className="fixed inset-0 -z-10">
          <div className="gradient-orb gradient-orb--iris -top-24 -left-24" />
          <div className="gradient-orb gradient-orb--cyan bottom-0 right-0" />
        </div>
        <Providers>
          <div className="min-h-full">
            <header className="sticky top-0 z-20 backdrop-blur bg-black/30 border-b border-white/10">
              <div className="mx-auto max-w-6xl px-4 py-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-lg bg-white/10 grid place-items-center border border-white/10">🎬</div>
                  <div className="font-semibold tracking-tight">InsightReel</div>
                </div>
                <div className="hidden md:flex items-center gap-2 text-sm text-white/60">
                  <span className="badge">Creative Mode</span>
                  <span className="badge">AI Ready</span>
                </div>
              </div>
            </header>
            {children}
            <footer className="mt-12 py-10 text-center text-xs text-white/50">
              Built with ❤️ for creators • {new Date().getFullYear()}
            </footer>
          </div>
        </Providers>
      </body>
    </html>
  );
}
