import type { Edge, Node } from "reactflow";
import type { EdgeMetadata, FunctionGraph } from "./graphSchema";
import type { SupportedLanguage } from "@i18n/strings";
import { createContentTranslator } from "@i18n/translator";
import { getEdgeStatusClass, normalizeEdgeStatus } from "./status";

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
    const metadata: EdgeMetadata & Record<string, unknown> = { ...(edge.metadata ?? {}) };
    const originalAnimated = edge.label === "True" || edge.label === "False";
    metadata.__originalAnimated = originalAnimated;

    const resolvedStatus = normalizeEdgeStatus(edge.metadata?.status);
    let className: string | undefined;
    if (resolvedStatus) {
      metadata.status = resolvedStatus;
      className = getEdgeStatusClass(resolvedStatus);
    } else if (edge.metadata?.status && process.env.NODE_ENV !== "production") {
      console.warn(`Unsupported edge status "${String(edge.metadata.status)}" – rendering with default styling.`);
    }

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
      className,
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

  const updatedEdges = edges.map((edge) => {
    const data = (edge.data ?? {}) as Record<string, unknown>;
    const { __originalAnimated, ...rest } = data;
    const metadata = Object.keys(rest).length > 0 ? (rest as EdgeMetadata) : undefined;

    return {
      source: edge.source,
      target: edge.target,
      label: edge.label,
      metadata,
    };
  });

  return {
    ...fn,
    nodes: updatedNodes,
    edges: updatedEdges,
  };
}
