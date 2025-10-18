import { useFlowStore } from "@hooks/useFlowStore";

export function NodeSidebar() {
  const currentFunction = useFlowStore((state) => state.currentFunction);
  const selectedNodeId = useFlowStore((state) => state.selectedNodeId);

  if (!currentFunction) {
    return (
      <aside className="node-sidebar">
        <p>Load a graph to get started.</p>
      </aside>
    );
  }

  const node = currentFunction.nodes.find((n) => n.id === selectedNodeId);

  return (
    <aside className="node-sidebar">
      <h2>Node Details</h2>
      {node ? (
        <dl>
          <dt>ID</dt>
          <dd>{node.id}</dd>
          <dt>Type</dt>
          <dd>{node.kind}</dd>
          {node.summary && (
            <>
              <dt>Summary</dt>
              <dd>{node.summary}</dd>
            </>
          )}
          <dt>Code</dt>
          <dd>{node.label}</dd>
          {node.location && (
            <>
              <dt>Source</dt>
              <dd>
                {node.location.file_path}:{node.location.line}
              </dd>
            </>
          )}
        </dl>
      ) : (
        <p>Select a node to inspect its details.</p>
      )}
    </aside>
  );
}
