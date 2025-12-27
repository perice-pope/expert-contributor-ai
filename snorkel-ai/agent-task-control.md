

---

# Agent Task Control — EXECUTABLE CONTRACT

> ⚠️ THIS FILE IS AN EXECUTION CONTRACT, NOT DOCUMENTATION  
> You MUST follow all rules.  
> You MUST NOT stop early.  
> You MUST NOT ship control files.

---

## TASK IDENTIFIER (MANDATORY)

Before doing ANY work, determine the task name:

- Task name = folder name at task root
- Must be kebab-case (example: `fix-memory-leak-python`)

Use this task name to namespace ALL control files.

### Control files (task-scoped)
- `<task-name>.STATE.md`
- `<task-name>.DONE.md`
- `<task-name>.QC.md`

🚫 Generic names like `STATE.md` or `DONE.md` are FORBIDDEN.

---

## COMPLETION CONTRACT (MANDATORY)

You are **NOT finished** until ALL of the following are true:

- `<task-name>.STATE.md` exists AND all steps 1–12 are checked
- `<task-name>.DONE.md` exists AND is fully populated
- `<task-name>.QC.md` exists AND all QC checks pass
- Oracle agent passes
- Real agents tested (≥ 2 distinct models)
- CI / LLMaJ checks executed
- ZIP structure validated
- Control files (STATE.md, DONE.md, QC.md, NOTES.md) are EXCLUDED from final ZIP

🚫 Stopping at Step 8 is a FAILURE  
🚫 Assuming completion is a FAILURE

---

## LOCK GATES (MANDATORY)

The task progresses through **three phases** with explicit locks:

| Phase | Steps | Lock Condition |
|-------|-------|----------------|
| IMPLEMENTATION | 1-6 | No lock (can proceed freely) |
| VERIFICATION | 4, 7, 8, 9 | 🔒 Each step requires PROOF before [x] |
| PACKAGING | 12 | 🔒 ALL verification steps must show ✅ with evidence |

### Verification Steps Require Proof

These steps CANNOT be marked `[x]` without evidence in STATE.md:

| Step | Proof Required |
|------|----------------|
| 4 | Command output showing interactive session worked |
| 7 | Command output showing `reward.txt = 1` |
| 8 | Run logs for ≥2 models, 2-3 times each, with outcomes |
| 9 | CI check output showing all checks PASS |

### Lock Status Markers

In STATE.md, use these markers:

- `[x]` = Complete WITH evidence documented
- `[~]` = Attempted but needs re-verification (evidence incomplete or suspect)
- `[ ]` = Not started or incomplete
- `[B]` = Blocked on external dependency

🚫 NEVER mark `[x]` on Steps 4, 7, 8, 9 without proof
🚫 NEVER proceed to Step 12 while any verification step shows `[~]` or `[ ]`

---

## Where QC belongs in the flow

Between Step 11 and Step 12

Why:

Step 11 = structure & submission hygiene

QC = semantic + CI correctness

Step 12 = irreversible packaging

This mirrors real CI pipelines.

---

## EXECUTION MODEL (NON-NEGOTIABLE)

You must behave as a **state machine**.

After EVERY action:

1. Read `<task-name>.STATE.md`
2. Find the highest unchecked step
3. Execute ONLY that step
4. Update `<task-name>.STATE.md`
5. Repeat

If execution halts and `<task-name>.STATE.md` exists:
- Resume automatically from the highest incomplete step

---

## REQUIRED CONTROL FILES

### 1️⃣ `<task-name>.STATE.md` (REQUIRED DURING EXECUTION)

Create this file IMMEDIATELY after determining the task name.

