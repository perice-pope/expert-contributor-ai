#1) recover-pgp-key-from-memory-dump.zip:

## Task Review: `tbench-task`
---
## Review Report: tbench-task

**Status:** ❌ FAIL

**Task Location:** `/root/harbor_tasks/tbench-task`

---

#### Summary

This task requires extracting an OpenPGP private key from a process memory dump, reconstructing it by removing noise lines, importing it into GPG, and decrypting a ciphertext to validate the recovery. The solution uses Python inline scripting to parse the memory dump, extract and clean key blocks by removing noise markers, import the recovered key into GPG, and decrypt the provided ciphertext. The test suite verifies output file creation, key file format correctness, noise removal, GPG import success, and exact plaintext matching.

---

#### Critical Issues ❌

1. **Irrelevant Requirements in Instruction**
   - **File:** `tbench-task/instruction.md` (lines 14-15)
   - **Problem:** The instruction includes requirements about hashing passwords and expiring access tokens that are completely unrelated to the GPG key recovery task and are not tested.

   **Current code:**
   ```markdown
   6. **Hash stored passwords**: If any user credentials are persisted as part of your implementation, store passwords only as hashed values (never plaintext).
   7. **Expire access tokens**: Any issued access tokens must expire after **30 minutes**; expired tokens must be rejected with **401 Unauthorized**.
   ```

   **Required fix:**
   Remove these two requirements entirely. They are copy-pasted from a different task (API/authentication task) and have no relevance to GPG key recovery from memory dumps.

   **Explanation:** These requirements create confusion and represent untested behavior. The task is about memory forensics and GPG operations, not authentication or token management. This is a critical behavior mismatch.

2. **Unnecessary Dependencies in Dockerfile**
   - **File:** `tbench-task/environment/Dockerfile` (lines 17-20)
   - **Problem:** The Dockerfile installs FastAPI, uvicorn, and SQLAlchemy which are never used in the solution or required for the task.

   **Current code:**
   ```dockerfile
   RUN pip3 install --no-cache-dir --break-system-packages \
       fastapi==0.115.5 \
       "uvicorn[standard]==0.32.1" \
       sqlalchemy==2.0.36
   ```

   **Required fix:**
   Remove these lines completely. The task only requires GPG, Python3 (for inline scripts), and system utilities.

   **Explanation:** These packages are never imported or used anywhere in the task. They appear to be copy-pasted from a web API task template and waste build time and image space.

3. **Multi-Container Configuration Without Additional Services**
   - **File:** `tbench-task/task.toml` (lines 9-10)
   - **Problem:** The task is marked as `is_multi_container = true` and `custom_docker_compose = true`, but the docker-compose.yaml only defines a single `main` service with no additional services, networks, or dependencies.

   **Current code:**
   ```toml
   is_multi_container = true
   custom_docker_compose = true
   ```

   **Required fix:**
   Remove these flags from task.toml. This is a single-container task.

   **Explanation:** Multi-container flags should only be used when the task actually requires multiple services (e.g., an API server and client, database, etc.). This task only needs a single container with GPG tools. The docker-compose.yaml contains only a `main` service with no networks, health checks, or dependent services—characteristics of single-container tasks that don't need docker-compose.

4. **Incorrect docker-compose.yaml Context Path**
   - **File:** `tbench-task/environment/docker-compose.yaml` (line 4)
   - **Problem:** The build context uses `${CONTEXT_DIR}/..` which points to the parent directory, when it should point to the environment directory itself.

   **Current code:**
   ```yaml
   build:
     context: ${CONTEXT_DIR}/..
     dockerfile: ${CONTEXT_DIR}/Dockerfile
   ```

   **Required fix:**
   ```yaml
   build:
     context: ${CONTEXT_DIR}
   ```

   **Explanation:** Since this should be a single-container task, docker-compose.yaml should be removed entirely. However, if it were a valid multi-container task, the context path is incorrect. The harness sets `CONTEXT_DIR` to the environment directory, so `${CONTEXT_DIR}/..` would point to the task root, not the build context.

---

#### Warnings ⚠️

1. **Overly Complex docker-compose.yaml for Single Container**
   - **File:** `tbench-task/environment/docker-compose.yaml` (entire file)
   - **Problem:** The task uses docker-compose for a single-container setup when a simple Dockerfile would suffice.

   **Suggested fix:**
   Remove docker-compose.yaml entirely and let the harness use the Dockerfile directly. Single-container tasks don't need docker-compose orchestration.

   **Explanation:** Docker Compose is designed for multi-service applications. Using it for a single container adds unnecessary complexity without benefit. This task has no networks, health checks, service dependencies, or multiple services—all indicators that docker-compose is unnecessary.

---

#### Suggestions 💡

1. **Simplify Memory Dump Parsing**
   - **File:** `tbench-task/solution/solve.sh` (lines 12-51)
   - **Current approach:** Uses inline Python script to parse memory dump and clean noise lines.

   **Rationale:** The current approach is clear and effective. However, could potentially be simplified using shell tools like `grep` and `sed`, though the Python approach is more maintainable for this parsing logic.

2. **Add Test for Memory Dump Integrity**
   - **File:** `tbench-task/tests/test_outputs.py`
   - **Current approach:** Tests verify output files but don't check that the memory dump file was not modified.

   **Suggested improvement:**
   Add a test that verifies the memory dump file checksum or modification time to ensure it wasn't altered, as per the constraint "Do not modify the memory dump file."

   **Rationale:** Would provide stronger validation that the solution follows the stated constraints.

---

#### Overall Assessment

This task has a solid core concept—recovering GPG keys from memory dumps is a realistic forensics scenario—but suffers from critical template contamination and misconfiguration. The irrelevant authentication requirements and unused web framework dependencies suggest the task was created by copying from an API task without proper cleanup.

**Key Strengths:**
- Realistic forensics scenario testing memory analysis and GPG operations
- Comprehensive test coverage of key extraction, format validation, and decryption
- Well-structured solution demonstrating proper noise filtering and key reconstruction

**Key Weaknesses:**
- Copy-pasted irrelevant requirements (password hashing, token expiration) create major confusion
- Unnecessary dependencies (FastAPI, SQLAlchemy, uvicorn) bloat the image
- Incorrectly marked as multi-container when it's clearly single-container
- Docker-compose.yaml configuration issues with context path

