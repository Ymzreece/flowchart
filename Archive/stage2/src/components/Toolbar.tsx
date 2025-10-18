import { ChangeEvent, useMemo } from "react";
import { useFlowStore } from "@hooks/useFlowStore";
import type { ModuleGraph } from "@lib/graphSchema";
import { useTranslation } from "@i18n/useTranslation";
import { availableLanguages, type SupportedLanguage } from "@i18n/strings";
import { normalizeEdgeStatus } from "@lib/status";
import type { EdgeStatus } from "@lib/graphSchema";
import { StatusLegend } from "@components/StatusLegend";

export function Toolbar() {
  const loadGraph = useFlowStore((state) => state.loadGraph);
  const currentModule = useFlowStore((state) => state.currentModule);
  const currentFunction = useFlowStore((state) => state.currentFunction);
  const setLanguage = useFlowStore((state) => state.setLanguage);
  const { t, language } = useTranslation();
  const statuses = useMemo(() => {
    if (!currentFunction) {
      return [] as EdgeStatus[];
    }
    const detected = new Set<EdgeStatus>();
    currentFunction.edges.forEach((edge) => {
      const status = normalizeEdgeStatus(edge.metadata?.status);
      if (status) {
        detected.add(status);
      }
    });
    return Array.from(detected);
  }, [currentFunction]);

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
        <span>{t("importJson")}</span>
        <input type="file" accept="application/json" onChange={handleFileUpload} hidden />
      </label>
      <button type="button" className="toolbar__button" onClick={handleExport} disabled={!currentFunction}>
        {t("exportJson")}
      </button>
      <label className="toolbar__language">
        <span>{t("languageLabel")}</span>
        <select value={language} onChange={(event) => setLanguage(event.target.value as SupportedLanguage)}>
          {availableLanguages.map((entry) => (
            <option key={entry.value} value={entry.value}>
              {t(entry.labelKey)}
            </option>
          ))}
        </select>
      </label>
      <div className="toolbar__meta">
        {currentFunction && (
          <div className="toolbar__info">
            <strong>{currentFunction.name}</strong>
            <span>{currentModule?.language}</span>
          </div>
        )}
        <StatusLegend statuses={statuses} />
      </div>
    </div>
  );
}
