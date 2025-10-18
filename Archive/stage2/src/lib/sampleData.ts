import type { ModuleGraph } from "./graphSchema";

export const sampleGraph: ModuleGraph = {
  language: "python",
  metadata: {
    file_path: "examples/process_order.py",
  },
  functions: [
    {
      name: "process_order",
      parameters: ["order", "customer"],
      nodes: [
        {
          id: "start",
          kind: "start",
          label: "Start",
          summary: "Begin the function.",
          metadata: {},
        },
        {
          id: "cond1",
          kind: "conditional",
          label: "if customer.is_vip",
          summary: "Check whether customer.is_vip.",
          metadata: {},
        },
        {
          id: "vip",
          kind: "statement",
          label: "apply_vip_discount(order)",
          summary: "Call apply vip discount with order.",
          metadata: {},
        },
        {
          id: "total_check",
          kind: "conditional",
          label: "elif order.total > 100",
          summary: "Otherwise, check whether order.total is greater than 100.",
          metadata: {},
        },
        {
          id: "discount",
          kind: "call",
          label: "apply_discount(order)",
          summary: "Call apply discount with order.",
          metadata: {},
        },
        {
          id: "ship",
          kind: "call",
          label: "ship_order(order)",
          summary: "Call ship order with order.",
          metadata: {},
        },
        {
          id: "end",
          kind: "end",
          label: "End",
          summary: "Finish the function.",
          metadata: {},
        },
      ],
      edges: [
        { source: "start", target: "cond1" },
        { source: "cond1", target: "vip", label: "True" },
        { source: "cond1", target: "total_check", label: "False" },
        { source: "vip", target: "ship" },
        { source: "total_check", target: "discount", label: "True" },
        { source: "total_check", target: "ship", label: "False" },
        { source: "discount", target: "ship" },
        { source: "ship", target: "end" },
      ],
    },
  ],
};
