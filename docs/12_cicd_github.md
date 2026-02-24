# 🚀 القسم الثاني عشر: إعداد CI/CD — GitHub Actions + Vercel + Railway
# المرجع: CLAUDE.md → docs/12_cicd_github.md
# ─────────────────────────────────────────────────────────────────────
#
# ✅ إجابة السؤال: هل ينفع تشتغل من المرحلة 1 بأسلوب المرحلة 3؟
#
# نعم — بشرط واحد:
# Claude Code CLI (ليس Web) هو الأداة للتطوير المحلي.
# Claude Code Web (عبر GitHub) للمراجعة والـ PRs فقط.
#
# الـ Workflow الصحيح:
#   [أنت محلياً بـ Claude Code CLI]
#       ↓ تكتب كود
#   [Git Push → GitHub]
#       ↓ GitHub Actions يشغّل الاختبارات
#   [Claude Code Web يراجع الـ PR ويقترح تحسينات]
#       ↓ أنت توافق
#   [Auto Deploy: Vercel (Frontend) + Railway (Backend)]
#
# ─────────────────────────────────────────────────────────────────────

---

## إعداد المستودع على GitHub

```bash
# 1. إنشاء المستودع
gh repo create quran-miracles --private --description "معجزات القرآن — AI Discovery Platform"

# 2. إعداد Secrets في GitHub
gh secret set ANTHROPIC_API_KEY      --body "sk-ant-..."
gh secret set SUPABASE_URL           --body "https://..."
gh secret set SUPABASE_SERVICE_KEY   --body "..."
gh secret set RAILWAY_TOKEN          --body "..."
gh secret set VERCEL_TOKEN           --body "..."
gh secret set VERCEL_ORG_ID          --body "..."
gh secret set VERCEL_PROJECT_ID      --body "..."
gh secret set NEO4J_URI              --body "bolt://..."
gh secret set REDIS_URL              --body "redis://..."

# 3. إعداد Branch Protection
gh api repos/:owner/quran-miracles/branches/main/protection \
  --method PUT \
  --field required_pull_request_reviews[required_approving_review_count]=1 \
  --field required_status_checks[strict]=true
```

---

## .github/workflows/ci.yml — الاختبارات التلقائية

```yaml
name: CI — اختبارات التكامل

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  # ═══════════════════════════════
  test-backend:
    name: 🐍 اختبار Backend Python
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: pgvector/pgvector:pg16
        env:
          POSTGRES_DB:       quran_miracles_test
          POSTGRES_USER:     test_user
          POSTGRES_PASSWORD: test_pass
        ports: ["5432:5432"]
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
      
      redis:
        image: redis:7-alpine
        ports: ["6379:6379"]
    
    steps:
      - uses: actions/checkout@v4
      
      - name: إعداد Python 3.12
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
      
      - name: تثبيت المكتبات
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-asyncio httpx
      
      - name: تطبيق Schema قاعدة البيانات
        run: |
          cd backend
          python scripts/apply_schema.py
        env:
          DATABASE_URL: postgresql://test_user:test_pass@localhost:5432/quran_miracles_test
      
      - name: تشغيل الاختبارات
        run: |
          cd backend
          pytest tests/ -v --tb=short \
            --ignore=tests/integration/test_claude_api.py
        env:
          DATABASE_URL:   postgresql://test_user:test_pass@localhost:5432/quran_miracles_test
          REDIS_URL:      redis://localhost:6379
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      
      - name: فحص جودة الكود
        run: |
          cd backend
          pip install ruff mypy
          ruff check .
          mypy . --ignore-missing-imports

  # ═══════════════════════════════
  test-frontend:
    name: ⚛️ اختبار Frontend Next.js
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: إعداد Node.js 20
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: npm
          cache-dependency-path: frontend/package-lock.json
      
      - name: تثبيت المكتبات
        run: |
          cd frontend
          npm ci
      
      - name: فحص TypeScript
        run: |
          cd frontend
          npx tsc --noEmit
      
      - name: فحص ESLint
        run: |
          cd frontend
          npm run lint
      
      - name: بناء المشروع
        run: |
          cd frontend
          npm run build
        env:
          NEXT_PUBLIC_API_URL: http://localhost:8000

  # ═══════════════════════════════
  validate-quran-data:
    name: 📖 التحقق من سلامة البيانات القرآنية
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: إعداد Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      
      - name: التحقق من checksum النص القرآني
        run: |
          python scripts/validate_quran_integrity.py
          # يتحقق أن النص القرآني لم يُعدَّل — checksum ثابت
      
      - name: التحقق من اكتمال التفاسير
        run: |
          python scripts/validate_tafseers.py
```

