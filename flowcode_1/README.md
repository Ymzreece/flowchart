# Flowcode Text Flowchart Generator (Prototype 1)

This prototype wires an LLM into the workflow so we can turn source code (or any textual brief) into a natural-language flowchart. It reads prompts from `prompt.md`, sends them to the OpenAI API, and saves the model response.

## Model Choice

For the first pass, the script targets **`gpt-4.1-mini`**:

- Produces richer, step-by-step reasoning than `gpt-4o-mini`, while still being faster/cheaper than the larger `gpt-4.1`.
- Handles long prompts (project overviews, code snippets) comfortably.
- Supports JSON/text output if we later choose to structure responses.

You can change the `MODEL_NAME` constant in `flowchart_generator.py` if you want to try `gpt-4.1` (higher quality) or `gpt-4o-mini` (cheaper, leaner).

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

1. Edit `prompt.md` with the text you want the model to use (e.g., copy/paste code, describe a repo, etc.).
2. Run the generator:

   ```bash
   python flowchart_generator.py \
     --prompt prompt.md \
     --output flowchart.txt
   ```

3. The response is written to `flowchart.txt`. You can add a `--format json` flag to request structured JSON (the script adjusts the prompt accordingly).

## Next Steps

- Experiment with prompt engineering inside `prompt.md` to steer the model toward the tone you want.
- Wrap the script in a backend service or VS Code command for direct integration.
- Feed the LLM output back into Stage 2 to render a natural-language flowchart (e.g., using React Flow with textual nodes).
