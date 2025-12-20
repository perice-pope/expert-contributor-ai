

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

🚫 Generic names like `STATE.md` or `DONE.md` are FORBIDDEN.

---

## COMPLETION CONTRACT (MANDATORY)

You are **NOT finished** until ALL of the following are true:

- `<task-name>.STATE.md` exists AND all steps 1–12 are checked
- `<task-name>.DONE.md` exists AND is fully populated
- Oracle agent passes
- Real agents tested (≥ 2 distinct models)
- CI / LLMaJ checks executed
- ZIP structure validated
- ALL control files are DELETED before final ZIP

🚫 Stopping at Step 8 is a FAILURE  
🚫 Assuming completion is a FAILURE

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

## CONTROL FILE TEARDOWN (MANDATORY)

The following files MUST NOT appear in the final ZIP:

* `<task-name>.STATE.md`
* `<task-name>.DONE.md`

If either file exists, submission is INVALID.

---

### Step 12: Final Packaging (NO CONTROL FILES)

1. Generate `<task-name>.DONE.md`
2. Verify all steps 1–11 complete
3. DELETE control files:

   ```bash
   rm -f <task-name>.STATE.md <task-name>.DONE.md
   ```
4. Verify deletion:

   ```bash
   test ! -f <task-name>.STATE.md && test ! -f <task-name>.DONE.md
   ```
5. Create ZIP from task root contents
6. Validate ZIP structure:

   ```bash
   unzip -l submission.zip | head -20
   ```

ONLY after ZIP validation may execution stop.

---

## ABSOLUTE FINAL RULE

If ANY of the following are true:

* A step is unchecked
* Control files exist
* ZIP structure is invalid

👉 YOU MUST CONTINUE EXECUTION

---

### END OF EXECUTABLE CONTRACT
