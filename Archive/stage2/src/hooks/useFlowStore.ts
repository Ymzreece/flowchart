import { create } from "zustand";
import type { FunctionGraph, ModuleGraph } from "@lib/graphSchema";
import type { SupportedLanguage } from "@i18n/strings";

interface FlowState {
  currentModule: ModuleGraph | null;
  currentFunction: FunctionGraph | null;
  selectedNodeId: string | null;
  language: SupportedLanguage;
  loadGraph: (graph: ModuleGraph | FunctionGraph) => void;
  updateFunction: (fn: FunctionGraph | null) => void;
  selectNode: (nodeId: string | null) => void;
  setLanguage: (language: SupportedLanguage) => void;
}

export const useFlowStore = create<FlowState>((set) => ({
  currentModule: null,
  currentFunction: null,
  selectedNodeId: null,
  language: "en",
  loadGraph: (graph) =>
    set((state) => {
      if ("functions" in graph) {
        const detectedLanguage = (graph.metadata?.language as SupportedLanguage | undefined) ?? state.language;
        return {
          currentModule: graph,
          currentFunction: graph.functions[0] ?? null,
          selectedNodeId: null,
          language: detectedLanguage,
        };
      }
      const detectedLanguage = state.language;
      return {
        currentModule: {
          language: "unknown",
          functions: [graph],
        },
        currentFunction: graph,
        selectedNodeId: null,
        language: detectedLanguage,
      };
    }),
  updateFunction: (fn) =>
    set((state) => {
      if (!fn) {
        return state;
      }
      if (!state.currentModule) {
        return {
          ...state,
          currentFunction: fn,
        };
      }
      const updatedFunctions = state.currentModule.functions.map((existing) =>
        existing.name === fn.name ? fn : existing,
      );
      return {
        currentModule: {
          ...state.currentModule,
          functions: updatedFunctions,
        },
        currentFunction: fn,
      };
    }),
  selectNode: (nodeId) => set({ selectedNodeId: nodeId }),
  setLanguage: (language) => set({ language }),
}));
