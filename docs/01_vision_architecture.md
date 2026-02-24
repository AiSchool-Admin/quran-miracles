# معمارية النظام — Vision & Architecture

> المرجع: CLAUDE.md → docs/01_vision_architecture.md

---

## الرؤية

بناء أول منصة في العالم تجمع:
- الاستكشاف المستمر الآلي
- التنبؤ بالمعجزات المحتملة
- توجيه الباحثين

بالذكاء الاصطناعي — 24/7 — بدون تدخل بشري في الاستكشاف.

---

## المجموعة التقنية

| الطبقة | التقنية |
|--------|---------|
| Frontend | Next.js 15 (App Router + TypeScript strict) |
| Styling | Tailwind CSS + Shadcn/UI |
| AI Client | Vercel AI SDK (@ai-sdk/anthropic) |
| Backend | FastAPI 0.111 + Python 3.12 |
| AI Engine | LangGraph 0.2 + langchain-anthropic |
| Database | PostgreSQL 16 (Supabase) + pgvector |
| Graph | Neo4j 5.x |
| Cache | Redis 7 (Upstash) |
| Deployment | Vercel + Railway |

---

*docs/01_vision_architecture.md — الإصدار 3.0*
