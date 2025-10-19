**Step 1:
python flowcode_1/flowchart_generator.py --prompt flowcode_1/prompt.md --include <file_name> --output <file_explanation>.txt


**Step 2:
python flowcode_2/graph_generator.py --input <file_explanation>.txt --output-prefix flowchart


**Step 3:
PYTHONPATH=flowcode_2/src python -m flowcode_renderer.cli --input flowchart_<language>.json --format stage2 --output flowchart_<language>.stage2.json


**Step 4:
npm run dev --prefix Archive/stage2