---

## .github/workflows/deploy-frontend.yml — نشر Vercel

```yaml
name: Deploy Frontend → Vercel

on:
  push:
    branches: [main]
    paths:
      - "frontend/**"
      - ".github/workflows/deploy-frontend.yml"

jobs:
  deploy:
    name: 🚀 نشر على Vercel
    runs-on: ubuntu-latest
    needs: [test-frontend]    # لا نشر بدون نجاح الاختبارات
    
    steps:
      - uses: actions/checkout@v4
      
      - name: نشر على Vercel
        uses: amondnet/vercel-action@v25
        with:
          vercel-token:      ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id:     ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          working-directory: ./frontend
          vercel-args: "--prod"
      
      - name: إشعار النجاح
        run: |
          echo "✅ Frontend deployed to Vercel"
          echo "🌐 URL: https://quran-miracles.vercel.app"
```

---

## .github/workflows/deploy-backend.yml — نشر Railway

```yaml
name: Deploy Backend → Railway

on:
  push:
    branches: [main]
    paths:
      - "backend/**"
      - ".github/workflows/deploy-backend.yml"

jobs:
  deploy:
    name: 🐍 نشر على Railway
    runs-on: ubuntu-latest
    needs: [test-backend]
    
    steps:
      - uses: actions/checkout@v4
      
      - name: تثبيت Railway CLI
        run: npm install -g @railway/cli
      
      - name: نشر على Railway
        run: |
          cd backend
          railway up --service quran-miracles-api
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
      
      - name: التحقق من صحة الـ API بعد النشر
        run: |
          sleep 15   # انتظر حتى يبدأ الخادم
          curl -f https://api.quran-miracles.railway.app/health || exit 1
          echo "✅ Backend API healthy"
```

---

## .github/workflows/claude-review.yml — مراجعة Claude Code Web للـ PRs

```yaml
name: Claude Code Review — مراجعة الكود بالذكاء الاصطناعي

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  claude-review:
    name: 🤖 مراجعة Claude للـ PR
    runs-on: ubuntu-latest
    
    permissions:
      contents:      read
      pull-requests: write    # ضروري للتعليق على الـ PR
    
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: استخراج التغييرات
        id: diff
        run: |
          git diff origin/main...HEAD -- \
            '*.py' '*.ts' '*.tsx' '*.sql' \
            > /tmp/pr_diff.txt
          echo "diff_lines=$(wc -l < /tmp/pr_diff.txt)" >> $GITHUB_OUTPUT
      
      - name: مراجعة Claude للكود
        if: steps.diff.outputs.diff_lines > 0
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          PR_NUMBER: ${{ github.event.pull_request.number }}
          REPO: ${{ github.repository }}
        run: |
          python scripts/claude_pr_review.py \
            --diff-file /tmp/pr_diff.txt \
            --pr-number $PR_NUMBER \
            --repo $REPO \
            --guidelines-file CLAUDE.md
```