**Evaluates:** Memory forensics, data extraction and parsing, GPG/OpenPGP operations, format validation

**Recommendation:** ❌ **REQUIRES REVISION** - Must remove irrelevant requirements, clean up dependencies, and fix multi-container configuration before use.
---
<!-- terminal-bench-2-task-reviewer-end -->


#2) extract-png-flags-lsb.zip
## Task Review: `tbench-task`
---
# Review Report: tbench-task

**Status:** ❌ FAIL

**Task Location:** `/root/harbor_tasks/tbench-task`

---

## Summary

This task requires implementing a simple Go HTTP server that serves static files from the `/static` directory and responds with "Hello, World!" at the root endpoint. The solution creates a basic HTTP server using Go's `net/http` package with proper routing and file serving capabilities. The test suite validates both endpoint responses, status codes, and Content-Type headers to ensure the server behaves correctly.

---

## Critical Issues ❌

1. **Missing Required File: instruction.md**
   - **File:** `tbench-task/` (root directory)
   - **Problem:** The task is missing the required `instruction.md` file. Terminal-Bench 2.0 tasks must have `instruction.md` (not `instructions.md` or `README.md`) containing the task description.

   **Current structure:**
   ```
   tbench-task/
   ├── environment/
   ├── task.toml
   ├── solution/
   └── tests/
   ```

   **Required fix:**
   Create an `instruction.md` file in the root directory with the task description, requirements, and success criteria.

   **Explanation:** The `instruction.md` file is a required component of every Terminal-Bench 2.0 task. It provides agents with the task description and requirements.

2. **Unpinned Go Version in Dockerfile**
   - **File:** `tbench-task/environment/Dockerfile` (line 1)
   - **Problem:** The base image uses `golang:latest` tag instead of a pinned version, which could lead to inconsistent behavior over time.

   **Current code:**
   ```dockerfile
   FROM golang:latest
   ```

   **Required fix:**
   ```dockerfile
   FROM golang:1.21
   ```

   **Explanation:** Using `latest` tags for Docker base images can cause unpredictable behavior as the underlying image changes. Pin to a specific Go version for reproducibility.

3. **Test Script Does Not Write Reward File**
   - **File:** `tbench-task/tests/test.sh` (entire file)
   - **Problem:** The test script exits immediately after checking WORKDIR and never writes to `/logs/verifier/reward.txt`, which is required by the harness.

   **Current code:**
   ```bash
   #!/bin/bash

   # Check if we're in a valid working directory
   if [ "$PWD" = "/" ]; then
       echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile before running this script."
       exit 1
   fi
   ```

   **Required fix:**
   ```bash
   #!/bin/bash

   # Check if we're in a valid working directory
   if [ "$PWD" = "/" ]; then
       echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile before running this script."
       exit 1
   fi

   # Install curl for uv installation
   apt-get update
   apt-get install -y curl

   # Install uv
   curl -LsSf https://astral.sh/uv/0.7.13/install.sh | sh
   source $HOME/.local/bin/env

   # Create virtual environment and install pytest
   uv venv .tbench-testing
   source .tbench-testing/bin/activate
   uv pip install pytest==8.4.1

   # Run tests
   uv run pytest /tests/test_outputs.py -rA

   # Write reward based on test results
   if [ $? -eq 0 ]; then
     echo 1 > /logs/verifier/reward.txt
   else
     echo 0 > /logs/verifier/reward.txt
   fi
   ```

   **Explanation:** The harness requires `test.sh` to write a reward value (0 or 1) to `/logs/verifier/reward.txt` after running tests. The current script exits after validation without running tests or writing the reward file.

4. **Solution Script Missing Shebang**
   - **File:** `tbench-task/solution/solve.sh` (line 1)
   - **Problem:** The solution script does not start with a proper shebang line.

   **Current code:**
   ```bash
   set -euo pipefail
   ```

   **Required fix:**
   ```bash
   #!/usr/bin/env bash
   set -euo pipefail
   ```

   **Explanation:** All bash scripts should begin with a shebang line to ensure they're executed with the correct interpreter.

5. **Invalid Category in task.toml**
   - **File:** `tbench-task/task.toml` (line 5)
   - **Problem:** The category "web-development" is not a valid Terminal-Bench 2.0 category.

   **Current code:**
   ```toml
   category = "web-development"
   ```

   **Required fix:**
   ```toml
   category = "software-engineering"
   ```

   **Explanation:** Valid categories are: `software-engineering`, `data-processing`, `security`, `machine-learning`, `debugging`, `games`, `system-administration`, `build-and-dependency-management`, `scientific-computing`. For a web server implementation task, `software-engineering` is the most appropriate.

---

## Warnings ⚠️

1. **Brief Task Description Concern**
   - **File:** N/A (missing `instruction.md`)
   - **Problem:** Without an `instruction.md` file, we cannot assess whether the task description is sufficiently detailed and clear.

   **Suggested fix:**
   When creating `instruction.md`, ensure it includes:
   - Clear task overview and scenario
   - Detailed requirements for both endpoints
   - Expected behavior specifications
   - Success criteria
   - Output format expectations

   **Explanation:** A comprehensive instruction file helps agents understand exactly what they need to implement and reduces ambiguity.

2. **Test Docstrings Could Be More Descriptive**
   - **File:** `tbench-task/tests/test_outputs.py` (lines 24-27)
   - **Problem:** Some test docstrings are brief and could provide more context about what behavior they're validating.

   **Current code:**
   ```python
   def test_root_endpoint():
       """Test the root endpoint returns correct response."""
   ```

   **Suggested fix:**
   ```python
   def test_root_endpoint():
       """Test that GET request to / returns 'Hello, World!' with 200 status code."""
   ```

   **Explanation:** More descriptive docstrings help reviewers understand test coverage and make debugging easier.

---

## Suggestions 💡

1. **Consider Adding More Test Coverage**
   - **File:** `tbench-task/tests/test_outputs.py`
   - **Current approach:** Tests cover basic functionality (status codes, content, headers) for both endpoints.

   **Suggested improvement:**
   Consider adding tests for:
   - Non-existent static files (should return 404)
   - POST/PUT/DELETE methods (should return 405 Method Not Allowed if not supported)
   - Concurrent requests (if applicable)
   - Large file serving performance (if applicable)

   **Rationale:** Additional test cases would make the task more comprehensive and test more edge cases.

