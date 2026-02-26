/** Core domain types for the Quran Miracles frontend. */

export interface Surah {
  number: number;
  name_arabic: string;
  name_english: string;
  name_transliteration: string;
  revelation_type: "makki" | "madani";
  verse_count: number;
  revelation_order: number;
}

export interface Verse {
  surah_number: number;
  verse_number: number;
  text_uthmani: string;
  text_simple?: string;
  text_clean?: string;
  juz?: number;
  page_number?: number;
  word_count?: number;
  similarity?: number;
  confidence_tier?: ConfidenceTier;
}

export type ConfidenceTier =
  | "tier_0"
  | "tier_1"
  | "tier_2"
  | "tier_3"
  | "tier_4";

export interface Finding {
  finding: string;
  confidence_tier: string;
  discipline?: string;
  field?: string;
  main_objection?: string;
  doi_reference?: string;
}

export interface Discovery {
  id: string;
  title_ar: string;
  title_en?: string;
  description_ar: string;
  category?: string;
  discipline?: string;
  confidence_tier: ConfidenceTier;
  confidence_score?: number;
  verification_status: "pending" | "verified" | "disputed" | "rejected";
  verse_ids: number[];
  evidence?: Record<string, unknown>;
  counter_arguments?: Record<string, unknown>;
  created_at: string;
}

export interface ScientificCorrelation {
  id: number;
  verse_id: number;
  field: string;
  subfield?: string;
  topic: string;
  scientific_claim: string;
  discovery_year?: number;
  doi_reference?: string;
  confidence_tier: "tier_1" | "tier_2" | "tier_3";
  total_score?: number;
  main_objection?: string;
  verified: boolean;
}

export interface Prediction {
  id: string;
  verse_text: string;
  hypothesis: string;
  discipline: string;
  confidence_tier: ConfidenceTier;
  statistical_score?: number;
  research_steps: string[];
  disclaimer: string;
}

export interface ResearchMap {
  hypothesis_id: string;
  steps: ResearchStep[];
}

export interface ResearchStep {
  order: number;
  title: string;
  description: string;
  methodology: string;
  expected_outcome: string;
}

export interface TafseerBook {
  id: number;
  slug: string;
  name_ar: string;
  name_en?: string;
  author_ar: string;
  methodology: string;
  priority_order: number;
}

export interface TafseerEntry {
  book_slug: string;
  book_name_ar: string;
  text: string;
}

/** SSE streaming event stages */
export type DiscoveryStage =
  | "session_start"
  | "quran_search"
  | "quran_found"
  | "linguistic"
  | "science_finding"
  | "tafseer"
  | "synthesis_token"
  | "quality_done"
  | "complete"
  | "error";
