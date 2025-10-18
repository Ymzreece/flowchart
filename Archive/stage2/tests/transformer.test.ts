import { describe, expect, it, vi } from "vitest";
import { toReactFlowGraph, updateFunctionGraphFromReactFlow } from "../src/lib/transformer";
import type { FunctionGraph } from "../src/lib/graphSchema";

const baseFunction: FunctionGraph = {
  name: "Example",
  nodes: [
    { id: "start", kind: "start", label: "Start", summary: "Start", metadata: {} },
    { id: "end", kind: "end", label: "End", summary: "End", metadata: {} }
  ],
  edges: [
    {
      source: "start",
      target: "end",
      label: "Next",
      metadata: { status: "success" }
    }
  ],
  metadata: {}
};

describe("transformer", () => {
  it("applies status class and preserves metadata for recognised statuses", () => {
    const { nodes, edges } = toReactFlowGraph(baseFunction, "en");
    expect(nodes).toHaveLength(2);
    expect(edges[0].className).toBe("edge-status-success");
    expect((edges[0].data as Record<string, unknown>).status).toBe("success");

    const roundTrip = updateFunctionGraphFromReactFlow(baseFunction, nodes, edges);
    expect(roundTrip.edges[0].metadata?.status).toBe("success");
    expect(roundTrip.edges[0].metadata?.__originalAnimated).toBeUndefined();
  });

  it("falls back to neutral styling and warns for unknown statuses", () => {
    const warnSpy = vi.spyOn(console, "warn").mockImplementation(() => {});
    const fn: FunctionGraph = {
      ...baseFunction,
      edges: [
        {
          source: "start",
          target: "end",
          label: "Maybe",
          metadata: { status: "mystery" } as any
        }
      ]
    };

    const { edges } = toReactFlowGraph(fn, "en");
    expect(edges[0].className).toBeUndefined();
    expect(warnSpy).toHaveBeenCalledWith(expect.stringContaining("Unsupported edge status"));
    warnSpy.mockRestore();
  });
});
