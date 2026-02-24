# خطة التنفيذ — Implementation Plan

> المرجع: CLAUDE.md → docs/09_implementation_plan.md

---

## المراحل

### المرحلة 1: الهيكل الأساسي
- إعداد المشروع وهيكل الملفات
- قاعدة البيانات (Schema + migrations)
- استيراد النص القرآني من tanzil.net

### المرحلة 2: محرك LangGraph
- بناء الوكلاء الستة
- تدفق LangGraph (8 عقد + شرط)
- SSE Streaming

### المرحلة 3: معالجة اللغة العربية
- CAMeL Tools integration
- Embeddings pipeline
- البحث الهجين (BM25 + semantic)

### المرحلة 4: محرك التنبؤ
- AbductiveReasoningEngine
- StatisticalSafeguards
- ResearchNavigator

### المرحلة 5: الواجهة الأمامية
- تصفح القرآن + التفاسير
- محرك الاستكشاف التفاعلي
- لوحة التحكم + التقارير

### المرحلة 6: المحرك المستقل
- جدولة المهام (APScheduler)
- مراقبة الأبحاث الجديدة
- التقارير الأسبوعية

---

*docs/09_implementation_plan.md — الإصدار 3.0*
