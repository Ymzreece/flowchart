# End-to-End Orchestrator CLI

## ADDED Requirements

### Requirement: `flowcode <filename>` runs Steps 1–3
The repository SHALL expose a root-level `flowcode` command that executes the first three steps from `flow.md` with a single invocation.

#### Scenario: Running `flowcode path/to/file.ext`
- Given `OPENAI_API_KEY` is available in the environment or `.env` in the repo root contains a usable key
- When the user runs `flowcode path/to/file.ext`
- Then Step 1 generates `flow_explanation.txt` in the repo root by invoking Stage 1 with `--include path/to/file.ext`
- And Step 2 generates `flowchart_en.json` and `flowchart_zh.json` in the repo root
- And Step 3 writes `flowchart_en.stage2.json` and `flowchart_zh.stage2.json` in the repo root
- And the command exits with a zero status code after printing success messages for each artifact.

### Requirement: Optional UI launch via `--open-ui`
The CLI SHALL optionally start the Stage 2 dev server when requested, but MUST keep this off by default.

#### Scenario: Running `flowcode main.py --open-ui`
- Given Node/npm are installed and the repo contains `Archive/stage2`
- When the user runs the command with `--open-ui`
- Then after producing all JSON artifacts, the command spawns `npm run dev --prefix Archive/stage2`
- And the CLI prints a message indicating the dev server has been launched (non-blocking child process or foreground based on implementation simplicity).

### Requirement: Model selection with sensible defaults
The CLI SHALL allow specifying models for Stage 1 and Stage 2, with defaults set to `gpt-5` and `gpt-5-nano` respectively.

#### Scenario: Using defaults
- Given the user does not pass model flags
- When the CLI runs Stage 1 and Stage 2
- Then Stage 1 uses model `gpt-5`
- And Stage 2 uses model `gpt-5-nano`.

#### Scenario: Overriding models
- Given the user passes `--model-stage1 <m1>` and/or `--model-stage2 <m2>`
- When the CLI runs Stage 1 and Stage 2
- Then the respective sub-steps are invoked with `--model <m1>` and `--model <m2>`
- And outputs are produced as usual.

### Requirement: Friendly environment key handling
The CLI SHALL attempt to discover the OpenAI API key and provide actionable errors when missing.

#### Scenario: `.env` without `OPENAI_API_KEY=` line
- Given the environment variable `OPENAI_API_KEY` is not set
- And a `.env` file exists in the repo root but contains an `api:` style key on the next line
- When the user runs `flowcode somefile`
- Then the CLI extracts a value that looks like an OpenAI key and sets `OPENAI_API_KEY` for the subprocesses
- And continues execution normally.
