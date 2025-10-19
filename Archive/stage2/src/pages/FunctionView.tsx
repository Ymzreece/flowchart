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

    const params = new URLSearchParams(window.location.search);
    const graphUrl = params.get("graph");

    if (graphUrl) {
      fetch(graphUrl)
        .then((r) => r.json())
        .then((parsed) => {
          loadGraph(parsed);
          setHasLoadedSample(true);
        })
        .catch(() => {
          loadGraph(sampleGraph);
          setHasLoadedSample(true);
        });
      return;
    }

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
