import { useEffect } from "react";
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

  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const hasNodes = nodes.length > 0;

  useEffect(() => {
    if (!currentFunction) {
      setNodes([]);
      setEdges([]);
      return;
    }
    const { nodes: rfNodes, edges: rfEdges } = toReactFlowGraph(currentFunction);
    setNodes(rfNodes);
    setEdges(rfEdges);
  }, [currentFunction, setNodes, setEdges]);

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

  return (
    <div className="flow-editor">
      <ReactFlow
        nodes={nodes}
        edges={edges}
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
          <p>Import a flow JSON file to begin editing.</p>
        </div>
      )}
    </div>
  );
}
