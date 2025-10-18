export type SupportedLanguage = "en" | "zh";

const STRINGS = {
  en: {
    appTitle: "Flowchart Editor",
    importJson: "Import JSON",
    exportJson: "Export JSON",
    languageLabel: "Language",
    nodeDetails: "Node Details",
    loadGraphPrompt: "Load a graph to get started.",
    selectNodePrompt: "Select a node to inspect its details.",
    fieldId: "ID",
    fieldType: "Type",
    fieldSummary: "Summary",
    fieldCode: "Code",
    fieldSource: "Source",
    fallbackMessage: "Import a flow JSON file to begin editing.",
    languageEnglish: "English",
    languageChinese: "中文"
  },
  zh: {
    appTitle: "流程图编辑器",
    importJson: "导入 JSON",
    exportJson: "导出 JSON",
    languageLabel: "语言",
    nodeDetails: "节点详情",
    loadGraphPrompt: "请先加载一个流程图。",
    selectNodePrompt: "选择一个节点查看详情。",
    fieldId: "编号",
    fieldType: "类型",
    fieldSummary: "摘要",
    fieldCode: "代码",
    fieldSource: "来源",
    fallbackMessage: "导入流程图 JSON 文件开始编辑。",
    languageEnglish: "英语",
    languageChinese: "中文"
  }
} as const;

export type TranslationKey = keyof typeof STRINGS.en;

export function getTranslation(language: SupportedLanguage, key: TranslationKey): string {
  const bundle = STRINGS[language] ?? STRINGS.en;
  return bundle[key] ?? STRINGS.en[key];
}

export const availableLanguages: { value: SupportedLanguage; labelKey: TranslationKey }[] = [
  { value: "en", labelKey: "languageEnglish" },
  { value: "zh", labelKey: "languageChinese" }
];
