# Change Proposal — Enable One-Line npm Install

## Problem
Users want to install Flowcode with a single `npm install -g` command. Today, the npm package is just a thin wrapper and requires a separate `pipx install` for the Python CLI.

## Proposal
Add an npm `postinstall` step that bootstraps the Python CLI automatically when possible. The wrapper will:
- Detect an existing Flowcode Python CLI and use it.
- If missing, run `python -m pip install --user` of the Python package from GitHub.
- Print clear guidance if Python or pip are not available.

Also harden the wrapper to avoid self-recursion when a global `flowcode` command points to the wrapper itself.

## Scope
- `npm/flowcode-cli` package:
  - Add `scripts/postinstall.js` to bootstrap the Python CLI.
  - Update `package.json` to run `postinstall`.
  - Fix `bin/flowcode.js` to avoid infinite recursion and prefer the installed Python module when available.
- Documentation note in README about the npm-only path and its assumptions (Python present on the system).

## Out of Scope
- Rewriting the CLI in Node/TypeScript (native implementation). This proposal takes the pragmatic bootstrap path.
- Guaranteeing PATH updates for `pip --user`; show helpful guidance instead.

## Risks & Mitigations
- Missing Python/pip/pipx: show actionable messages with next-step commands.
- Corporate environments blocking postinstall: wrapper still works if the user installs Python CLI manually later.
- PATH not updated for `pip --user`: detect and print the likely bin directory.

## Dependencies
- Requires Python available in the environment for bootstrap (or manual install fallback).
