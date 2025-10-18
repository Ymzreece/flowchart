import { describe, expect, it } from "vitest";
import { getEdgeStatusClass, normalizeEdgeStatus } from "../src/lib/status";

describe("status helpers", () => {
  it("normalizes valid statuses", () => {
    expect(normalizeEdgeStatus("SUCCESS")).toBe("success");
    expect(normalizeEdgeStatus("warning")).toBe("warning");
  });

  it("returns undefined for invalid statuses", () => {
    expect(normalizeEdgeStatus("mystery")).toBeUndefined();
    expect(normalizeEdgeStatus(42)).toBeUndefined();
  });

  it("converts statuses to class names", () => {
    expect(getEdgeStatusClass("error")).toBe("edge-status-error");
  });
});