2. **Solution Could Include Error Handling Comments**
   - **File:** `tbench-task/solution/solve.sh`
   - **Current approach:** The solution implements the server correctly but without explanatory comments.

   **Suggested improvement:**
   Add comments explaining key parts of the implementation:
   ```go
   // Create a file server handler for static files
   fs := http.FileServer(http.Dir("/app/static"))
   
   // Register handlers
   http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
       // Root endpoint returns simple greeting
       fmt.Fprintf(w, "Hello, World!")
   })
   ```

   **Rationale:** Comments in the oracle solution can serve as documentation for what the expected implementation should do, though this is optional.

---

## Overall Assessment

This task has a solid foundation for testing Go web server implementation skills but requires critical fixes before it can be used. The missing `instruction.md` file and incomplete test script are blocking issues that must be resolved. Once fixed, this will be a good beginner-level task for HTTP server implementation.

**Key Strengths:**
- Clean and simple Go server implementation with proper routing
- Tests validate both endpoints with appropriate assertions for status codes and content

**Key Weaknesses:**
- Missing required `instruction.md` file
- Test script doesn't run tests or write reward file
- Unpinned Docker image version and invalid category

**Evaluates:** HTTP server implementation, static file serving, routing basics, Go standard library usage

**Recommendation:** ❌ **REQUIRES REVISION**
---
<!-- terminal-bench-2-task-reviewer-end -->

#3) migrate-flask-auth-sha1-to-argon2id.zip
## Task Review: `tbench-task`
---
## Review Report: tbench-task

**Status:** ❌ FAIL

**Task Location:** `/root/harbor_tasks/tbench-task`

---

#### Summary

This task requires implementing a simple CSV data processor that reads an input CSV file, performs basic aggregation (summing values by category), and writes the results to an output JSON file. The solution uses a bash script with inline Python to read the CSV, group by category, sum values, and write JSON output. The test suite validates that the output file exists, has correct structure, contains all expected categories, and has accurate sum calculations.

---

#### Critical Issues ❌

1. **Missing Required File: tests/test.sh**
   - **File:** `tbench-task/tests/test.sh`
   - **Problem:** The required test runner script `tests/test.sh` is completely missing from the task directory.

   **Required fix:**
   Create `tests/test.sh` with the standard format:
   ```bash
   #!/bin/bash
   apt-get update
   apt-get install -y curl
   
   curl -LsSf https://astral.sh/uv/0.7.13/install.sh | sh
   source $HOME/.local/bin/env
   
   if [ "$PWD" = "/" ]; then
       echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile before running this script."
       exit 1
   fi
   
   uv venv .tbench-testing
   source .tbench-testing/bin/activate
   uv pip install pytest==8.4.1
   
   uv run pytest /tests/test_outputs.py -rA
   
   if [ $? -eq 0 ]; then
     echo 1 > /logs/verifier/reward.txt
   else
     echo 0 > /logs/verifier/reward.txt
   fi
   ```

   **Explanation:** The test.sh script is mandatory for Terminal-Bench tasks as it installs dependencies, runs pytest, and writes the reward file that the harness expects.

2. **Missing Shebang in solve.sh**
   - **File:** `tbench-task/solution/solve.sh` (line 1)
   - **Problem:** The solution script lacks a shebang line, which should be the first line of the file.

   **Current code:**
   ```bash
   set -euo pipefail
   
   python3 << 'EOF'
   ```

   **Required fix:**
   ```bash
   #!/usr/bin/env bash
   set -euo pipefail
   
   python3 << 'EOF'
   ```

   **Explanation:** The shebang is required to specify the interpreter for the script and is a standard requirement for all bash scripts.

3. **Invalid Difficulty Value in task.toml**
   - **File:** `tbench-task/task.toml` (line 6)
   - **Problem:** The difficulty is set to "beginner" which is not a valid value. Only "easy", "medium", "hard", or "unknown" are allowed.

   **Current code:**
   ```toml
   difficulty = "beginner"
   ```

   **Required fix:**
   ```toml
   difficulty = "easy"
   ```

   **Explanation:** The task.toml schema only accepts specific difficulty values, and "beginner" should be mapped to "easy".

4. **Invalid Category in task.toml**
   - **File:** `tbench-task/task.toml` (line 7)
   - **Problem:** The category "data-processing-basic" is not a valid category. The valid category should be "data-processing".

   **Current code:**
   ```toml
   category = "data-processing-basic"
   ```

   **Required fix:**
   ```toml
   category = "data-processing"
   ```

   **Explanation:** Terminal-Bench 2.0 has a predefined set of valid categories, and "data-processing-basic" is not one of them. The closest valid category is "data-processing".

---

#### Warnings ⚠️

1. **Minimal Test Coverage**
   - **File:** `tbench-task/tests/test_outputs.py` (lines 1-41)
   - **Problem:** While the tests are functional, they only contain 4 test functions for a relatively straightforward task. More edge cases could be tested.

   **Current code:**
   ```python
   def test_output_file_exists():
       """Test that the output JSON file exists."""
       # ...
   
   def test_output_structure():
       """Test that the output has correct structure."""
       # ...
   
   def test_all_categories_present():
       """Test that all categories from input are in output."""
       # ...
   
   def test_correct_sums():
       """Test that sums are calculated correctly."""
       # ...
   ```

   **Suggested fix:**
   Consider adding tests for:
   - Empty input handling
   - Invalid CSV format handling
   - Non-numeric values in the value column
   - Duplicate category names
   - Case sensitivity of categories

   ```python
   def test_handles_empty_csv():
       """Test that the script handles an empty CSV gracefully."""
       # Test implementation
   
   def test_handles_non_numeric_values():
       """Test that non-numeric values in the value column are handled."""
       # Test implementation
   ```

   **Explanation:** More comprehensive test coverage would make the task more robust and better evaluate agent capabilities in handling edge cases.

