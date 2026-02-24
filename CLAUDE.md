# Quran Miracles - معجزات القرآن الكريم

## Project Overview
A modern web application showcasing the miracles of the Holy Quran, including numerical, scientific, and linguistic miracles. Built with Next.js 14 (App Router), TypeScript, and Tailwind CSS with full Arabic (RTL) support.

## Tech Stack
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS with RTL support
- **Font**: Amiri (Arabic), Inter (English)
- **Deployment**: Vercel

## Project Structure
```
quran-miracles/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── layout.tsx          # Root layout (RTL, fonts, metadata)
│   │   ├── page.tsx            # Home page
│   │   ├── globals.css         # Global styles
│   │   ├── numerical/          # Numerical miracles section
│   │   │   └── page.tsx
│   │   ├── scientific/         # Scientific miracles section
│   │   │   └── page.tsx
│   │   ├── linguistic/         # Linguistic miracles section
│   │   │   └── page.tsx
│   │   └── about/              # About page
│   │       └── page.tsx
│   ├── components/             # Reusable UI components
│   │   ├── layout/
│   │   │   ├── Header.tsx      # Navigation header
│   │   │   ├── Footer.tsx      # Site footer
│   │   │   └── Sidebar.tsx     # Sidebar navigation
│   │   ├── ui/
│   │   │   ├── MiracleCard.tsx  # Miracle display card
│   │   │   ├── QuranVerse.tsx   # Quran verse display
│   │   │   └── SectionTitle.tsx # Section title component
│   │   └── shared/
│   │       └── SearchBar.tsx    # Search functionality
│   ├── lib/                    # Utility functions and data
│   │   ├── constants.ts        # App constants
│   │   ├── utils.ts            # Helper functions
│   │   └── data/
│   │       ├── numerical.ts    # Numerical miracles data
│   │       ├── scientific.ts   # Scientific miracles data
│   │       └── linguistic.ts   # Linguistic miracles data
│   └── types/                  # TypeScript type definitions
│       └── index.ts            # Shared types and interfaces
├── public/
│   └── images/                 # Static images
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── next.config.ts
├── postcss.config.mjs
├── .env.local                  # Local environment variables
├── .gitignore
├── CLAUDE.md
└── README.md
```

## Development Commands
```bash
npm install          # Install dependencies
npm run dev          # Start development server (http://localhost:3000)
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint
```

## Key Design Decisions
- **RTL-first**: The entire UI is designed right-to-left for Arabic content
- **App Router**: Using Next.js App Router for server components and better performance
- **Static Data**: Miracle data is stored as TypeScript files for type safety
- **Responsive**: Mobile-first responsive design
- **Accessible**: WCAG 2.1 AA compliance target

## Content Categories
1. **المعجزات العددية** (Numerical Miracles) - Mathematical patterns in the Quran
2. **المعجزات العلمية** (Scientific Miracles) - Scientific facts mentioned in the Quran
3. **المعجزات اللغوية** (Linguistic Miracles) - Linguistic uniqueness of the Quran

## Coding Conventions
- Use TypeScript strict mode
- Components use PascalCase naming
- Utility functions use camelCase
- Arabic text content stored in data files
- All components must be responsive
- Use Tailwind CSS utilities, avoid custom CSS when possible
