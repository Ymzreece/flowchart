# npm Install Bootstrap

## ADDED Requirements

### Requirement: Postinstall bootstraps Python CLI
The npm package SHALL attempt to install (or upgrade) the Python Flowcode CLI automatically during `npm install -g`, using Python’s pip only.

#### Scenario: Python is available
- Given `python` or `python3` is on PATH
- When the user runs `npm install -g @ydtech/flowcode`
- Then the `postinstall` script executes `python -m pip install --user <python-package-spec>`
- And prints the likely user bin directory if PATH needs updating.

#### Scenario: Python is not available
- Given neither `python` nor `python3` is on PATH
- When the user runs `npm install -g @ydtech/flowcode`
- Then the script prints clear guidance to install Python and run the pip command manually.

### Requirement: Wrapper avoids self-recursion
The `flowcode` Node wrapper SHALL avoid calling itself recursively when attempting to delegate to a `flowcode` binary.

#### Scenario: Only the npm wrapper is installed
- Given the global `flowcode` points to the wrapper’s own JS file
- When the wrapper resolves `flowcode` in PATH
- Then it detects the same file path and skips delegating to avoid recursion
- And it falls back to running `python -m flowcode_renderer.orchestrator` when available.
