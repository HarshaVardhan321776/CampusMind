# CampusMind Next.js Frontend

This is the Next.js frontend for CampusMind, an AI-powered academic assistant.

## Stack
- **Framework:** Next.js 15 (App Router)
- **Styling:** Tailwind CSS
- **Typography:** Source Serif 4, Public Sans, IBM Plex Mono (Google Fonts)
- **Brand Colors:** Powder Blue #B9DDF5 | Pure White #FFFFFF | Racing Orange #FF5A1F

## Getting Started

```bash
# Install dependencies
npm install

# Run development server (requires backend at localhost:8000)
npm run dev
```

## Environment Variables

Create a `.env.local` file:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

For production (Vercel), set this in the Vercel dashboard under Project Settings > Environment Variables.

## Deployment

This app is deployed on Vercel. The backend FastAPI app must be deployed separately.

## Pages
- `/` — Redirects to dashboard or auth
- `/auth` — Login & Registration
- `/dashboard` — Academic workspace overview
- `/chat` — AI conversation interface
- `/documents` — Document upload and management
- `/settings` — Account settings
- `/terms` — Terms of Service
- `/privacy` — Privacy Policy