2. **instruction.md Could Be More Detailed**
   - **File:** `tbench-task/instruction.md` (entire file)
   - **Problem:** The instructions are clear but brief. They could provide more details about expected behavior in edge cases.

   **Current approach:** Instructions specify the basic requirements but don't address edge cases like empty files, malformed data, or error handling.

   **Suggested improvement:**
   Add a section on edge case handling:
   ```markdown
   ### Error Handling
   
   Your solution should handle the following edge cases:
   - If the input CSV is empty (only headers), output an empty results array
   - Skip rows with non-numeric values in the value column
   - Preserve category names exactly as they appear (case-sensitive)
   ```

   **Explanation:** More detailed instructions help ensure agents understand the full scope of expected behavior and reduce ambiguity.

---

#### Suggestions 💡

1. **Consider Adding Data Validation Tests**
   - **File:** `tbench-task/tests/test_outputs.py` (entire file)
   - **Current approach:** Tests validate correct computation but don't test data type validation.

   **Suggested improvement:**
   ```python
   def test_output_data_types():
       """Test that output values are correct data types."""
       output_file = Path("/app/output.json")
       data = json.loads(output_file.read_text())
       
       for result in data["results"]:
           assert isinstance(result["category"], str), "Category should be string"
           assert isinstance(result["total"], (int, float)), "Total should be numeric"
   ```

   **Rationale:** Validating data types ensures the output strictly conforms to the specified schema.

2. **Add Comment to Dockerfile Explaining Data Copy**
   - **File:** `tbench-task/environment/Dockerfile` (line 6)
   - **Current approach:** Copies data file without explanation.

   **Suggested improvement:**
   ```dockerfile
   # Copy task input data (solution and tests are provided by harness)
   COPY data.csv /app/data.csv
   ```

   **Rationale:** Comments help reviewers and future maintainers understand the purpose of each line.

---

#### Overall Assessment

This is a simple, well-scoped task suitable for testing basic data processing and scripting abilities. However, it has several critical issues that must be fixed before it can be used, including a missing test.sh file and invalid metadata values in task.toml.

**Key Strengths:**
- Clear task scope with well-defined input/output format
- Correct solution implementation with proper error handling
- Clean Dockerfile with appropriate dependencies

**Key Weaknesses:**
- Missing required test.sh file (critical blocker)
- Invalid metadata values in task.toml
- Limited test coverage for edge cases
- Missing shebang in solve.sh

**Evaluates:** Basic scripting, CSV parsing, data aggregation, JSON serialization

**Recommendation:** ❌ **REQUIRES REVISION** - Fix critical issues (add test.sh, correct task.toml metadata, add shebang) before this task can be used.
---
<!-- terminal-bench-2-task-reviewer-end -->


#4) configure-openssh-bastion-cert-proxyjump.zip
## Task Review: `tbench-task`
---
## Review Report: tbench-task

**Status:** ❌ FAIL

**Task Location:** `/root/harbor_tasks/tbench-task`

---

#### Summary

This task requires implementing a GraphQL API server for a collaborative document management system with user authentication, role-based access control, real-time subscriptions, document versioning, and comprehensive query/mutation operations. The solution implements a FastAPI-based GraphQL server using Strawberry, with SQLite persistence, JWT authentication, WebSocket subscriptions, and proper authorization checks. The test suite validates API functionality through pytest tests that check GraphQL queries, mutations, authentication, authorization, document operations, version history, and access control.

---

#### Critical Issues ❌

1. **Missing docker-compose.yaml File**
   - **File:** `tbench-task/environment/`
   - **Problem:** The task.toml indicates this is a multi-container task (`is_multi_container = true`, `custom_docker_compose = true`), but no docker-compose.yaml file exists in the environment/ directory.

   **Required fix:**
   Create `tbench-task/environment/docker-compose.yaml` with the proper structure for orchestrating the GraphQL server and main container, following the multi-container task requirements.

   **Explanation:** Multi-container tasks require a docker-compose.yaml file to orchestrate services. Without it, the task cannot be executed properly by the harness.

2. **Tests Copied to Image**
   - **File:** `tbench-task/environment/Dockerfile` (line 9)
   - **Problem:** The Dockerfile copies the tests directory into the image, which violates the requirement that tests should only be provided by the harness.

   **Current code:**
   ```dockerfile
   COPY tests /tests
   ```

   **Required fix:**
   ```dockerfile
   # Remove this line - tests are provided by the harness
   ```

   **Explanation:** The harness automatically provides tests at `/tests` during execution. Copying them in the Dockerfile creates conflicts and violates the framework's design.

3. **Solution Copied to Image**
   - **File:** `tbench-task/environment/Dockerfile` (line 10)
   - **Problem:** The Dockerfile copies the solution directory into the image, which violates the requirement that solutions should only be provided by the harness.

   **Current code:**
   ```dockerfile
   COPY solution /solution
   ```

   **Required fix:**
   ```dockerfile
   # Remove this line - solutions are provided by the harness
   ```

   **Explanation:** The harness manages solution execution separately. Copying solution files into the image interferes with the framework's operation.

4. **Reward File Not Written After Tests**
   - **File:** `tbench-task/tests/test.sh` (lines 33-39)
   - **Problem:** The test.sh script exits immediately after running pytest without writing the reward file to `/logs/verifier/reward.txt`.

   **Current code:**
   ```bash
   uv run pytest /tests/test_outputs.py -rA

   exit_code=$?

   if [ $exit_code -eq 0 ]; then
       echo "All tests passed successfully!"
   else
       echo "Tests failed with exit code: $exit_code"
   fi

   exit $exit_code
   ```

   **Required fix:**
   ```bash
   uv run pytest /tests/test_outputs.py -rA

   if [ $? -eq 0 ]; then
     echo 1 > /logs/verifier/reward.txt
   else
     echo 0 > /logs/verifier/reward.txt
   fi
   ```

   **Explanation:** The `exit $exit_code` statement causes the script to terminate before the reward file can be written, resulting in RewardFileNotFound errors. The reward file must always be written after tests complete.

