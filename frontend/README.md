# Raksha AI — MVP Frontend

The web-based Open Source Intelligence (OSINT) analyst workbench for **Raksha AI**, inspired by Palantir's analytical UI design principles.

Built with **Next.js 14 (App Router)**, **TypeScript**, and **Tailwind CSS**.

---

## 1. Quick Start

### Prerequisites
- Node.js 18+ (tested with v22.13)
- `pnpm` (or `npm`)

### Setup & Run

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies
pnpm install

# 3. Start local development server (http://localhost:3000)
pnpm run dev

# 4. Production build and start
pnpm run build
pnpm run start
```

---

## 2. Environment Variables & Modes

Create or edit `.env.local` inside `/frontend`:

```env
# Backend FastAPI endpoint
NEXT_PUBLIC_API_URL=http://localhost:8000

# Set to true to run completely decoupled with offline synthetic OSINT mock data
NEXT_PUBLIC_USE_MOCK=false
```

### Switching Between Mock and Real API
- **Real Backend Mode (`NEXT_PUBLIC_USE_MOCK=false`)**:
  Connects to the FastAPI backend running at `NEXT_PUBLIC_API_URL`. Endpoints queried:
  - `GET /api/articles` (paginated stream with ring, classification, and date filters)
  - `GET /api/articles/{id}` (attributed article object view)
  - `GET /api/sources/health` and `GET /api/sources` (health telemetry)
  - `GET /api/stats` (platform aggregates)
  - Automatic fallback: If the backend is temporarily unreachable, the frontend gracefully falls back to mock data to maintain analyst workflow without crashing.
- **Mock Mode (`NEXT_PUBLIC_USE_MOCK=true`)**:
  Runs completely offline with realistic synthetic OSINT articles and feed statuses (`lib/api/mock-data.ts`). Strictly adheres to content guidelines: no real persons, no classified data, and no use of prohibited labels like "verified".

---

## 3. Project Structure

```
frontend/
├── app/
│   ├── layout.tsx              # Root layout with Source Serif 4 & IBM Plex Sans fonts + AppShell
│   ├── page.tsx                # Redirects "/" to "/articles"
│   ├── globals.css             # Tailwind layers & custom scrollbars
│   ├── articles/
│   │   ├── page.tsx            # /articles: Live feed, overview metrics, filter bar, cards, pagination
│   │   └── [id]/
│   │       └── page.tsx        # /articles/[id]: Full object view, metadata, attribution & raw snippet
│   └── sources/
│       └── page.tsx            # /sources: Source status directory, uptime cards, telemetry table
├── components/
│   ├── shell/
│   │   ├── AppShell.tsx        # Responsive layout wrapper with desktop sidebar and mobile drawer
│   │   ├── Sidebar.tsx         # Primary navigation + "Coming later" disabled items (Map, Graph, Profiles...)
│   │   └── TopBar.tsx          # System operational indicator, live IST clock, breadcrumb title
│   ├── shared/
│   │   ├── StatCard.tsx        # Summary metric card with accent colors
│   │   ├── RingMarker.tsx      # Rings 1 to 4 badge (India, Adversary, Regional, Global)
│   │   ├── SentimentLabel.tsx  # Negative / Neutral / Positive indicator with directional arrows
│   │   ├── ThreatLevel.tsx     # Low / Medium / High severity badge with 1-10 numerical rating
│   │   ├── EventTypeTag.tsx    # Canonical event category tag (Border, Military, Cyber, etc.)
│   │   ├── LanguageTag.tsx     # Language code badge + translation indicator
│   │   ├── StatusPill.tsx      # Feed health pill: Operational, Stale, Failing, Empty
│   │   ├── Pagination.tsx      # Accessible keyboard/URL-driven pagination
│   │   ├── EmptyState.tsx      # Zero-result fallback with reset action
│   │   ├── ErrorState.tsx      # Error banner with retry trigger
│   │   └── LoadingSkeleton.tsx # Wireframe skeletons for cards and tables
│   ├── articles/
│   │   ├── ArticleCard.tsx     # Feed card: title, summary excerpt, source, ring, badges, IST time, link
│   │   ├── ArticleFilters.tsx  # Filter bar: ring, event type, language, date range, search query
│   │   └── ArticleDetailView.tsx # Detailed analysis view with provenance panel
│   └── sources/
│       └── SourceTable.tsx     # Sortable table with expandable diagnostics drawer
├── lib/
│   ├── tokens.ts               # Exact palette tokens, ring colors, status colors, spacing
│   ├── utils.ts                # cn helper, formatISTDate(), relative time formatting
│   └── api/
│       ├── types.ts            # Domain models and API response types
│       ├── adapters.ts         # Single adapter transforming raw API payloads -> UI domain models
│       ├── client.ts           # Typed client with query param handling and mock fallback
│       └── mock-data.ts        # Synthetic realistic OSINT data for offline evaluation
├── design-reference/           # Reference screens downloaded from Stitch (not shipped in bundle)
│   ├── article-feed/
│   ├── article-detail/
│   └── source-status/
├── tailwind.config.ts          # Custom design tokens, colors, and font families
├── next.config.js
├── tsconfig.json
└── package.json
```

---

## 4. Key Design & Compliance Guardrails

1. **Attribution & Truthful Labeling**:
   - The word "verified" is never used. Articles reflect attributed public reports ("reported by", "source claim").
2. **Copyright-Safe Storage**:
   - Only headlines, short summary snippets ($\le 500$ chars), and direct links to canonical publishers are presented.
3. **IST Standardization**:
   - All timestamps and relative dates are computed and rendered in Indian Standard Time (`Asia/Kolkata`).
4. **Accessibility (WCAG AA)**:
   - Contrast ratio $\ge 4.5:1$ on all text and badge combinations.
   - Visible focus indicators (`focus-visible:ring-2 focus-visible:ring-primary-navy`).
   - Non-color reliant signals: every badge pairs visual color with icons and descriptive text labels.
5. **URL-Driven State**:
   - Filters, search terms (`q`), sorting order, and pagination are synchronized with browser URL query parameters for shareability.