```markdown
STATE = INCOMPLETE

---
## VERIFICATION GATE

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Step 4: Interactive test | ⬜ NOT VERIFIED | (paste command + output summary) |
| Step 7: Oracle agent | ⬜ NOT VERIFIED | (paste reward.txt = 1 proof) |
| Step 8: Real agents (Model 1) | ⬜ NOT VERIFIED | (paste run outcome) |
| Step 8: Real agents (Model 2) | ⬜ NOT VERIFIED | (paste run outcome) |
| Step 9: CI checks | ⬜ NOT VERIFIED | (paste all checks PASS) |

🔒 **PACKAGING LOCKED** — Step 12 blocked until ALL show ✅ VERIFIED

---
## COMPLETED STEPS

Legend: [x]=complete with evidence, [~]=needs re-verification, [ ]=incomplete, [B]=blocked

### Implementation (no lock)
- [ ] 1 - Extract and Rename
- [ ] 2 - Write Instructions and Configuration
- [ ] 3 - Configure Docker Environment
- [ ] 5 - Create Solution File
- [ ] 6 - Write Tests

### Verification (requires proof)
- [ ] 4 - Local Interactive Test
- [ ] 7 - Run Oracle Agent
- [ ] 8 - Test With Real Agents
- [ ] 9 - Run CI / LLMaJ Checks

### Validation
- [ ] 10 - Final Verification
- [ ] 11 - Pre-Submission Validation
- [ ] 11.5 - Quality Control Gate

### Packaging (locked until verification complete)
- [ ] 12 - Final Packaging

---
## ISSUE LOG

| # | Date | Issue | Action Taken | Assumption |
|---|------|-------|--------------|------------|

---
## NEXT ACTION

(Current step and what needs to be done)
```

**Rules**

* You may only check a step after it is fully complete WITH EVIDENCE for verification steps
* You may NOT delete this file (it remains in development directory but is excluded from ZIP)
* `STATE = DONE` may only occur after Step 12 AND all verification gates show ✅

**⚠️ VERIFICATION GATE RULES (MANDATORY):**
* Steps 4, 7, 8, 9 require PROOF in the VERIFICATION GATE table
* Update the table with actual evidence when steps complete
* Status must change from ⬜ to ✅ only when proof is documented
* PACKAGING LOCKED message remains until all gates are ✅

**⚠️ COMPLETION CRITERIA (MANDATORY):**
* Step 4: Interactive test MUST work (environment behaves correctly)
* Step 7: Oracle agent MUST PASS (reward.txt = "1", not "0")
* Step 8: MUST run ≥2 models, 2-3 times each, record all outcomes
* Step 9: CI checks MUST PASS (all checks pass, not just "attempted")
* Step 12: Can ONLY be marked complete after ALL steps 1-11.5 are [x]

🚫 DO NOT mark [x] if:
- Step failed or had errors
- Tests didn't pass (reward = 0)
- Required runs/models weren't completed
- Description says "needs verification", "pending", or "attempted"
- VERIFICATION GATE still shows ⬜ for that step

---

### 2️⃣ `<task-name>.DONE.md` (REQUIRED, TEMPORARY)

This file MUST exist before teardown and MUST NOT exist in final ZIP.

**Purpose:** Track verification status and final completion. This file is named DONE.md but the task is NOT done until it says so explicitly.

Template:

```markdown
# DONE — <task-name>

## ❌ TASK COMPLETE: NO
<!-- Change to ✅ TASK COMPLETE: YES only when ALL gates are unlocked -->

| Final Gate | Status |
|------------|--------|
| All verification steps passed | 🔒 LOCKED |
| ZIP package created | 🔒 LOCKED |

**Reason:** (describe current blocker)

---

## Verification Summary

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Oracle agent | ⬜ PENDING | (not yet run) |
| Real agent: Model 1 | ⬜ PENDING | (not yet run) |
| Real agent: Model 2 | ⬜ PENDING | (not yet run) |
| CI / LLMaJ checks | ⬜ PENDING | (not yet run) |
| ZIP structure validated | ⬜ PENDING | (not yet created) |
| Forbidden files excluded | ⬜ PENDING | (not yet verified) |

---

## Implementation Summary

(Brief description of what was built)

---

## Next Steps

(What needs to happen to unlock the gates)
```

**Rules:**
* Header must show ❌ TASK COMPLETE: NO until truly complete
* Only change to ✅ TASK COMPLETE: YES after Step 12 packaging succeeds
* Each verification item must show actual evidence, not just ✅
* If blocked, document the blocker explicitly

---

### 3️⃣ `<task-name>.QC.md` (REQUIRED, TEMPORARY)

