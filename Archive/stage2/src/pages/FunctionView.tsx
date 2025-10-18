import { useEffect, useState } from "react";
import { FlowEditor } from "@components/FlowEditor";
import { NodeSidebar } from "@components/NodeSidebar";
import { Toolbar } from "@components/Toolbar";
import { useFlowStore } from "@hooks/useFlowStore";
import { sampleGraph } from "@lib/sampleData";

export function FunctionView() {
  const [hasLoadedSample, setHasLoadedSample] = useState(false);
  const loadGraph = useFlowStore((state) => state.loadGraph);

  useEffect(() => {
    if (hasLoadedSample) return;
    loadGraph(sampleGraph);
    setHasLoadedSample(true);
  }, [hasLoadedSample, loadGraph]);

  return (
    <div className="function-view">
      <Toolbar />
      <div className="function-layout">
        <FlowEditor />
        <NodeSidebar />
      </div>
    </div>
  );
}
