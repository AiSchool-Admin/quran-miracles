import { create } from "zustand";

interface AppState {
  currentSurah: number | null;
  currentVerse: number | null;
  setCurrentVerse: (surah: number, verse: number) => void;
  isStreaming: boolean;
  setIsStreaming: (streaming: boolean) => void;
}

export const useAppStore = create<AppState>((set) => ({
  currentSurah: null,
  currentVerse: null,
  setCurrentVerse: (surah, verse) =>
    set({ currentSurah: surah, currentVerse: verse }),
  isStreaming: false,
  setIsStreaming: (streaming) => set({ isStreaming: streaming }),
}));
