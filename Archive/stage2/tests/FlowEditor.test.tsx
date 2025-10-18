import { render, screen } from "@testing-library/react";
import App from "../src/App";

describe("Flowchart Editor App", () => {
  it("renders header", () => {
    render(<App />);
    expect(screen.getByText(/Flowchart Editor/i)).toBeInTheDocument();
  });
});
