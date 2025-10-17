export type NodeKind =
  | "start"
  | "end"
  | "statement"
  | "conditional"
  | "loop"
  | "call"
  | "return"
  | "exception"
  | "unknown";

export interface SourceLocation {
  file_path: string;
  line: number;
  column?: number;
}

export interface NodeIR {
  id: string;
  kind: NodeKind;
  label: string;
  summary?: string | null;
  location?: SourceLocation;
  metadata?: Record<string, unknown>;
}

export interface EdgeIR {
  source: string;
  target: string;
  label?: string;
  metadata?: Record<string, unknown>;
}

export interface FunctionGraph {
  name: string;
  parameters?: string[];
  returns?: string | null;
  docstring?: string | null;
  nodes: NodeIR[];
  edges: EdgeIR[];
  metadata?: Record<string, unknown>;
}

export interface ModuleGraph {
  language: string;
  functions: FunctionGraph[];
  metadata?: Record<string, unknown>;
}
