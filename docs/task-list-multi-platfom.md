# Task List – Multi-Platform Support (Windows/macOS/Linux)

This document tracks the implementation of cross-platform Python 3 auto-detection and Windows compatibility as described in `docs/multi_platform_mod.md`. Update statuses as work progresses.

## Legend
- Status values: Pending | In Progress | Complete | Blocked
- References use section names from `docs/multi_platform_mod.md` and other docs

## Scope
Enable seamless execution on Windows/macOS/Linux by auto-detecting a valid Python 3 interpreter and integrating it into all tool wrappers, with clear error messaging and optional environment overrides.

## Task Dependencies and Status

| Task ID | Description | Dependencies | Status | Reference |
|---------|-------------|--------------|--------|-----------|
| **PLANNING** |
| MP-0 | Finalize multi-platform design plan | None | Complete | multi_platform_mod.md: Goal, Proposed Solution |
| **IMPLEMENTATION** |
| MP-1 | Implement `src/utils/python.js` with detection + env overrides | MP-0 | Complete | multi_platform_mod.md: Detection Strategy, Invocation Pattern |
| MP-2 | Refactor `src/tools/class-diagram.js` to use detection | MP-1 | Complete | multi_platform_mod.md: Changes Required (Design Only) |
| MP-3 | Refactor `src/tools/tree-structure.js` to use detection | MP-1 | Complete | multi_platform_mod.md: Changes Required (Design Only) |
| MP-4 | Refactor `src/tools/module-functions.js` to use detection | MP-1 | Complete | multi_platform_mod.md: Changes Required (Design Only) |
| MP-5 | Centralize friendly error messaging for missing Python 3 | MP-1 | Complete | multi_platform_mod.md: Error Messaging |
| **TESTING** |
| MT-1 | Manual verification on Windows (PowerShell, CMD): `py -3` present | MP-2, MP-3, MP-4 | Pending | multi_platform_mod.md: Testing Plan |
| MT-2 | Manual verification on Windows with only `python.exe` in PATH | MP-2, MP-3, MP-4 | Pending | multi_platform_mod.md: Testing Plan |
| MT-3 | Manual verification with env overrides (`MCP_PYTHON`, `MCP_PYTHON_ARGS`) | MP-1 | Pending | multi_platform_mod.md: Environment Variables |
| MT-4 | Manual verification on Ubuntu/macOS (default `python3`) | MP-2, MP-3, MP-4 | Pending | multi_platform_mod.md: Testing Plan |
| **DOCUMENTATION** |
| MD-1 | Update README to document env overrides and Windows notes | MP-1 | Complete | multi_platform_mod.md: Environment Variables, Platform Notes |
| MD-2 | Update API.md error handling examples for detection failures | MP-5 | Complete | multi_platform_mod.md: Error Messaging |
| MD-3 | Add link to this task list in `docs/README.md` | None | Complete | Project Docs Index |
| **CHECKPOINTS** |
| C-MP-1 | Cross-platform detection integrated in all tools | MP-2, MP-3, MP-4 | Pending | Acceptance Criteria |
| C-MP-2 | Windows and *nix manual tests pass | MT-1, MT-2, MT-3, MT-4 | Pending | Acceptance Criteria |
| C-MP-3 | Docs updated and released | MD-1, MD-2, MD-3 | Pending | Rollout & Backwards Compatibility |

## Update Rules (apply in commit messages and PRs)
- Start Task: "Update status of task [ID] from 'Pending' to 'In Progress'"
- Complete Task: "Update status of task [ID] from 'In Progress' to 'Complete'"
- Blocked Task: "Update status of task [ID] to 'Blocked' – [reason]"
- Add Sub-Task: "Add sub-task under [PARENT_ID]: | [PARENT_ID].[SUB_NUM] | [DESCRIPTION] | [PARENT_ID] | Pending | [REFERENCE] |"

## Notes & Rationale
- Centralizing detection in `src/utils/python.js` prevents OS-specific logic in each tool wrapper and ensures a single source of truth. See: multi_platform_mod.md: Detection Strategy.
- Environment overrides (`MCP_PYTHON`, `MCP_PYTHON_ARGS`) support complex and multi-install Python environments. See: multi_platform_mod.md: Environment Variables.
- Clear error messages reduce support burden and improve UX when Python 3 is missing. See: multi_platform_mod.md: Error Messaging.

## Acceptance Criteria
- Tools run on Windows with `py -3` or `python.exe` (>= 3.x) without user code changes.
- Tools run on macOS/Ubuntu with `python3`; fallback to `python` only when it’s Python 3.
- Friendly, actionable error is returned when no Python 3 is available.
- README and API docs reflect env overrides and error behavior.

## Quick Links
- Design Plan: `docs/multi_platform_mod.md`
- Main Design Document: `docs/Design.md`
- API Reference: `docs/API.md`
- Docs Index: `docs/README.md`
