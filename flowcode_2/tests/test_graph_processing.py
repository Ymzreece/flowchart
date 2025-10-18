from __future__ import annotations

import json
import unittest

from flowcode_renderer.converter import graph_to_stage2_module
from flowcode_renderer.parser import parse_graph_json

SAMPLE_JSON = json.dumps(
    {
        "metadata": {"title": "Test Flow", "summary": "Demo"},
        "entry_node": "start",
        "nodes": [
            {"id": "start", "title": "Start", "summary": "Begin", "type": "start"},
            {"id": "decision", "title": "Check", "summary": "Check condition", "type": "decision"},
            {"id": "end", "title": "End", "summary": "Finish", "type": "end"},
        ],
        "edges": [
            {"source": "start", "target": "decision", "label": "Next"},
            {"source": "decision", "target": "end", "label": "True"},
        ],
    }
)


class GraphProcessingTests(unittest.TestCase):
    def test_parse_graph_json(self) -> None:
        graph = parse_graph_json(SAMPLE_JSON)
        self.assertEqual(graph.entry_node, "start")
        self.assertEqual(len(graph.nodes), 3)
        self.assertEqual(len(graph.edges), 2)
        self.assertEqual(graph.nodes["decision"].type, "decision")

    def test_converter_stage2(self) -> None:
        graph = parse_graph_json(SAMPLE_JSON)
        module = graph_to_stage2_module(graph)
        self.assertEqual(module["functions"][0]["name"], "Test Flow")
        node_kinds = {node["id"]: node["kind"] for node in module["functions"][0]["nodes"]}
        self.assertEqual(node_kinds["start"], "start")
        self.assertEqual(node_kinds["decision"], "conditional")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
