# Tasks: Lite CLI Command Group

## Phase 1: Setup

- [x] T001 Create `hermes_cli/lite_cmd.py` with module docstring and `cmd_lite` dispatch
- [x] T002 Create `hermes_cli/logs_lite.py` with argument parser and query engine
- [x] T003 Verify `hermes_cli/main.py` integration point; add `cmd_lite` function
- [x] T004 Verify `hermes_cli/lite_config.py` exposes `load_lite_config()`
- [x] T005 Add `lite` to `_BUILTIN_SUBCOMMANDS` in `main.py`

## Phase 2: Foundational

- [x] T006 Implement `lite logs` subcommand with `--stream`, `--since`, `--tail`, `--grep`
- [x] T007 Implement `lite logs --export` and `--exclude` flags
- [x] T008 Implement `lite workspaces` subcommand
- [x] T009 Implement `lite profiles` subcommand
- [x] T010 Implement `lite doctor` subcommand delegating to `DoctorLite`

## Phase 3: Integration

- [x] T011 Register `lite` subparser in `hermes_cli/main.py`
- [x] T012 Verify `hermes lite --help` shows all four subcommands
- [x] T013 Verify `hermes lite logs --stream agent` produces valid JSON lines
- [x] T014 Verify `hermes lite doctor` completes without ImportError

## Phase 4: Polish

- [x] T015 Run `py_compile` on all new Python files
- [x] T016 Update `specs/007-lite-cli-ux/` status to Complete
