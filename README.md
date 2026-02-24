# معجزات القرآن الكريم — AI Discovery Platform

منصة استكشاف الإعجاز القرآني بالذكاء الاصطناعي

## المجموعة التقنية

- **Frontend:** Next.js 15 + TypeScript + Tailwind CSS + Shadcn/UI
- **Backend:** Python 3.12 + FastAPI + LangGraph 0.2
- **Database:** PostgreSQL 16 (pgvector) + Neo4j 5 + Redis 7
- **AI:** Claude (Anthropic) + CAMeLBERT + AraBERT + text-embedding-3-large
- **Deployment:** Vercel + Railway + GitHub Actions

## البدء السريع

```bash
# 1. نسخ ملف المتغيرات البيئية
cp .env.example .env

# 2. تشغيل الخدمات عبر Docker
docker compose up -d

# 3. إعداد Frontend
cd frontend && npm install && npm run dev

# 4. إعداد Backend
cd backend && pip install -r requirements.txt
uvicorn main:app --reload
```

## هيكل المشروع

```
quran-miracles/
├── frontend/          ← Next.js 15 (App Router)
├── backend/           ← FastAPI + LangGraph
│   ├── api/           ← REST API routes
│   ├── discovery_engine/
│   │   ├── core/      ← LangGraph workflow
│   │   ├── agents/    ← 6 specialized AI agents
│   │   ├── mcts/      ← Monte Carlo Tree Search
│   │   ├── prediction/← Predictive engine
│   │   └── autonomous/← 24/7 background worker
│   ├── arabic_nlp/    ← Arabic NLP processing
│   └── database/      ← SQLAlchemy models
├── data/              ← Quranic text + tafseers + science
├── docs/              ← Technical documentation
└── .github/workflows/ ← CI/CD pipelines
```

## الوثائق

راجع مجلد `docs/` للوثائق التقنية المفصلة، و `CLAUDE.md` للقواعد الذهبية.
