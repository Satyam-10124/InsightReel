# InsightReel — Creative Next.js Frontend

A creative, glassmorphic Next.js frontend for InsightReel with Tailwind CSS, React Query, and PDF export.

## Quick Start

1. Install deps

```bash
npm i
# or
pnpm i
```

2. Set API base

Create `.env.local` with:

```
NEXT_PUBLIC_INSIGHTREEL_API=https://insight-reel-production.up.railway.app
```

3. Run dev

```bash
npm run dev
```

Open http://localhost:3001

## Tech

- Next.js App Router (TS)
- Tailwind CSS, creative gradients + glass UI
- TanStack Query for API calls
- @react-pdf/renderer for beautiful PDF export

## Structure

- `app/` — pages, layout, providers
- `components/` — UI and PDF components
- `hooks/` — React Query hooks
- `lib/` — API client and utilities
- `types/` — shared TypeScript types (match backend contracts)

## Deploy

- Any Next-compatible host (Vercel, Netlify). Ensure `NEXT_PUBLIC_INSIGHTREEL_API` points to your FastAPI instance.
