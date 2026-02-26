# ── Stage 1: Build (compile C extensions then discard gcc) ──
FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

COPY backend/requirements.txt .
# Install only production deps — skip dev/test packages
RUN pip install --no-cache-dir --prefix=/install \
    -r requirements.txt

# ── Stage 2: Runtime (slim, no compiler) ──
FROM python:3.12-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

COPY backend/ .

ENV PORT=8000
ENV PYTHONUNBUFFERED=1
EXPOSE ${PORT}

CMD ["python", "start.py"]
