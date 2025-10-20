#!/usr/bin/env node
// Best-effort bootstrap to install the Python CLI during `npm install -g`.
// Tries pipx first, then falls back to `python -m pip --user`.

const { spawnSync } = require("node:child_process");
const os = require("node:os");

const PYTHON_SPEC = "git+https://github.com/Ymzreece/flowchart.git#subdirectory=flowcode_2";

function run(cmd, args, opts = {}) {
  const res = spawnSync(cmd, args, { stdio: "inherit", ...opts });
  return res.status === 0;
}

function which(cmd) {
  const tool = process.platform === "win32" ? "where" : "command";
  const args = process.platform === "win32" ? [cmd] : ["-v", cmd];
  const res = spawnSync(tool, args, { stdio: "pipe" });
  return res.status === 0;
}

function pythonExe() {
  if (which("python3")) return "python3";
  if (which("python")) return "python";
  return null;
}

function alreadyAvailable(py) {
  if (!py) return false;
  const res = spawnSync(py, ["-c", "import flowcode_renderer"], { stdio: "ignore" });
  return res.status === 0;
}

try {
  const py = pythonExe();
  if (alreadyAvailable(py)) {
    console.log("[flowcode] Python CLI appears installed; skipping bootstrap.");
    process.exit(0);
  }

  if (py) {
    console.log("[flowcode] Installing Python CLI via pip --user...");
    if (run(py, ["-m", "pip", "install", "--user", PYTHON_SPEC])) {
      const hint = process.platform === "win32"
        ? "%USERPROFILE%\\AppData\\Roaming\\Python\\PythonXX\\Scripts"
        : "~/.local/bin";
      console.log(
        `\n[flowcode] Installed via pip --user. If 'flowcode' is not found, add ${hint} to your PATH.\n`
      );
      process.exit(0);
    }
  }

  console.warn(
    "[flowcode] Could not bootstrap Python CLI automatically.\n" +
      "Install manually (requires Python):\n  python -m pip install --user \"" + PYTHON_SPEC + "\"\n"
  );
} catch (err) {
  console.warn("[flowcode] postinstall skipped:", err?.message || err);
}
