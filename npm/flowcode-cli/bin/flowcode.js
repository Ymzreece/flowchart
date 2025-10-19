#!/usr/bin/env node
/*
  Thin Node wrapper for the Flowcode Python CLI.
  It tries, in order:
    1) a globally available `flowcode` (e.g., installed via pipx)
    2) `python3 -m flowcode_renderer.orchestrator`
    3) `python -m flowcode_renderer.orchestrator`
  If all fail, it prints guidance to install the Python package with pipx.
*/

const { spawn } = require("node:child_process");

const args = process.argv.slice(2);

function run(cmd, cmdArgs) {
  return new Promise((resolve, reject) => {
    const p = spawn(cmd, cmdArgs, { stdio: "inherit" });
    p.on("error", (err) => reject(err));
    p.on("exit", (code) => {
      if (code === 0) resolve(0);
      else reject(code ?? 1);
    });
  });
}

(async () => {
  try {
    await run("flowcode", args);
    return;
  } catch (e1) {}

  try {
    await run("python3", ["-m", "flowcode_renderer.orchestrator", ...args]);
    return;
  } catch (e2) {}

  try {
    await run("python", ["-m", "flowcode_renderer.orchestrator", ...args]);
    return;
  } catch (e3) {}

  console.error(
    "flowcode CLI not found. Install the Python CLI first:\n" +
      "  pipx install \"git+https://github.com/<your-username>/<repo>.git#subdirectory=flowcode_2\"\n\n" +
      "Then rerun: flowcode " + args.join(" ")
  );
  process.exit(1);
})();

