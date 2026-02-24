# نماذج العربية / RAG / Embeddings

> المرجع: CLAUDE.md → docs/04_arabic_nlp_rag.md

---

## النماذج المستخدمة

| النموذج | الاستخدام |
|---------|-----------|
| CAMeLBERT-CA | العربية الكلاسيكية (NYU Abu Dhabi) |
| AraBERT v0.2 Large | التحليل الدلالي |
| CAMeL Tools v1.2.0 | التحليل الصرفي |
| text-embedding-3-large | التضمينات (OpenAI — 1536 بُعد) |
| claude-sonnet-4-5 | الاستدلال (Anthropic) |

## البحث الهجين

1. BM25 للمطابقة اللفظية
2. Semantic similarity عبر pgvector
3. Arabic cross-encoder reranking

---

*docs/04_arabic_nlp_rag.md — الإصدار 3.0*