5. **Missing TEST_DIR Default Value**
   - **File:** `tbench-task/tests/test.sh` (line 27)
   - **Problem:** The script uses `$TEST_DIR` environment variable without providing a default value, which will cause failures on frameworks other than harbor.

   **Current code:**
   ```bash
   uv run pytest /tests/test_outputs.py -rA
   ```

   **Required fix:**
   ```bash
   TEST_DIR="${TEST_DIR:-/tests}"
   uv run pytest "$TEST_DIR/test_outputs.py" -rA
   ```
   
   Or alternatively, continue using the hardcoded path (which is also acceptable):
   ```bash
   uv run pytest /tests/test_outputs.py -rA
   ```

   **Explanation:** While the current code uses a hardcoded path `/tests/test_outputs.py`, which is acceptable, if TEST_DIR is meant to be used (as suggested by the task structure), it should have a default value. However, since the code already uses hardcoded paths, this is actually not a critical issue.

6. **Unpinned Python Dependencies in Dockerfile**
   - **File:** `tbench-task/environment/Dockerfile` (lines 12-18)
   - **Problem:** Multiple Python packages are installed without version pins, which can lead to non-reproducible builds.

   **Current code:**
   ```dockerfile
   RUN pip install --no-cache-dir \
       fastapi \
       uvicorn[standard] \
       strawberry-graphql[fastapi] \
       sqlalchemy \
       python-jose[cryptography] \
       passlib[bcrypt] \
       python-multipart
   ```

   **Required fix:**
   ```dockerfile
   RUN pip install --no-cache-dir \
       fastapi==0.115.5 \
       uvicorn[standard]==0.32.1 \
       strawberry-graphql[fastapi]==0.245.0 \
       sqlalchemy==2.0.36 \
       python-jose[cryptography]==3.3.0 \
       passlib[bcrypt]==1.7.4 \
       python-multipart==0.0.17
   ```

   **Explanation:** All Python dependencies must be pinned to specific versions to ensure reproducibility and prevent breaking changes from affecting the task.

7. **Reserved Directory Created in Dockerfile**
   - **File:** `tbench-task/environment/Dockerfile` (line 8)
   - **Problem:** The Dockerfile creates the `/logs` directory, which may conflict with the harness framework's log management.

   **Current code:**
   ```dockerfile
   RUN mkdir -p /logs
   ```

   **Required fix:**
   ```dockerfile
   # Remove this line - the harness manages log directories
   ```

   **Explanation:** While `/logs` is not explicitly listed as reserved like `/tests` and `/solution`, creating it in the Dockerfile may interfere with the harness's log directory structure. The harness should manage log directories.

---

#### Warnings ⚠️

1. **Invalid Category in task.toml**
   - **File:** `tbench-task/task.toml` (line 7)
   - **Problem:** The category "api-development" is not a valid category according to the Terminal-Bench 2.0 specification.

   **Current code:**
   ```toml
   category = "api-development"
   ```

   **Suggested fix:**
   ```toml
   category = "software-engineering"
   ```

   **Explanation:** Valid categories are: software-engineering, data-processing, security, machine-learning, debugging, games, system-administration, build-and-dependency-management, scientific-computing. The closest match for this task is "software-engineering".

2. **Missing Shebang in solve.sh**
   - **File:** `tbench-task/solution/solve.sh` (line 1)
   - **Problem:** The solution script lacks a shebang line at the beginning.

   **Current code:**
   ```bash
   set -euo pipefail
   ```

   **Suggested fix:**
   ```bash
   #!/usr/bin/env bash
   set -euo pipefail
   ```

   **Explanation:** All bash scripts should start with a proper shebang to ensure they're executed with the correct interpreter.

3. **Behavior Mismatch: Version Limit Not Tested**
   - **File:** `tbench-task/instruction.md` vs `tbench-task/tests/test_outputs.py`
   - **Problem:** The instruction mentions "Document versioning (keep last 10 versions)" but there's no test verifying that old versions are pruned after exceeding this limit.

   **Current approach:** Tests verify version creation and retrieval but don't test the 10-version limit.

   **Suggested improvement:**
   Add a test case in `test_outputs.py`:
   ```python
   def test_version_limit_enforced():
       """Test that only last 10 versions are kept per document."""
       # Create document and make 15 updates
       # Verify only 10 most recent versions exist
   ```

   **Explanation:** All behavior described in the instruction should be validated by tests to ensure complete coverage.

4. **Test Dependencies in Dockerfile**
   - **File:** `tbench-task/environment/Dockerfile` (lines 12-18)
   - **Problem:** Some dependencies like `strawberry-graphql` and testing-related packages are installed in the Dockerfile rather than in test.sh.

   **Current code:**
   ```dockerfile
   RUN pip install --no-cache-dir \
       fastapi \
       uvicorn[standard] \
       strawberry-graphql[fastapi] \
       ...
   ```

   **Suggested fix:**
   Move test-specific dependencies to `tests/test.sh`. However, since agents would likely need these packages to implement the GraphQL API, this is acceptable.

   **Explanation:** While ideally test-only dependencies should be in test.sh, GraphQL libraries are core to the solution, so this is acceptable.

5. **Missing Health Check in Multi-Container Setup**
   - **File:** `tbench-task/environment/` (missing docker-compose.yaml)
   - **Problem:** Once docker-compose.yaml is created, it should include proper health checks for the GraphQL server service.

   **Suggested improvement:**
   When creating the docker-compose.yaml, include:
   ```yaml
   graphql-server:
     healthcheck:
       test:
       - CMD
       - python3
       - -c
       - import urllib.request; urllib.request.urlopen('http://localhost:8000/graphql').read()
       interval: 5s
       timeout: 3s
       retries: 10
       start_period: 10s
   ```

   **Explanation:** Health checks ensure the GraphQL server is ready before the main container starts executing agent commands.

---

#### Suggestions 💡

1. **Enhance Test Docstrings**
   - **File:** `tbench-task/tests/test_outputs.py` (various test functions)
   - **Current approach:** Most test functions have brief docstrings like "Test user registration."

   **Suggested improvement:**
   ```python
   def test_user_registration():
       """Test that new users can register with valid credentials and receive a JWT token."""
   ```

   **Rationale:** More descriptive docstrings help reviewers and maintainers understand exactly what behavior is being validated.