```python
# scripts/claude_pr_review.py
# مراجعة Claude Code Web للـ PRs

import anthropic
import argparse
import subprocess
import json

def review_pr(diff_file: str, pr_number: int, repo: str, guidelines_file: str):
    
    with open(diff_file, 'r') as f:
        diff = f.read()
    
    with open(guidelines_file, 'r') as f:
        guidelines = f.read()
    
    client = anthropic.Anthropic()
    
    review = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=3000,
        system=f"""
        أنت مراجع كود متخصص في مشروع "معجزات القرآن الكريم".
        
        قواعد المشروع المُلزِمة:
        {guidelines[:3000]}
        
        مهمتك: مراجعة التغييرات في الـ PR والتحقق من:
        1. الالتزام بقواعد المشروع (CLAUDE.md)
        2. جودة الكود وأفضل الممارسات
        3. الأمانة العلمية في أي ادعاءات قرآنية
        4. صحة نظام المستويات (tier_0 → tier_4)
        5. وجود dir=rtl في كل مكوّن frontend جديد
        6. عدم تعديل النص القرآني
        
        اكتب ملاحظاتك بالعربية مع أمثلة محددة من الكود.
        كن بنّاءً ومحدداً — لا تُعمّم.
        """,
        messages=[{
            "role": "user",
            "content": f"راجع هذه التغييرات:\n\n```diff\n{diff[:8000]}\n```"
        }]
    )
    
    review_text = review.content[0].text
    
    # نشر التعليق على الـ PR
    comment = f"## 🤖 مراجعة Claude Code\n\n{review_text}"
    
    subprocess.run([
        "gh", "pr", "comment", str(pr_number),
        "--repo", repo,
        "--body", comment
    ], check=True)
    
    print(f"✅ تم نشر مراجعة Claude على PR #{pr_number}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--diff-file")
    parser.add_argument("--pr-number", type=int)
    parser.add_argument("--repo")
    parser.add_argument("--guidelines-file")
    args = parser.parse_args()
    
    review_pr(args.diff_file, args.pr_number, args.repo, args.guidelines_file)
```

---

## إجابة السؤال — هل ينفع البدء مباشرة بأسلوب المرحلة 3؟

```
✅ نعم — بشرط فهم الفرق بين الأدوات:

┌─────────────────────────┬────────────────────────────────────────────┐
│ الأداة                  │ متى تستخدمها؟                              │
├─────────────────────────┼────────────────────────────────────────────┤
│ Claude Code CLI (محلي)  │ كتابة الكود + تشغيله + اختباره محلياً     │
│                         │ → الأداة الرئيسية للتطوير اليومي           │
├─────────────────────────┼────────────────────────────────────────────┤
│ Claude Code Web (GitHub)│ مراجعة الـ PRs + اقتراح تحسينات           │
│                         │ → لا تكتب كوداً — فقط يراجع ويقترح        │
├─────────────────────────┼────────────────────────────────────────────┤
│ GitHub Actions          │ CI/CD — اختبارات تلقائية + نشر            │
│                         │ → يعمل عند كل Push/PR بدون تدخل            │
├─────────────────────────┼────────────────────────────────────────────┤
│ Vercel                  │ نشر Frontend تلقائياً من main branch       │
├─────────────────────────┼────────────────────────────────────────────┤
│ Railway                 │ نشر Backend Python تلقائياً                │
└─────────────────────────┴────────────────────────────────────────────┘

الـ Workflow اليومي:
  1. أنت تشغّل: claude "نفّذ هذه المهمة — راجع docs/02_langgraph_agents.md"
  2. Claude Code CLI يكتب الكود ويختبره محلياً
  3. git push → GitHub Actions تشغّل الاختبارات
  4. تفتح PR → Claude Code Web يراجع ويعلّق
  5. أنت توافق → Vercel + Railway ينشران تلقائياً

المطلوب للبدء:
  ✅ تثبيت Claude Code CLI: npm install -g @anthropic-ai/claude-code
  ✅ إنشاء GitHub repo: gh repo create quran-miracles --private
  ✅ إضافة Secrets في GitHub Settings
  ✅ نسخ ملفات workflows من هذا الملف
  ✅ ربط Vercel بالـ repo (من vercel.com)
  ✅ ربط Railway بالـ repo (من railway.app)
```

---

## إعداد Vercel (5 دقائق)

```bash
# من مجلد frontend/
npm install -g vercel
vercel login
vercel link      # يربط المجلد بمشروع Vercel
vercel env add NEXT_PUBLIC_API_URL  # https://api.quran-miracles.railway.app
```

## إعداد Railway (5 دقائق)

```bash
# من مجلد backend/
npm install -g @railway/cli
railway login
railway init     # ينشئ مشروع جديد
railway link     # يربط بـ GitHub repo

# إضافة المتغيرات البيئية
railway variables set ANTHROPIC_API_KEY=sk-ant-...
railway variables set DATABASE_URL=postgresql://...
railway variables set REDIS_URL=redis://...
```

---

*docs/12_cicd_github.md — الإصدار 3.0 | معجزات القرآن الكريم*
