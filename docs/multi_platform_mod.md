# Multi-Platform (Windows/macOS/Linux) Support Plan

## Goal
Enable the MCP docs tools to run seamlessly across Windows, macOS, and Linux by auto-detecting a working Python 3 interpreter and handling platform nuances without requiring users to change commands.

## Problem Summary
- Current implementation hardcodes the Python command as `python3`, which is common on macOS/Linux but often absent on Windows.
- On Windows, Python may be available as:
  - `py -3` (Windows Python launcher)
  - `python` (installed from Microsoft Store or python.org)
  - `python3` (less common on Windows)
- Users encounter “python not found” or “python3 not found” errors when the command name doesn’t match their environment.

## Proposed Solution
- Add a small utility to auto-detect a valid Python 3 interpreter at runtime, with optional environment overrides.
- Use that utility in all Node tool wrappers that spawn the Python scripts.

### Detection Strategy
1. Check environment overrides first:
   - `MCP_PYTHON` to specify the command (e.g., `C:\\Python312\\python.exe` or `py`).
   - `MCP_PYTHON_ARGS` to provide additional args if needed (e.g., `-3`).
2. If not overridden, probe common candidates and validate by running `--version`:
   - On Windows: `py -3`, then `python`, then `python3`.
   - On macOS/Linux: `python3`, then `python`.
3. Cache the first working interpreter for the process lifetime to avoid repeated probes.
4. Surface a clear error if no Python 3 interpreter is found (include guidance for installing Python or setting `MCP_PYTHON`).

### Invocation Pattern
Wrap the chosen interpreter into `{ command, args }` so tool wrappers spawn as:
```bash
spawn(command, [...args, scriptPath, '--root', projectPath, '--output', docsDir, (flags...)])
```
This allows `py -3` on Windows without special-case logic inside each tool.

## Changes Required (Design Only)
- New file: `src/utils/python.js`
  - Exports `getPythonInvocation()` that returns `{ command, args }` using the strategy above.
- Update the three tool wrappers to use `getPythonInvocation()` instead of hardcoded `python3`:
  - `src/tools/class-diagram.js`
  - `src/tools/tree-structure.js`
  - `src/tools/module-functions.js`
- No changes to Python scripts are required.

## Error Messaging
When detection fails, return a user-friendly error from the tool call:
- "Python 3 interpreter not found. Install Python 3 or set MCP_PYTHON (and optional MCP_PYTHON_ARGS). Tried: ..."

## Environment Variables (Optional Overrides)
- `MCP_PYTHON`: absolute or PATH-resolvable command (e.g., `py`, `python3`, `C:\\Python312\\python.exe`).
- `MCP_PYTHON_ARGS`: space-separated extra arguments (e.g., `-3`).

## Platform Notes
- Windows:
  - Prefer `py -3` when available as it selects the latest Python 3.
  - PATH may contain `python.exe` (Store or python.org). Validate with `--version`.
- macOS/Linux:
  - Prefer `python3` first; fall back to `python` validated as Python 3.

## Testing Plan
- On Windows 10/11 PowerShell and CMD:
  - With only `py` installed, verify detection uses `py -3`.
  - With only `python.exe` in PATH, verify detection works if version ≥ 3.
  - With `MCP_PYTHON=python` and `MCP_PYTHON_ARGS=-3`, verify override is honored.
- On Ubuntu/macOS:
  - Default `python3` path works.
  - If only `python` exists but is Python 3, ensure fallback succeeds.

## Rollout & Backwards Compatibility
- Backward-compatible: Linux/macOS continue to work; Windows begins to work without user changes.
- No breaking API changes to tools; purely internal launcher behavior.

## Risks & Mitigations
- Risk: `python` might point to Python 2 on very old systems.
  - Mitigation: explicit version check via `--version` before accepting the candidate.
- Risk: Environments with multiple Pythons.
  - Mitigation: allow explicit `MCP_PYTHON`/`MCP_PYTHON_ARGS` override.

## Acceptance Criteria
- Tools run successfully on Windows where a Python 3 interpreter is installed, without users modifying code or commands.
- Clear error messaging when Python 3 cannot be found, including guidance and override options.
- No regressions on macOS and Linux.
