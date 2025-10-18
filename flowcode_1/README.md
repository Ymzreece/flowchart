# Flowcode Text Flowchart Generator (Prototype 1)

This prototype wires an LLM into the workflow so we can turn source code (or any textual brief) into a **natural-language explanation**. It reads prompts from `prompt.md`, sends them to the OpenAI API, and saves the model response as rich text. Stage 2 tooling can then transform that text into a structured flowchart.

## Model Choice

For the first pass, the script targets **`gpt-4.1-mini`**—a good balance between reasoning quality and cost. Use the `--model` flag if you want to try `gpt-4o`, `gpt-4o-mini`, or other available models.

## Project Structure

```
flowcode_1/
├── README.md
├── prompt.md              # Your instruction or source text for the LLM
└── flowchart_generator.py # CLI script that calls the LLM and writes output
```

## Requirements

- Python 3.9+
- `openai` Python SDK (`pip install openai`)
- An OpenAI API key with access to GPT‑4.1 models.

## Setting the API Key

Set the key as an environment variable before running the script:

```bash
export OPENAI_API_KEY="sk-..."
```

Alternatively, you can place it in a `.env` file and load it manually, or edit `flowchart_generator.py` to read from a different source. **Never hardcode the key in source control.**

## Usage

1. Edit `prompt.md` with the instructions you want the model to follow (keep high-level guidance here).
2. Provide source files directly via `--include` (optional, can be repeated) so you don’t have to paste code into the prompt template.
3. Run the generator (defaults to rich-text output):

   ```bash
   python flowchart_generator.py \
     --prompt prompt.md \
     --include path/to/source.c \
     --include path/to/README.md \
      --output flow_explanation.txt
   ```

4. The response is written to `flow_explanation.txt`. Keep this file for Stage 2 (`flowcode_2/graph_generator.py`) to turn into a structured flowchart.

## Next Steps

- Experiment with prompt engineering inside `prompt.md` to emphasise the details you need (menu breakdowns, branching, etc.).
- Wrap the script in a backend service or VS Code command for direct integration.
- Pass the generated text to Stage 2 tooling to produce a graph for React Flow or Graphviz visualisation.
