"""End-to-end test: run the full discovery pipeline with real DB data.

Usage:
    cd backend && python -m pytest tests/test_e2e_discovery.py -v -s
    # or directly:
    cd backend && python tests/test_e2e_discovery.py
"""

from __future__ import annotations

import asyncio
import json
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


async def run_e2e_test():
    """Run the full discovery pipeline with 'الماء في القرآن الكريم'."""
    from arabic_nlp.embeddings_service import EmbeddingsService
    from database.service import DatabaseService
    from discovery_engine.core.graph import build_discovery_graph

    db_url = os.environ.get(
        "DATABASE_URL",
        "postgresql://quran_user:changeme@localhost:5432/quran_miracles",
    )

    print("=" * 70)
    print("  E2E Test: الماء في القرآن الكريم")
    print("=" * 70)

    # 1. Initialize services
    print("\n[1] Initializing DatabaseService...")
    db = DatabaseService(db_url)
    await db.connect()
    print("    ✅ Connected to database")

    print("[2] Initializing EmbeddingsService...")
    embeddings = EmbeddingsService()
    await embeddings.initialize(db_url)
    print("    ✅ Embeddings loaded")

    # 2. Build graph
    print("[3] Building discovery graph...")
    graph = build_discovery_graph(db=db, embeddings=embeddings)
    print("    ✅ Graph built")

    # 3. Run query
    query = "الماء في القرآن الكريم"
    print(f"\n[4] Running query: «{query}»\n")

    initial_state = {
        "query": query,
        "disciplines": ["physics", "biology", "psychology"],
        "mode": "guided",
        "iteration_count": 0,
        "streaming_updates": [],
    }

    config = {"configurable": {"thread_id": "test-e2e-001"}}
    result = await graph.ainvoke(initial_state, config=config)

    # 4. Display results
    print("=" * 70)
    print("  RESULTS")
    print("=" * 70)

    # Source
    source = "unknown"
    for u in result.get("streaming_updates", []):
        if u.get("stage") == "quran_rag":
            source = u.get("source", "unknown")
    print(f"\n✅ source: \"{source}\"")

    # Verses
    verses = result.get("verses", [])
    print(f"✅ عدد الآيات: {len(verses)}")
    if verses:
        top = verses[0]
        sim = top.get("similarity", 0)
        print(f"✅ أعلى آية تشابهاً: {top.get('verse_key', '?')} — similarity: {sim:.4f}")
        print(f"   {top.get('text_clean', '')[:80]}...")

    # Tafseers
    total_tafseers = 0
    has_shaarawy = False
    for v in verses:
        tafseers = v.get("tafseers", [])
        total_tafseers += len(tafseers)
        for t in tafseers:
            if "shaarawy" in t.get("slug", "").lower():
                has_shaarawy = True
    print(f"\n✅ التفاسير: {total_tafseers} تفسير")
    print(f"✅ الشعراوي موجود: {'نعم' if has_shaarawy else 'لا'}")

    # Tafseer findings
    tafseer_findings = result.get("tafseer_findings", {})
    if isinstance(tafseer_findings, dict):
        shaarawy_note = tafseer_findings.get("shaarawy_linguistic_note", "")
        print(f"   ملاحظة الشعراوي: {shaarawy_note[:150]}...")

    # Science
    science = result.get("science_findings", [])
    print(f"\n✅ اكتشافات علمية: {len(science)}")
    if science:
        s = science[0]
        print(f"   {s.get('verse_key', '?')}: {s.get('scientific_claim', '')[:100]}...")
        print(f"   confidence_tier: {s.get('confidence_tier', '?')}")

    # Humanities
    humanities = result.get("humanities_findings", [])
    print(f"\n✅ اكتشافات إنسانية: {len(humanities)}")
    if humanities:
        h = humanities[0]
        print(f"   {h.get('verse_key', '?')}: correlation_type={h.get('correlation_type', '?')}")

    # Synthesis
    synthesis = result.get("synthesis", "")
    tier = result.get("confidence_tier", "?")
    print(f"\n✅ confidence_tier: {tier}")

    # Quality
    quality = result.get("quality_score", 0.0)
    print(f"✅ درجة الجودة: {quality}")

    # Discovery persistence
    discovery_id = result.get("discovery_id")
    print(f"\n✅ discovery_id: {discovery_id}")

    if discovery_id and db:
        try:
            row = await db.pool.fetchrow(
                "SELECT * FROM discoveries WHERE id = $1::uuid",
                discovery_id,
            )
            if row:
                print(f"✅ حُفظ الاكتشاف في DB!")
                print(f"   title_ar: {row['title_ar'][:80]}...")
                print(f"   confidence_tier: {row['confidence_tier']}")
                print(f"   created_at: {row['created_at']}")
        except Exception as exc:
            print(f"⚠️ Error checking DB: {exc}")

    # Cleanup
    await db.close()

    print("\n" + "=" * 70)
    print("  TEST COMPLETE")
    print("=" * 70)

    return result


if __name__ == "__main__":
    asyncio.run(run_e2e_test())
