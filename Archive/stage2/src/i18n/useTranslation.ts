import { useMemo } from "react";
import { useFlowStore } from "@hooks/useFlowStore";
import { getTranslation, type SupportedLanguage, type TranslationKey } from "@i18n/strings";

export function useTranslation() {
  const language = useFlowStore((state) => state.language) as SupportedLanguage;

  const t = useMemo(() => {
    return (key: TranslationKey) => getTranslation(language, key);
  }, [language]);

  return { t, language };
}
