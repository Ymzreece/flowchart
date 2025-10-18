import { create } from "zustand";
import type { FunctionGraph, ModuleGraph } from "@lib/graphSchema";

interface FlowState {
  currentModule: ModuleGraph | null;
  currentFunction: FunctionGraph | null;
  selectedNodeId: string | null;
  loadGraph: (graph: ModuleGraph | FunctionGraph) => void;
  updateFunction: (fn: FunctionGraph | null) => void;
  selectNode: (nodeId: string | null) => void;
}

export const useFlowStore = create<FlowState>((set) => ({
  currentModule: null,
  currentFunction: null,
  selectedNodeId: null,
  loadGraph: (graph) =>
    set(() => {
      if ("functions" in graph) {
        return {
          currentModule: graph,
          currentFunction: graph.functions[0] ?? null,
          selectedNodeId: null,
        };
      }
      return {
        currentModule: {
          language: "unknown",
          functions: [graph],
        },
        currentFunction: graph,
        selectedNodeId: null,
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
}));
