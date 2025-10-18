import type { EdgeStatus } from "@lib/graphSchema";
import { EDGE_STATUS_LABEL_KEYS, EDGE_STATUS_VALUES } from "@lib/status";
import { useTranslation } from "@i18n/useTranslation";

interface StatusLegendProps {
  statuses: EdgeStatus[];
}

export function StatusLegend({ statuses }: StatusLegendProps) {
  const { t } = useTranslation();

  if (!statuses || statuses.length === 0) {
    return null;
  }

  const present = new Set(statuses);

  return (
    <div className="status-legend" aria-label={t("statusLegendTitle")}>
      <span className="status-legend__title">{t("statusLegendTitle")}</span>
      <ul className="status-legend__list">
        {EDGE_STATUS_VALUES.filter((status) => present.has(status)).map((status) => (
          <li key={status} className="status-legend__item">
            <span aria-hidden="true" className={`status-legend__swatch status-legend__swatch--${status}`} />
            <span className="status-legend__label">{t(EDGE_STATUS_LABEL_KEYS[status])}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
