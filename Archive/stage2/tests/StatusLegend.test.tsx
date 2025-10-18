import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { StatusLegend } from "../src/components/StatusLegend";

describe("StatusLegend", () => {
  it("renders nothing when no statuses are provided", () => {
    const markup = renderToStaticMarkup(<StatusLegend statuses={[]} />);
    expect(markup).toBe("");
  });

  it("displays provided statuses in stable order", () => {
    const markup = renderToStaticMarkup(<StatusLegend statuses={["warning", "success"]} />);
    expect(markup).toContain("Edge status");
    expect(markup).toContain("Success");
    expect(markup).toContain("Warning");
    expect(markup.indexOf("Success")).toBeLessThan(markup.indexOf("Warning"));
  });
});
