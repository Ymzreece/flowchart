import type { EdgeStatus } from "./graphSchema";
import type { TranslationKey } from "@i18n/strings";

export const EDGE_STATUS_VALUES: readonly EdgeStatus[] = [
  "default",
  "active",
  "success",
  "warning",
  "error",
  "disabled"
] as const;

const EDGE_STATUS_SET = new Set<string>(EDGE_STATUS_VALUES);

export function normalizeEdgeStatus(value: unknown): EdgeStatus | undefined {
  if (typeof value !== "string") {
    return undefined;
  }
  const candidate = value.toLowerCase();
  return EDGE_STATUS_SET.has(candidate) ? (candidate as EdgeStatus) : undefined;
}

export function getEdgeStatusClass(status: EdgeStatus): string {
  return `edge-status-${status}`;
}

export const EDGE_STATUS_LABEL_KEYS: Record<EdgeStatus, TranslationKey> = {
  default: "statusDefault",
  active: "statusActive",
  success: "statusSuccess",
  warning: "statusWarning",
  error: "statusError",
  disabled: "statusDisabled"
} as const;