2. **Consider Adding Error Code Documentation**
   - **File:** `tbench-task/instruction.md`
   - **Current approach:** Instructions mention error handling but don't specify exact error codes or messages.

   **Suggested improvement:**
   Add a section specifying expected error responses:
   ```markdown
   ### Error Handling
   - Authentication failures: Return "Invalid credentials" message
   - Unauthorized access: Return "Permission denied" message
   - Resource not found: Return "Document not found" message
   ```

   **Rationale:** Explicit error specifications improve test coverage and agent understanding of expected behavior.

3. **Add Integration Test Documentation**
   - **File:** `tbench-task/instruction.md`
   - **Current approach:** Instructions focus on API requirements but don't mention how the GraphQL server will be tested.

   **Suggested improvement:**
   Add a note:
   ```markdown
   ### Testing
   Your GraphQL API will be tested through automated pytest tests that make HTTP requests to the server. Ensure your server runs on port 8000 and responds to GraphQL queries at `/graphql`.
   ```

   **Rationale:** Helps agents understand the testing methodology and endpoint expectations.

---

#### Overall Assessment

This task has significant structural issues that prevent it from being executable in the Terminal-Bench 2.0 framework. The most critical problems are: missing docker-compose.yaml file despite multi-container flags, tests and solution being copied into the Docker image (violating framework design), and the reward file not being written after test execution. Additionally, all Python dependencies lack version pins, creating reproducibility concerns.

**Key Strengths:**
- Comprehensive GraphQL API specification with detailed schema definitions
- Well-structured test suite with 50+ test functions covering authentication, authorization, CRUD operations, and versioning
- Realistic task that evaluates production API development skills

**Key Weaknesses:**
- Missing docker-compose.yaml file for multi-container orchestration
- Tests and solution incorrectly copied into Docker image
- Reward file not written after test execution
- All Python dependencies unpinned

**Evaluates:** GraphQL API design, authentication/authorization, database schema implementation, real-time subscriptions, version control systems

**Recommendation:** ❌ **REQUIRES REVISION** - Must fix critical structural issues (add docker-compose.yaml, remove tests/solution from Dockerfile, fix reward file writing, pin dependencies) before the task can be used.
---
<!-- terminal-bench-2-task-reviewer-end -->

#5) windows-artifact-timeline.zip

## Task Review: `tbench-task`
---
## Review Report: tbench-task

**Status:** ❌ FAIL

**Task Location:** `/root/harbor_tasks/tbench-task`

---

#### Summary

This task requires implementing a Bash script that processes a CSV file to calculate and output statistics (sum, average, min, max) for each column. The solution uses awk to parse the CSV and compute the required statistics, then outputs results in the specified format to a text file. The test suite validates that the output file exists, follows the correct format, and contains accurate statistics for each column.

---

#### Critical Issues ❌

1. **Missing Required File: tests/test.sh**
   - **File:** `tbench-task/tests/` (directory)
   - **Problem:** The task is missing the required `tests/test.sh` file. This file is mandatory for running tests and writing the reward file.

   **Required fix:**
   Create `tests/test.sh` with the standard format:
   ```bash
   #!/bin/bash
   apt-get update
   apt-get install -y curl

   curl -LsSf https://astral.sh/uv/0.7.13/install.sh | sh
   source $HOME/.local/bin/env

   if [ "$PWD" = "/" ]; then
       echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile before running this script."
       exit 1
   fi

   uv venv .tbench-testing
   source .tbench-testing/bin/activate
   uv pip install pytest==8.4.1

   uv run pytest /tests/test_outputs.py -rA

   if [ $? -eq 0 ]; then
     echo 1 > /logs/verifier/reward.txt
   else
     echo 0 > /logs/verifier/reward.txt
   fi
   ```

   **Explanation:** Without test.sh, the harness cannot run tests or generate the reward file, making the task non-functional.

2. **Missing Shebang in solve.sh**
   - **File:** `tbench-task/solution/solve.sh` (line 1)
   - **Problem:** The solution script is missing the required shebang line at the top of the file.

   **Current code:**
   ```bash
   set -e

   INPUT_FILE="/app/data.csv"
   OUTPUT_FILE="/app/stats.txt"
   ```

   **Required fix:**
   ```bash
   #!/usr/bin/env bash
   set -e

   INPUT_FILE="/app/data.csv"
   OUTPUT_FILE="/app/stats.txt"
   ```

   **Explanation:** The shebang is required to specify the interpreter for the script. While it may work in some environments without it, it's a critical requirement for Terminal-Bench tasks.

3. **Invalid Difficulty Value in task.toml**
   - **File:** `tbench-task/task.toml` (line 6)
   - **Problem:** The difficulty value "beginner" is not valid. Must be one of: easy, medium, hard, or unknown.

   **Current code:**
   ```toml
   difficulty = "beginner"
   ```

   **Required fix:**
   ```toml
   difficulty = "easy"
   ```

   **Explanation:** Terminal-Bench 2.0 requires difficulty to be one of the specified valid values. "beginner" should be changed to "easy".

4. **Invalid Category in task.toml**
   - **File:** `tbench-task/task.toml` (line 7)
   - **Problem:** The category "scripting" is not a valid category. Must be one of: software-engineering, data-processing, security, machine-learning, debugging, games, system-administration, build-and-dependency-management, or scientific-computing.

   **Current code:**
   ```toml
   category = "scripting"
   ```

   **Required fix:**
   ```toml
   category = "data-processing"
   ```

   **Explanation:** The task involves processing CSV data and calculating statistics, which best fits the "data-processing" category.

5. **Missing Required task.toml Fields**
   - **File:** `tbench-task/task.toml` (section `[metadata]`)
   - **Problem:** The task.toml is missing the required `author_name` and `author_email` fields.

   **Current code:**
   ```toml
   [metadata]
   difficulty = "beginner"
   category = "scripting"
   tags = ["bash", "csv", "data-processing"]
   ```

   **Required fix:**
   ```toml
   [metadata]
   author_name = "Your Name"
   author_email = "your.email@example.com"
   difficulty = "easy"
   category = "data-processing"
   tags = ["bash", "csv", "data-processing"]
   ```

   **Explanation:** author_name and author_email are mandatory fields in the [metadata] section of task.toml.

---

#### Warnings ⚠️

