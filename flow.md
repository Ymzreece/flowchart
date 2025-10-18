**Step 1:
python flowcode_1/flowchart_generator.py \     
       --prompt flowcode_1/prompt.md \
       --output flow_explanation_motor.txt


**Step 2:
python flowcode_2/graph_generator.py \                     
    --input flow_explanation_motor.txt \
    --output-prefix flowchart


**Step 3:
PYTHONPATH=flowcode_2/src python -m flowcode_renderer.cli \
    --input flowchart_zh.json \
    --format stage2 \
    --output flowchart_zh.stage2.json


**Step 4:
npm run dev --prefix Archive/stage2