This file records completion of the official Quality Control checklist.

This file MUST exist before final packaging  
This file MUST NOT exist in the final ZIP

Template:

```markdown
# Quality Control — <task-name>

## Manual Review Readiness

- [ ] Oracle correctness verified  
  (Oracle solution produces correct output and aligns with task intent)

- [ ] Prompt clarity verified  
  (All required behavior is explicitly stated in instruction.md)

- [ ] Environment correctness verified  
  (Dockerfile builds and runtime behavior matches task assumptions)

- [ ] Tags reviewed and accurate  
  (task.toml metadata accurately reflects task content)

---

## CI / Evaluation Checks

- [ ] behavior_in_task_description  
  (EVERY behavior checked by tests is explicitly described in instruction.md)

- [ ] behavior_in_tests  
  (EVERY behavior described in instruction.md is exercised by tests)

- [ ] informative_test_docstrings  
  (Each test clearly states what behavior it validates)

- [ ] anti_cheating_measures  
  (Agent cannot trivially bypass task by reading files, hardcoding outputs, or inspecting solutions)

- [ ] structured_data_schema (if applicable)  
  (Exact schema is documented in task.yaml or an explicitly referenced file)

- [ ] pinned_dependencies  
  (All non-apt dependencies are version pinned)

- [ ] typos  
  (No typos in filenames, variables, paths, or instructions)

- [ ] tests_or_solution_in_image  
  (tests/ and solution files are NOT copied into the Docker image)

- [ ] test_deps_in_image  
  (Test-only dependencies are installed at test time, not build time)

- [ ] hardcoded_solution  
  (Solution derives results via computation, not direct echo/cat of final answers)

- [ ] file_reference_mentioned  
  (All files referenced in tests are mentioned in task instructions)

- [ ] check_canary  
  (Required canary string exists at top of all required files)

- [ ] check_dockerfile_references  
  (Dockerfile does NOT reference forbidden files)

- [ ] check_run-tests_sh  
  (run-tests.sh uses uv init / uv venv or task.yaml declares system-wide scope)

- [ ] check_task_absolute_path  
  (Instructions use absolute paths, not relative ones)

- [ ] check_test_file_references  
  (Files referenced in tests are declared in task.yaml)

- [ ] check_files  
  (No extraneous files exist outside the task directory)

- [ ] check_privileged_containers  
  (No privileged containers are used)

- [ ] check_task_sizes  
  (All files are under 1MB)

- [ ] validate_task_fields  
  (All required task.yaml fields are present and valid)

---

## Result

### Code Quality Checks: ⬜ PENDING
<!-- Change to ✅ ALL PASSED only when every box above is checked -->

⚠️ **SCOPE NOTICE:** QC checks validate code quality and structure.
They do NOT replace verification steps (4, 7, 8, 9) which require actual execution proof.

See `<task-name>.STATE.md` VERIFICATION GATE for execution status.
```

**Rules:**

* Every checkbox must be checked before marking "ALL PASSED"
* If any check fails, execution MUST continue (fix and re-check)
* QC passing does NOT mean the task is complete — verification steps still required
* Do NOT claim "ready for submission" while STATE.md verification gates are locked

This wording is directly grounded in the QC document but removes all interpretive wiggle room.

---

## AUTONOMOUS CONTINUATION (MANDATORY)

### Default Behavior: ACT → LOG → CONTINUE

When encountering issues during execution:

1. **If the fix is obvious** → Fix it immediately
2. **Log the issue** → Add to ISSUE LOG in STATE.md
3. **Continue working** → Move to the next actionable item

### DO NOT Stop To Ask

❌ "Should I fix this error?"  
❌ "Do you want me to continue?"  
❌ "Is this the right approach?"

✅ Fix the error, log it, continue  
✅ Make the reasonable choice, log it, continue  
✅ Document assumptions, continue

### Only Stop When

- Required credentials/API keys are missing
- External access (harbor, network) is unavailable
- Ambiguous choice with significant, irreversible impact
- Human approval is explicitly required by contract

### When Blocked on External Resources

If a verification step requires external resources (API keys, harbor access, etc.):

