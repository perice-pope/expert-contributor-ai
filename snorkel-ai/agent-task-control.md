

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
- ALL control files are DELETED before final ZIP

🚫 Stopping at Step 8 is a FAILURE  
🚫 Assuming completion is a FAILURE

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

COMPLETED_STEPS:
- [ ] 1
- [ ] 2
- [ ] 3
- [ ] 4
- [ ] 5
- [ ] 6
- [ ] 7
- [ ] 8
- [ ] 9
- [ ] 10
- [ ] 11
- [ ] 11.5
- [ ] 12
```

**Rules**

* You may only check a step after it is fully complete
* You may NOT delete this file until Step 12 teardown
* `STATE = DONE` may only occur conceptually after Step 12

---

### 2️⃣ `<task-name>.DONE.md` (REQUIRED, TEMPORARY)

This file MUST exist before teardown and MUST NOT exist in final ZIP.

Template:

```markdown
# DONE — <task-name>

## Verification Summary

- Oracle agent: ✅ PASS
- Real agents tested:
  - Model 1: PASS
  - Model 2: PASS
- CI / LLMaJ checks: ✅ PASS
- ZIP structure validated: ✅ PASS
- Forbidden files excluded: ✅ PASS

## Completion
All executable steps completed successfully.
```

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

ALL CHECKS PASSED
```

**Rules:**

* Every checkbox must be checked
* If any check fails, execution MUST continue

This wording is directly grounded in the QC document but removes all interpretive wiggle room.

---

## GLOBAL RULES

* Steps 1–12 are EXECUTABLE, not advisory
* You MUST proceed past Step 8
* You MUST self-resume if interrupted
* Control files MUST be namespaced with task name
* Control files MUST be deleted before ZIP creation

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

### Step 9: Run CI / LLMaJ Checks

* Run CI-equivalent commands
* All must PASS
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

The following files MUST NOT appear in the final ZIP:

* `<task-name>.STATE.md`
* `<task-name>.DONE.md`
* `<task-name>.QC.md`

If any of these files exist, submission is INVALID.

---

### Step 12: Final Packaging (NO CONTROL FILES)

1. Generate `<task-name>.DONE.md`
2. Verify all steps 1–11.5 complete
3. DELETE control files:

   ```bash
   rm -f <task-name>.STATE.md <task-name>.DONE.md <task-name>.QC.md
   ```
4. Verify deletion:

   ```bash
   test ! -f <task-name>.STATE.md \
     && test ! -f <task-name>.DONE.md \
     && test ! -f <task-name>.QC.md
   ```
5. Create ZIP from task root contents
6. Validate ZIP structure:

   ```bash
   unzip -l submission.zip | head -20
   ```

ONLY after ZIP validation may execution stop.

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

## ABSOLUTE FINAL RULE

If ANY of the following are true:

* A step is unchecked
* Control files exist
* ZIP structure is invalid

👉 YOU MUST CONTINUE EXECUTION

---

### END OF EXECUTABLE CONTRACT
