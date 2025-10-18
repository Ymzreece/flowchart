import type { Edge, Node } from "reactflow";

const EDGE_HIGHLIGHT_CLASS = "edge-highlight";
const EDGE_DIM_CLASS = "edge-dim";
const NODE_SELECTED_CLASS = "node-selected";
const NODE_CONNECTED_CLASS = "node-connected";
const NODE_DIM_CLASS = "node-dim";

const EDGE_CLASSES = [EDGE_HIGHLIGHT_CLASS, EDGE_DIM_CLASS];
const NODE_CLASSES = [NODE_SELECTED_CLASS, NODE_CONNECTED_CLASS, NODE_DIM_CLASS];

function sanitizeClassName(className: string | undefined, classesToRemove: string[]): string {
  if (!className) {
    return "";
  }
  return className
    .split(/\s+/)
    .filter(Boolean)
    .filter((cls) => !classesToRemove.includes(cls))
    .join(" ");
}

function appendClass(base: string, cls: string | undefined): string | undefined {
  if (!cls) {
    return base.trim() || undefined;
  }
  return [base, cls].filter(Boolean).join(" ").trim() || undefined;
}

function getOriginalAnimated(edge: Edge): boolean {
  const data = edge.data as Record<string, unknown> | undefined;
  if (data && typeof data === "object" && "__originalAnimated" in data) {
    return Boolean((data as Record<string, unknown>).__originalAnimated);
  }
  return Boolean(edge.animated);
}

export function highlightConnectedEdges(edges: Edge[], selectedNodeId?: string | null): Edge[] {
  if (!selectedNodeId) {
    return edges.map((edge) => {
      const baseClass = sanitizeClassName(edge.className, EDGE_CLASSES);
      return {
        ...edge,
        className: baseClass || undefined,
        animated: getOriginalAnimated(edge),
      };
    });
  }

  return edges.map((edge) => {
    const baseClass = sanitizeClassName(edge.className, EDGE_CLASSES);
    const isConnected = edge.source === selectedNodeId || edge.target === selectedNodeId;
    const className = appendClass(baseClass, isConnected ? EDGE_HIGHLIGHT_CLASS : EDGE_DIM_CLASS);
    return {
      ...edge,
      className,
      animated: isConnected ? true : getOriginalAnimated(edge),
    };
  });
}

export function highlightNodes(nodes: Node[], edges: Edge[], selectedNodeId?: string | null): Node[] {
  if (!selectedNodeId) {
    return nodes.map((node) => {
      const baseClass = sanitizeClassName(node.className, NODE_CLASSES);
      return {
        ...node,
        className: baseClass || undefined,
      };
    });
  }

  const neighborIds = new Set<string>();
  edges.forEach((edge) => {
    if (edge.source === selectedNodeId) {
      neighborIds.add(edge.target);
    }
    if (edge.target === selectedNodeId) {
      neighborIds.add(edge.source);
    }
  });

  return nodes.map((node) => {
    const baseClass = sanitizeClassName(node.className, NODE_CLASSES);
    let addition: string | undefined;
    if (node.id === selectedNodeId) {
      addition = NODE_SELECTED_CLASS;
    } else if (neighborIds.has(node.id)) {
      addition = NODE_CONNECTED_CLASS;
    } else {
      addition = NODE_DIM_CLASS;
    }
    return {
      ...node,
      className: appendClass(baseClass, addition),
    };
  });
}