1. Mark the step `[B]` (blocked) in STATE.md
2. Update VERIFICATION GATE to show ❌ NOT VERIFIED with reason
3. Complete ALL other steps that can be done locally
4. Document exactly what command/resource is needed to unblock
5. Update NEXT ACTION with clear instructions for resumption

Do NOT:
- Mark verification steps `[x]` without actual proof
- Claim the task is "ready for submission" while blocked
- Create the final ZIP while verification gates are locked

### Non-Blocking Issue Log

Add this section to STATE.md and USE IT:

```markdown
## ISSUE LOG

| # | Date | Issue | Action Taken | Assumption |
|---|------|-------|--------------|------------|
| 1 | YYYY-MM-DD | Description | What was done | Why (if not obvious) |
```

Every autonomous fix MUST be logged. This creates an audit trail without stopping work.

---

## GLOBAL RULES

* Steps 1–12 are EXECUTABLE, not advisory
* You MUST proceed past Step 8
* You MUST self-resume if interrupted
* Control files MUST be namespaced with task name
* Control files (STATE.md, DONE.md, QC.md, NOTES.md) MUST be excluded from ZIP creation
* You MUST log issues and continue, not stop to ask

---

## LOCAL TESTING STRATEGY (QUICK REFERENCE)

Before submitting to CI, run these tests locally in order:

| Phase | Command | What It Validates | Pass Criteria |
|-------|---------|-------------------|---------------|
| 1. Build | `harbor tasks start-env <task>` | Docker builds correctly | No build errors |
| 2. Oracle | `harbor run -a oracle -p <task>` | Solution passes all tests | reward = 1 |
| 3. NOP | `harbor run -a nop -p <task>` | Task isn't trivially solvable | reward = 0 |
| 4. Quality | `harbor tasks check -m openai/gpt-4o <task>` | CI quality checks pass | All checks pass |
| 5. Agents | `harbor run -a claude-code -m anthropic/claude-sonnet-4-5-20250929 -k 3 -n 1 <task>` | Difficulty assessment | 40-70% for MEDIUM |

### Quick Commands

```bash
# Phase 1: Build
harbor tasks start-env harbor_tasks/<task-name>

# Phase 2: Oracle (solution works)
harbor run -a oracle -p harbor_tasks/<task-name>

# Phase 3: NOP (correctly fails)
harbor run -a nop -p harbor_tasks/<task-name>

# Phase 4: Quality checks (CRITICAL - run before agents!)
harbor tasks check -m openai/gpt-4o harbor_tasks/<task-name>

# Phase 5: Agent difficulty (Claude)
harbor run -a claude-code -m anthropic/claude-sonnet-4-5-20250929 -p harbor_tasks/<task-name> -k 3 -n 1

# Phase 5: Agent difficulty (Codex)
harbor run -a codex -m openai/gpt-5 -p harbor_tasks/<task-name> -k 3 -n 1
```

### Difficulty Targets

| Classification | Combined Agent Success Rate |
|----------------|----------------------------|
| TRIVIAL | > 90% (too easy, revise) |
| EASY | 70-90% |
| MEDIUM | 40-70% ← Target |
| HARD | 20-40% |
| VERY HARD | < 20% |

---

## STEP-BY-STEP EXECUTION

---

### Step 1: Extract and Rename

* Copy `template-task`
* Rename to kebab-case task name
* Verify folder name matches task name
* Mark Step 1 complete

---

### Step 2: Write Task Instructions and Configuration

* Fully define requirements in this `instruction.md`
* Configure `task.toml`
* Validate:

  * category is valid
  * difficulty is valid
* Mark Step 2 complete

---

### Step 3: Configure Docker Environment

* Edit `environment/Dockerfile`
* Pin dependencies
* DO NOT copy `solution/` or `tests/` into image
* Build succeeds locally
* Mark Step 3 complete

---

### Step 4: Local Interactive Test

```bash
harbor run --agent oracle --path harbor_tasks/<task-name> --interactive
```

* Environment behaves correctly
* Mark Step 4 complete

---

### Step 5: Create Solution File

* Create `solution/solve.sh`
* Deterministic
* Human-authored
* Executable
* Mark Step 5 complete

---

