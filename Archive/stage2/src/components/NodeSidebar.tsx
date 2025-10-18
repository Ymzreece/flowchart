import { useMemo } from "react";
import { useFlowStore } from "@hooks/useFlowStore";
import { useTranslation } from "@i18n/useTranslation";
import { createContentTranslator } from "@i18n/translator";

export function NodeSidebar() {
  const currentFunction = useFlowStore((state) => state.currentFunction);
  const selectedNodeId = useFlowStore((state) => state.selectedNodeId);
  const language = useFlowStore((state) => state.language);
  const { t } = useTranslation();
  const translator = useMemo(() => createContentTranslator(language), [language]);

  if (!currentFunction) {
    return (
      <aside className="node-sidebar">
        <p>{t("loadGraphPrompt")}</p>
      </aside>
    );
  }

  const node = currentFunction.nodes.find((n) => n.id === selectedNodeId);

  return (
    <aside className="node-sidebar">
      <h2>{t("nodeDetails")}</h2>
      {node ? (
        <dl>
          <dt>{t("fieldId")}</dt>
          <dd>{node.id}</dd>
          <dt>{t("fieldType")}</dt>
          <dd>{node.kind}</dd>
          {node.summary && (
            <>
              <dt>{t("fieldSummary")}</dt>
              <dd>{translator.translateNodeLabel(node.summary, node.metadata)}</dd>
            </>
          )}
          <dt>{t("fieldCode")}</dt>
          <dd>{node.label}</dd>
          {node.location && (
            <>
              <dt>{t("fieldSource")}</dt>
              <dd>
                {node.location.file_path}:{node.location.line}
              </dd>
            </>
          )}
        </dl>
      ) : (
        <p>{t("selectNodePrompt")}</p>
      )}
    </aside>
  );
}
