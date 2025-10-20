#!/usr/bin/env node
/*
  Thin Node wrapper for the Flowcode Python CLI.
  It tries, in order:
    1) a globally available `flowcode` (e.g., installed via pipx)
    2) `python3 -m flowcode_renderer.orchestrator`
    3) `python -m flowcode_renderer.orchestrator`
  If all fail, it prints guidance to install the Python package with pipx.
*/

const { spawn, spawnSync } = require("node:child_process");
const path = require("node:path");

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
  // Try delegating to an existing 'flowcode' if it's not this wrapper (avoid recursion)
  try {
    const whichCmd = process.platform === "win32" ? "where" : "command";
    const whichArgs = process.platform === "win32" ? ["flowcode"] : ["-v", "flowcode"];
    const found = spawnSync(whichCmd, whichArgs, { stdio: "pipe" });
    if (found.status === 0) {
      const resolved = (() => {
        const out = (found.stdout || Buffer.from(""))
          .toString()
          .split(/\r?\n/)
          .filter(Boolean)[0] || "";
        return out.trim();
      })();
      const selfPath = path.resolve(process.argv[1]);
      if (resolved && path.resolve(resolved) !== selfPath) {
        await run("flowcode", args);
        return;
      }
    }
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
      "  python -m pip install --user \"git+https://github.com/Ymzreece/flowchart.git#subdirectory=flowcode_2\"\n\n" +
      "Then rerun: flowcode " + args.join(" ")
  );
  process.exit(1);
})();
