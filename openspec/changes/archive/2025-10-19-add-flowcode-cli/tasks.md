# Tasks — Add End-to-End `flowcode` CLI

# Tasks — Add End-to-End `flowcode` CLI

<!-- OPENSPEC:START -->
**Guardrails**
- Favor straightforward, minimal implementations first and add complexity only when it is requested or clearly required.
- Keep changes tightly scoped to the requested outcome.
- Refer to `openspec/AGENTS.md` (located inside the `openspec/` directory—run `ls openspec` or `openspec update` if you don't see it) if you need additional OpenSpec conventions or clarifications.

**Steps**
Track these steps as TODOs and complete them one by one.
1. Read `changes/<id>/proposal.md`, `design.md` (if present), and `tasks.md` to confirm scope and acceptance criteria.
2. Work through tasks sequentially, keeping edits minimal and focused on the requested change.
3. Confirm completion before updating statuses—make sure every item in `tasks.md` is finished.
4. Update the checklist after all work is done so each task is marked `- [x]` and reflects reality.
5. Reference `openspec list` or `openspec show <item>` when additional context is required.

**Reference**
- Use `openspec show <id> --json --deltas-only` if you need additional context from the proposal while implementing.
<!-- OPENSPEC:END -->

 - [x] Scaffold change under `openspec/changes/add-flowcode-cli/` with proposal, tasks, and spec.
 - [x] Implement root-level `flowcode` Python script orchestrating Steps 1–3.
 - [x] Add optional `--open-ui` flag to spawn `npm run dev --prefix Archive/stage2`.
 - [x] Add `--model-stage1` and `--model-stage2` flags, defaulting to `gpt-5` and `gpt-5-nano`.
 - [x] Verify model overrides are passed to Stage 1 and Stage 2.
 - [x] Load `OPENAI_API_KEY` from environment; fallback to `.env` heuristics when unset.
 - [x] Validate outputs exist and print canonical success messages for each step.
 - [x] Run `openspec validate add-flowcode-cli --strict` and fix any issues.
 - [x] Document quick usage in the script `--help`.