### Step 6: Write Tests

* Create `tests/test.sh`
* pytest MUST use `-rA`
* Must write `/logs/verifier/reward.txt`
* Mark Step 6 complete

---

### Step 7: Run Oracle Agent

```bash
harbor run --agent oracle --path harbor_tasks/<task-name>
```

* Must PASS
* Fix failures until pass
* Mark Step 7 complete

---

### Step 8: Test With Real Agents (NOT FINAL)

Run ≥ 2 models, 2–3 times each.

Examples:

```bash
harbor run -a terminus-2 -m gpt-4o -p <task-name>
harbor run -a terminus-2 -m anthropic/claude-3-5-sonnet-20240620 -p <task-name>
```

* Record outcomes
* Mark Step 8 complete
* IMMEDIATELY proceed to Step 9

---

### Step 9: Run CI / LLMaJ Checks (LOCAL QUALITY CHECKS)

Run the **exact same quality checks** that CI will run:

```bash
# Run quality checks locally (uses LLM to evaluate)
harbor tasks check -m openai/gpt-4o harbor_tasks/<task-name>

# Or with output file for detailed results
harbor tasks check -m openai/gpt-4o -o quality-results.json harbor_tasks/<task-name>
```

**Key checks that must pass:**
- `behavior_in_instruction` - Tests only assert behaviors stated in instruction.md
- `behavior_in_tests` - All instruction requirements have corresponding tests
- `informative_test_docstrings` - Every test has a docstring
- `anti_cheating_measures` - Agent can't trivially bypass
- `structured_data_schema` - Output formats documented
- `pinned_dependencies` - All versions pinned
- `file_reference_mentioned` - Test file paths in instructions

If any check fails, fix it before proceeding.

* Run `harbor tasks check`
* All checks must PASS
* Mark Step 9 complete

---

### Step 10: Final Verification

Confirm:

* Oracle passes
* CI passes
* Real agents tested
* All required files present

Mark Step 10 complete

---

### Step 11: Pre-Submission Validation

* Validate `task.toml`
* Validate test flags
* Validate forbidden files
* Validate file structure

Mark Step 11 complete

---

### Step 11.5: Quality Control Gate (MANDATORY)

1. Create `<task-name>.QC.md`
2. Evaluate ALL Quality Control checks listed
3. Fix any failures
4. Check ALL boxes in `<task-name>.QC.md`
5. Verify the file exists and is complete

If `<task-name>.QC.md` is incomplete:
- DO NOT proceed
- Continue execution until resolved

This prevents silent skipping.

---

## CONTROL FILE TEARDOWN (MANDATORY)

The following files MUST NOT appear in the final ZIP (development/maintainer files):

* `<task-name>.DONE.md` (temporary control file)
* `<task-name>.QC.md` (temporary control file)
* `<task-name>.STATE.md` (development progress tracking)
* `NOTES.md` (maintainer documentation)

**Note:** These files should remain in the development directory but be excluded from the submission ZIP.

**Required files that MUST be included:**
* `instruction.md` (task instructions)
* `task.toml` (task configuration)
* `app/`, `solution/`, `tests/`, `environment/` directories

If any of the forbidden files exist in the ZIP, submission is INVALID.

---

### Step 12: Final Packaging (NO CONTROL FILES)

1. Generate `<task-name>.DONE.md`
2. Verify all steps 1–11.5 complete
3. DELETE temporary control files (keep STATE.md and NOTES.md for development):

   ```bash
   rm -f <task-name>.DONE.md <task-name>.QC.md
   ```
4. Verify deletion:

   ```bash
   test ! -f <task-name>.DONE.md \
     && test ! -f <task-name>.QC.md
   ```
5. **DELETE ALL EXISTING ZIP FILES** (prevent multiple ZIPs):

   ```bash
   # Delete any existing ZIPs for this task (in task dir, parent dir, or anywhere)
   find . -name "<task-name>*.zip" -type f -delete
   find .. -maxdepth 1 -name "<task-name>*.zip" -type f -delete
   ```
