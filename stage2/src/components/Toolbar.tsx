import { ChangeEvent } from "react";
import { useFlowStore } from "@hooks/useFlowStore";
import type { ModuleGraph } from "@lib/graphSchema";

export function Toolbar() {
  const loadGraph = useFlowStore((state) => state.loadGraph);
  const currentModule = useFlowStore((state) => state.currentModule);
  const currentFunction = useFlowStore((state) => state.currentFunction);

  const handleFileUpload = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const text = await file.text();
    try {
      const parsed = JSON.parse(text) as ModuleGraph;
      loadGraph(parsed);
    } catch (error) {
      console.error("Failed to parse JSON graph", error);
      alert("Invalid flow JSON. Please verify the structure.");
    }
  };

  const handleExport = () => {
    if (!currentModule || !currentFunction) return;
    const blob = new Blob([JSON.stringify(currentModule, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${currentFunction.name}.flow.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="toolbar">
      <label className="toolbar__upload">
        <span>Import JSON</span>
        <input type="file" accept="application/json" onChange={handleFileUpload} hidden />
      </label>
      <button type="button" className="toolbar__button" onClick={handleExport} disabled={!currentFunction}>
        Export JSON
      </button>
      {currentFunction && (
        <div className="toolbar__info">
          <strong>{currentFunction.name}</strong>
          <span>{currentModule?.language}</span>
        </div>
      )}
    </div>
  );
}
