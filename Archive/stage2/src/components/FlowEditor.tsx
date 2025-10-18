import { useEffect, useMemo } from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  ReactFlowProvider,
  useEdgesState,
  useNodesState,
  addEdge,
  Connection,
  Edge,
} from "reactflow";
import "reactflow/dist/style.css";

import { useFlowStore } from "@hooks/useFlowStore";
import { toReactFlowGraph } from "@lib/transformer";
import { highlightConnectedEdges, highlightNodes } from "@lib/highlightUtils";
import { useTranslation } from "@i18n/useTranslation";

export function FlowEditor() {
  return (
    <ReactFlowProvider>
      <FlowEditorInner />
    </ReactFlowProvider>
  );
}

function FlowEditorInner() {
  const currentFunction = useFlowStore((state) => state.currentFunction);
  const selectNode = useFlowStore((state) => state.selectNode);
  const selectedNodeId = useFlowStore((state) => state.selectedNodeId);
  const language = useFlowStore((state) => state.language);
  const { t } = useTranslation();

  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const hasNodes = nodes.length > 0;

  useEffect(() => {
    if (!currentFunction) {
      setNodes([]);
      setEdges([]);
      return;
    }
    const { nodes: rfNodes, edges: rfEdges } = toReactFlowGraph(currentFunction, language);
    setNodes(rfNodes);
    setEdges(rfEdges);
  }, [currentFunction, language, setNodes, setEdges]);

  const onConnect = (connection: Connection) => {
    setEdges((eds) => addEdge(connection, eds));
  };

  const onSelectionChange = ({ nodes: selectedNodes }: { nodes: typeof nodes }) => {
    if (selectedNodes.length === 0) {
      selectNode(null);
      return;
    }
    selectNode(selectedNodes[0].id);
  };

  const handleNodesChange: typeof onNodesChange = (changes) => {
    onNodesChange(changes);
  };

  const handleEdgesChange: typeof onEdgesChange = (changes) => {
    onEdgesChange(changes);
  };

  const handleConnect = (connection: Edge | Connection) => {
    onConnect(connection as Connection);
  };

  const decoratedEdges = useMemo(
    () => highlightConnectedEdges(edges, selectedNodeId),
    [edges, selectedNodeId]
  );
  const decoratedNodes = useMemo(
    () => highlightNodes(nodes, edges, selectedNodeId),
    [nodes, edges, selectedNodeId]
  );

  return (
    <div className="flow-editor">
      <ReactFlow
        nodes={decoratedNodes}
        edges={decoratedEdges}
        style={{ width: "100%", height: "100%" }}
        onNodesChange={handleNodesChange}
        onEdgesChange={handleEdgesChange}
        onConnect={handleConnect}
        fitView
        onSelectionChange={onSelectionChange}
      >
        <Background />
        <MiniMap />
        <Controls />
      </ReactFlow>
      {!hasNodes && (
        <div className="flow-empty">
          <p>{t("fallbackMessage")}</p>
        </div>
      )}
    </div>
  );
}
