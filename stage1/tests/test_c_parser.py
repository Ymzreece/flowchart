from __future__ import annotations

import unittest
from pathlib import Path

from flow_ir.parsers.c_simple_parser import CSimpleParser


class CSimpleParserTests(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = CSimpleParser()
        self.fixture = Path(__file__).parent / "fixtures" / "sample_c.c"

    def test_parses_c_function(self) -> None:
        module = self.parser.parse_file(self.fixture)
        self.assertEqual(module.language, "c")
        self.assertEqual(len(module.functions), 1)
        fn = module.functions[0]
        self.assertEqual(fn.name, "sum")
        labels = [node.label for node in fn.nodes]
        self.assertTrue(any(label.startswith("if") for label in labels))
        self.assertTrue(any(label.startswith("for") for label in labels))
        summaries = [node.summary for node in fn.nodes]
        self.assertTrue(any(summary and ("Repeat" in summary or "Loop" in summary) for summary in summaries))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
