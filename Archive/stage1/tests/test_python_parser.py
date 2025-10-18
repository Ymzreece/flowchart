from __future__ import annotations

import unittest
from pathlib import Path

from flow_ir.parsers.python_parser import PythonParser


class PythonParserTests(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = PythonParser()
        self.fixture_path = Path(__file__).parent / "fixtures" / "sample_python.py"

    def test_parses_function(self) -> None:
        module = self.parser.parse_file(self.fixture_path)
        self.assertEqual(module.language, "python")
        self.assertEqual(len(module.functions), 1)
        fn = module.functions[0]
        self.assertEqual(fn.name, "process_order")
        labels = [node.label for node in fn.nodes]
        self.assertIn("Start", labels)
        self.assertIn("End", labels)
        self.assertTrue(any(label.startswith("if ") for label in labels))
        summaries = [node.summary for node in fn.nodes]
        self.assertTrue(any(summary and "Check whether" in summary for summary in summaries))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
