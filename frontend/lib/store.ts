import { create } from "zustand";
import type {
  Verse,
  Finding,
  Prediction,
  DiscoveryStage,
} from "@/types";

/** Global application state. */
interface AppState {
  /* ── Quran browsing ──────────────────────── */
  currentSurah: number | null;
  currentVerse: number | null;
  setCurrentVerse: (surah: number, verse: number) => void;

  /* ── Discovery engine ────────────────────── */
  isStreaming: boolean;
  setIsStreaming: (streaming: boolean) => void;
  discoveryStage: DiscoveryStage | "";
  setDiscoveryStage: (stage: DiscoveryStage | "") => void;
  discoveryVerses: Verse[];
  setDiscoveryVerses: (verses: Verse[]) => void;
  discoveryFindings: Finding[];
  addDiscoveryFinding: (finding: Finding) => void;
  discoverySynthesis: string;
  appendSynthesis: (token: string) => void;
  qualityScore: number | null;
  setQualityScore: (score: number | null) => void;
  resetDiscovery: () => void;

  /* ── Predictions ─────────────────────────── */
  predictions: Prediction[];
  setPredictions: (predictions: Prediction[]) => void;
}

export const useAppStore = create<AppState>((set) => ({
  /* ── Quran browsing ──────────────────────── */
  currentSurah: null,
  currentVerse: null,
  setCurrentVerse: (surah, verse) =>
    set({ currentSurah: surah, currentVerse: verse }),

  /* ── Discovery engine ────────────────────── */
  isStreaming: false,
  setIsStreaming: (streaming) => set({ isStreaming: streaming }),
  discoveryStage: "",
  setDiscoveryStage: (stage) => set({ discoveryStage: stage }),
  discoveryVerses: [],
  setDiscoveryVerses: (verses) => set({ discoveryVerses: verses }),
  discoveryFindings: [],
  addDiscoveryFinding: (finding) =>
    set((s) => ({ discoveryFindings: [...s.discoveryFindings, finding] })),
  discoverySynthesis: "",
  appendSynthesis: (token) =>
    set((s) => ({ discoverySynthesis: s.discoverySynthesis + token })),
  qualityScore: null,
  setQualityScore: (score) => set({ qualityScore: score }),
  resetDiscovery: () =>
    set({
      discoveryStage: "",
      discoveryVerses: [],
      discoveryFindings: [],
      discoverySynthesis: "",
      qualityScore: null,
    }),

  /* ── Predictions ─────────────────────────── */
  predictions: [],
  setPredictions: (predictions) => set({ predictions }),
}));
