"use client";
import { create } from "zustand";

type IDEState = {
  files: Record<string, string>;
  activePath: string | null;
  setFiles: (files: Record<string, string>) => void;
  setActivePath: (path: string) => void;
  updateFile: (path: string, content: string) => void;
};

export const useIDEStore = create<IDEState>((set) => ({
  files: {},
  activePath: null,
  setFiles: (files) => set({ files, activePath: Object.keys(files)[0] ?? null }),
  setActivePath: (activePath) => set({ activePath }),
  updateFile: (path, content) => set((s) => ({ files: { ...s.files, [path]: content } }))
}));