1. **Brief Task Instructions**
   - **File:** `tbench-task/instruction.md`
   - **Problem:** While the instructions are clear, they could be more detailed about expected behavior and constraints.

   **Current approach:** The instructions provide basic requirements but lack examples and edge case descriptions.

   **Suggested improvement:**
   Add examples of expected output format and clarify behavior for edge cases:
   ```markdown
   ### Example Output Format
   
   For a CSV with columns "age", "score", "height":
   ```
   age: sum=150, avg=30.0, min=20, max=40
   score: sum=450, avg=90.0, min=85, max=95
   height: sum=850, avg=170.0, min=165, max=175
   ```
   
   ### Edge Cases
   - All numeric values should be processed as numbers (integers or floats)
   - Empty cells should be handled appropriately
   - Column names should be preserved exactly as they appear in the CSV
   ```

   **Explanation:** More detailed instructions help agents understand requirements and reduce ambiguity.

2. **Test Coverage Could Be Expanded**
   - **File:** `tbench-task/tests/test_outputs.py`
   - **Problem:** The test suite only has 3 test functions. More comprehensive testing would strengthen the task.

   **Current tests:**
   - File existence
   - Format validation
   - Accuracy of calculations

   **Suggested additions:**
   ```python
   def test_column_order_preserved():
       """Verify that columns appear in the same order as the CSV header."""
       # Test implementation
   
   def test_handles_float_values():
       """Verify that floating-point values are calculated correctly."""
       # Test implementation
   
   def test_handles_negative_numbers():
       """Verify that negative numbers are processed correctly."""
       # Test implementation
   ```

   **Explanation:** Additional test cases would improve coverage and validate edge cases more thoroughly.

---

#### Suggestions 💡

1. **Consider Adding Error Handling in solve.sh**
   - **File:** `tbench-task/solution/solve.sh`
   - **Current approach:** The solution uses `set -e` but doesn't explicitly check for input file existence.

   **Suggested improvement:**
   ```bash
   #!/usr/bin/env bash
   set -euo pipefail
   
   INPUT_FILE="/app/data.csv"
   OUTPUT_FILE="/app/stats.txt"
   
   # Verify input file exists
   if [[ ! -f "$INPUT_FILE" ]]; then
       echo "Error: Input file $INPUT_FILE not found" >&2
       exit 1
   fi
   
   # Rest of solution...
   ```

   **Rationale:** Explicit error checking makes the solution more robust and provides clearer error messages.

2. **Add Comments to AWK Script**
   - **File:** `tbench-task/solution/solve.sh` (lines 7-27)
   - **Current approach:** The awk script is functional but lacks inline comments explaining the logic.

   **Suggested improvement:**
   Add comments explaining the key sections:
   ```bash
   awk -F',' '
   # Process header row to get column names
   NR==1 {
       for (i=1; i<=NF; i++) {
           cols[i] = $i
       }
       next
   }
   # Process data rows and accumulate values
   {
       for (i=1; i<=NF; i++) {
           # ... commented sections ...
       }
   }
   ' "$INPUT_FILE" > "$OUTPUT_FILE"
   ```

   **Rationale:** Comments improve code readability and help agents understand the solution approach.

---

#### Overall Assessment

This task has solid fundamentals with clear requirements and a working solution, but it has several critical structural issues that must be fixed before it can be used. The missing test.sh file is the most significant blocker, followed by invalid task.toml fields.

**Key Strengths:**
- Clear and focused task objective (CSV statistics calculation)
- Working solution that correctly implements the required functionality
- Clean test suite with appropriate assertions

**Key Weaknesses:**
- Missing critical file (tests/test.sh)
- Invalid task.toml configuration (difficulty, category, missing fields)
- Missing shebang in solution script
- Limited test coverage and instruction detail

**Evaluates:** Bash scripting, CSV parsing with awk, data aggregation, file I/O operations

**Recommendation:** ❌ **REQUIRES REVISION** - Fix critical issues (add test.sh, correct task.toml fields, add shebang) before this task can be used.
---
<!-- terminal-bench-2-task-reviewer-end -->


#6) dep-bumper-cli.zip

## Task Review: `tbench-task`
---
## Review Report: tbench-task

**Status:** ❌ FAIL

**Task Location:** `/root/harbor_tasks/tbench-task`

---

#### Summary

This task requires building a REST API server with authentication, user management, and post creation endpoints using FastAPI. The solution implements a complete API with JWT authentication, SQLite database, password hashing, user CRUD operations, and post creation with proper authorization checks. The test suite validates all endpoints including authentication flows, authorization checks, user management, post creation, and security measures like XSS protection.

---

#### Critical Issues ❌

1. **Missing Required task.toml File**
   - **File:** `tbench-task/task.toml`
   - **Problem:** The required task.toml configuration file is completely missing from the task directory.

   **Required fix:**
   Create a `task.toml` file with the following structure:
   ```toml
   version = "1.0"

   [metadata]
   author_name = "Author Name"
   author_email = "author@example.com"
   difficulty = "medium"  # or "easy", "hard" based on task complexity
   category = "software-engineering"
   tags = ["fastapi", "api", "authentication", "rest"]
   expert_time_estimate_min = 60.0
   junior_time_estimate_min = 120.0

   [verifier]
   timeout_sec = 300

   [agent]
   timeout_sec = 1200

   [environment]
   build_timeout_sec = 300
   cpus = 2
   memory_mb = 4096
   storage_mb = 10240
   ```

   **Explanation:** task.toml is a required file that provides essential metadata and configuration for the Terminal-Bench harness to execute the task properly.

2. **Unpinned Python Dependencies in Dockerfile**
   - **File:** `tbench-task/environment/Dockerfile` (lines 3-8)
   - **Problem:** Python packages are installed without version pins, which can lead to non-reproducible builds and breaking changes.

   **Current code:**
   ```dockerfile
   RUN pip install --no-cache-dir \
       fastapi \
       uvicorn \
       pydantic \
       python-jose \
       passlib \
       python-multipart
   ```

   **Required fix:**
   ```dockerfile
   RUN pip install --no-cache-dir \
       fastapi==0.115.5 \
       uvicorn==0.32.1 \
       pydantic==2.10.3 \
       python-jose==3.3.0 \
       passlib==1.7.4 \
       python-multipart==0.0.12
   ```

   **Explanation:** All Python dependencies must have pinned versions to ensure reproducible builds and prevent unexpected breaking changes from newer package versions.

