import type { Edge, Node } from "reactflow";
import type { FunctionGraph } from "./graphSchema";
import type { SupportedLanguage } from "@i18n/strings";
import { createContentTranslator } from "@i18n/translator";

interface ReactFlowGraph {
  nodes: Node[];
  edges: Edge[];
}

export function toReactFlowGraph(fn: FunctionGraph, language: SupportedLanguage = "en"): ReactFlowGraph {
  const translator = createContentTranslator(language);
  const nodes: Node[] = fn.nodes.map((node, index) => ({
    id: node.id,
    position: {
      x: (index % 4) * 240,
      y: Math.floor(index / 4) * 160,
    },
    data: {
      label: translator.translateNodeLabel(node.summary ?? node.label, node.metadata),
      summary: node.summary ? translator.translateNodeLabel(node.summary, node.metadata) : node.summary,
      code: node.label,
      kind: node.kind,
      location: node.location,
      metadata: node.metadata,
    },
    type: "default",
  }));

  const edges: Edge[] = fn.edges.map((edge) => {
    const metadata: Record<string, unknown> = { ...(edge.metadata ?? {}) };
    const originalAnimated = edge.label === "True" || edge.label === "False";
    metadata.__originalAnimated = originalAnimated;

    return {
      id: `${edge.source}-${edge.target}-${edge.label ?? "edge"}`,
      source: edge.source,
      target: edge.target,
      label: translator.translateEdgeLabel(edge.label, edge.metadata),
      data: metadata,
      animated: originalAnimated,
      markerEnd: {
        type: "arrowclosed",
      },
    };
  });

  return { nodes, edges };
}

export function updateFunctionGraphFromReactFlow(
  fn: FunctionGraph,
  nodes: Node[],
  edges: Edge[],
): FunctionGraph {
  const updatedNodes = nodes.map((node) => {
    const original = fn.nodes.find((n) => n.id === node.id);
    return {
      ...original,
      id: node.id,
      label: original?.label ?? String(node.data?.code ?? node.id),
      summary: (node.data?.summary as string | undefined) ?? original?.summary,
      metadata: {
        ...(original?.metadata ?? {}),
        position: node.position,
      },
    };
  });

  const updatedEdges = edges.map((edge) => ({
    source: edge.source,
    target: edge.target,
    label: edge.label,
    metadata: edge.data as Record<string, unknown> | undefined,
  }));

  return {
    ...fn,
    nodes: updatedNodes,
    edges: updatedEdges,
  };
}
