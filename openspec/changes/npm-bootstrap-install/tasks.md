# Tasks — One-Line npm Install

- [x] Add `scripts/postinstall.js` to npm wrapper to bootstrap Python CLI via `pip`.
- [x] Wire `postinstall` in `npm/flowcode-cli/package.json`.
- [x] Fix `npm` wrapper recursion by avoiding calling itself when resolving `flowcode`.
- [x] Print clear guidance on failure, including PATH hints.
- [x] Validate change with `openspec validate npm-bootstrap-install --strict`.