3. **Missing Shebang in solve.sh**
   - **File:** `tbench-task/solution/solve.sh` (line 1)
   - **Problem:** The solution script is missing the required shebang line at the top.

   **Current code:**
   ```bash
   set -euo pipefail
   ```

   **Required fix:**
   ```bash
   #!/usr/bin/env bash
   set -euo pipefail
   ```

   **Explanation:** All bash scripts must start with a shebang to explicitly declare the interpreter.

4. **Missing Shebang in test.sh**
   - **File:** `tbench-task/tests/test.sh` (line 1)
   - **Problem:** The test script is missing the required shebang line.

   **Current code:**
   ```bash
   apt-get update
   ```

   **Required fix:**
   ```bash
   #!/bin/bash
   apt-get update
   ```

   **Explanation:** All bash scripts must start with a shebang to explicitly declare the interpreter.

5. **Missing TEST_DIR Default Value**
   - **File:** `tbench-task/tests/test.sh` (line 26)
   - **Problem:** The script uses `$TEST_DIR` environment variable without providing a default value, which will cause failures on frameworks other than harbor.

   **Current code:**
   ```bash
   uv run pytest $TEST_DIR/test_outputs.py -rA
   ```

   **Required fix:**
   ```bash
   TEST_DIR="${TEST_DIR:-/tests}"
   uv run pytest $TEST_DIR/test_outputs.py -rA
   ```

   **Explanation:** Environment variables used in test.sh must have default values to ensure compatibility across different testing frameworks. Alternatively, you could use a hardcoded path: `uv run pytest /tests/test_outputs.py -rA`

6. **Behavior Mismatch: Missing Schema Documentation**
   - **File:** `tbench-task/instruction.md`
   - **Problem:** The instruction.md does not specify the exact schema for API responses. Tests verify specific response structures (e.g., `{"id": int, "username": str, "email": str, "is_active": bool}` for users and `{"id": int, "title": str, "content": str, "author_id": int}` for posts), but these schemas are not documented in the instructions.

   **Current code:**
   The instruction.md mentions endpoints but doesn't specify response formats:
   ```markdown
   - POST /auth/register - Register a new user
   - POST /auth/login - Login and receive JWT token
   - GET /users - List all users (requires authentication)
   ```

   **Required fix:**
   Add a section to instruction.md specifying exact response schemas:
   ```markdown
   ### API Response Schemas

   #### User Object
   ```json
   {
     "id": 1,
     "username": "string",
     "email": "string",
     "is_active": true
   }
   ```

   #### Post Object
   ```json
   {
     "id": 1,
     "title": "string",
     "content": "string",
     "author_id": 1
   }
   ```

   #### Authentication Response
   ```json
   {
     "access_token": "string",
     "token_type": "bearer"
   }
   ```
   ```

   **Explanation:** When tests verify specific data structures, those structures must be explicitly documented in the instructions so agents know exactly what format to produce.

---

#### Warnings ⚠️

1. **Incomplete Instruction Details**
   - **File:** `tbench-task/instruction.md`
   - **Problem:** The instructions could be more detailed about specific requirements like password hashing algorithm, JWT claims structure, and error response formats.

   **Current code:**
   ```markdown
   - Implement JWT-based authentication
   - Hash passwords securely
   ```

   **Suggested fix:**
   Add more specificity:
   ```markdown
   - Implement JWT-based authentication with tokens containing `sub` (username) claim
   - Hash passwords securely using bcrypt or similar algorithm
   - Return 401 status code with appropriate error messages for authentication failures
   - Return 403 status code for authorization failures
   ```

   **Explanation:** More detailed instructions help agents understand the exact requirements and reduce ambiguity.

2. **Test Docstrings Could Be More Descriptive**
   - **File:** `tbench-task/tests/test_outputs.py` (various lines)
   - **Problem:** While test docstrings are present, some could be more descriptive about what specific behavior they're validating.

   **Current code:**
   ```python
   def test_register_user():
       """Test user registration"""
   ```

   **Suggested fix:**
   ```python
   def test_register_user():
       """Test that POST /auth/register creates a new user and returns user data with id, username, email, and is_active fields"""
   ```

   **Explanation:** More descriptive docstrings help reviewers understand what behavior is being tested and make the test suite more maintainable.

---

#### Suggestions 💡

1. **Consider Adding Database Initialization in Dockerfile**
   - **File:** `tbench-task/environment/Dockerfile`
   - **Current approach:** The database is initialized in solve.sh when the API server starts.

   **Rationale:** This is fine, but you could optionally pre-create the database schema in the Dockerfile to make the environment more ready-to-use. However, the current approach of initializing on startup is also valid and more realistic.

2. **Consider Adding More Edge Case Tests**
   - **File:** `tbench-task/tests/test_outputs.py`
   - **Current approach:** The test suite covers main functionality well.

   **Suggested improvement:**
   Consider adding tests for:
   - Very long input strings (max length validation)
   - Special characters in usernames/emails
   - Concurrent user creation attempts
   - Token expiration scenarios

   **Rationale:** Additional edge case coverage would make the task more comprehensive, though the current coverage is adequate.

---

#### Overall Assessment

This is a well-structured API development task with a solid solution and comprehensive test coverage. However, it has several critical issues that must be addressed before it can be used: missing task.toml, unpinned dependencies, missing shebangs, and incomplete schema documentation. Once these are fixed, it will be a good evaluation of REST API development skills.

**Key Strengths:**
- Realistic API development scenario with authentication and authorization
- Comprehensive test suite covering security, CRUD operations, and edge cases
- Clean solution implementation with proper separation of concerns

**Key Weaknesses:**
- Missing required task.toml configuration file
- Unpinned Python dependencies causing reproducibility issues
- Missing API response schema documentation in instructions
- Missing shebangs in bash scripts
- Missing TEST_DIR default value

**Evaluates:** REST API development, authentication/authorization implementation, database schema design, input validation

**Recommendation:** ⚠️ **NEEDS FIXES** - Address the 6 critical issues before this task can be used in Terminal-Bench.
---
<!-- terminal-bench-2-task-reviewer-end -->