6. Verify no ZIPs exist:

   ```bash
   test ! -f <task-name>.zip \
     && test ! -f <task-name>-submission.zip \
     && test ! -f ../<task-name>.zip \
     && test ! -f ../<task-name>-submission.zip
   ```
7. Create ZIP from task root contents, excluding development files:

   ```bash
   # ZIP must have files at ROOT level (not nested in directory)
   # CI expects: task.toml, instruction.md, app/, tests/, etc. at root
   cd <task-name>
   zip -r ../<task-name>-submission.zip . \
     -x "*.pyc" -x "*__pycache__*" -x "*.DS_Store" \
     -x "*.pytest_cache*" \
     -x "NOTES.md" \
     -x "*.STATE.md" \
     -x "*.DONE.md" \
     -x "*.QC.md" \
     -x "*.zip"
   cd ..
   ```
8. Verify ONLY ONE ZIP exists:

   ```bash
   # Should find exactly one ZIP file
   ZIP_COUNT=$(find .. -maxdepth 1 -name "<task-name>*.zip" -type f | wc -l)
   test "$ZIP_COUNT" -eq 1 || (echo "ERROR: Found $ZIP_COUNT ZIP files, expected 1" && exit 1)
   ```
9. Validate ZIP structure:

   ```bash
   unzip -l <task-name>-submission.zip | head -20
   # Verify no forbidden files
   unzip -l <task-name>-submission.zip | grep -E "(NOTES|STATE|DONE|QC|__pycache__|\.pytest_cache|\.pyc)" && exit 1 || echo "✓ No forbidden files"
   ```

ONLY after ZIP validation and single-ZIP verification may execution stop.

---

## Why this will NOT skip steps again

Because now:

QC is:

* A state-gated step
* A file-verified artifact
* A hard dependency of ZIP creation

The agent cannot reach Step 12 without QC passing

The QC file cannot leak into the ZIP

Restarting the agent resumes cleanly at QC if interrupted

This is exactly how production CI gates are modeled.

---

## Final mental model

You now have three execution layers:

1. Build & test pipeline (Steps 1–11)
2. Semantic + CI correctness gate (QC)
3. Immutable packaging (Step 12)

Agents are good at work.  
They are bad at "remembering to double-check".

You didn't ask them to remember.  
You forced them.

---

## INFRASTRUCTURE TROUBLESHOOTING

### Harbor RewardFileNotFoundError - Volume Mount Issue

**Symptoms:**
- All tests pass but Harbor reports `RewardFileNotFoundError`
- `test-stdout.txt` exists in verifier directory but `reward.txt` and `ctrf.json` do not
- Files exist inside container (`/logs/verifier/reward.txt`) but not on host filesystem

**Root Cause:**
Harbor CLI runs inside Docker (via shim) and mounts `${PWD}:/workspace`. When Harbor tells task containers to mount volumes at `/workspace/jobs/.../verifier`, Docker looks for `/workspace` on the **actual host filesystem**. If `/workspace` is a separate directory (not symlinked to Harbor workspace), volume mounts fail silently.

**Fix:**
```bash
# Create symlink so /workspace points to Harbor workspace
sudo rm -rf /workspace
sudo ln -s /home/perice09/workspace/snorkel-ai /workspace
```

**Verification:**
```bash
ls -la /workspace  # Should show symlink
cd /home/perice09/workspace/snorkel-ai
harbor run --agent oracle --path <task-name>
# Check: ls -la /workspace/jobs/*/<task-name>__*/verifier/reward.txt
```

**Additional Fix for CI Checks:**
Edit `/home/perice09/.local/bin/harbor` to pass API keys:
```bash
-e OPENAI_API_KEY="${OPENAI_API_KEY:-}" \
-e ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-}" \
-e OPENAI_BASE_URL="${OPENAI_BASE_URL:-}" \
```

**When to Check:**
- `RewardFileNotFoundError` despite tests passing
- After Harbor Docker image rebuilds
- On new machines or after system updates

---

## ABSOLUTE FINAL RULE

If ANY of the following are true:

* A step is unchecked
* Forbidden control files exist (DONE.md or QC.md)
* ZIP structure is invalid

👉 YOU MUST CONTINUE EXECUTION

---

### END OF EXECUTABLE CONTRACT
