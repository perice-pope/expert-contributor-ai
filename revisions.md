# Revisions Tracker

> **AI Execution Instructions:**
> 1. Scan this document for entries with status `[ ]` (pending) or `[→]` (in-progress)
> 2. Locate the zip file specified in `file_path`
> 3. Extract and analyze the contents
> 4. Implement changes based on the revision notes and logs
> 5. Create revised zip file in `/revisions/` folder with `-revised` suffix
> 6. Update status to `[✓]` and add completion timestamp
> 7. Update "Lessons Learned" section with insights

---

## Revision Queue

### Template (Copy this for each new revision)
```markdown
#### [REVISION-XXX] - Brief Title
- **Status**: `[ ]` Pending | `[→]` In Progress | `[✓]` Completed | `[✗]` Cancelled
- **Priority**: Low | Medium | High | Critical
- **File Path**: `path/to/file.zip`
- **Date Submitted**: YYYY-MM-DD
- **Completed**: YYYY-MM-DD HH:MM (auto-filled by AI)

**Logs/Issues:**
```
[Paste error logs, stack traces, or console output here]
```

**Revision Notes:**
1. [Specific change needed - be precise]
2. [Another change - include file paths if known]
3. [More details...]

**Expected Output:**
- [ ] Checklist item 1
- [ ] Checklist item 2
- [ ] Verification step

**Related to Lesson**: [Reference to lesson ID if applicable, e.g., LESSON-001]

**AI Execution Log:**
```
[AI will populate this section with actions taken]
- Extracted: [files]
- Modified: [files]
- Created: [output path]
- Tests run: [results]
```
```

---

## Active Revisions

### [REVISION-001] - Example Revision Template
- **Status**: `[ ]` Pending
- **Priority**: High
- **File Path**: `submissions/example-project.zip`
- **Date Submitted**: 2025-12-21
- **Completed**: --

**Logs/Issues:**
```
[Example log section - replace with actual logs]
Error: Module not found 'express'
    at Function.Module._resolveFilename (node:internal/modules/cjs/loader:1039:15)
    at Function.Module._load (node:internal/modules/cjs/loader:885:27)
```

**Revision Notes:**
1. Add missing dependencies to package.json
2. Fix import paths in src/server.js
3. Update configuration to use environment variables
4. Add error handling for database connections

**Expected Output:**
- [ ] Dependencies properly listed in package.json
- [ ] All imports resolve correctly
- [ ] Environment variables documented in .env.example
- [ ] Error handling tested and working

**Related to Lesson**: --

**AI Execution Log:**
```
[AI will populate this after processing]
```

---

## Completed Revisions

### [REVISION-000] - Sample Completed Revision
- **Status**: `[✓]` Completed
- **Priority**: Medium
- **File Path**: `submissions/sample.zip`
- **Date Submitted**: 2025-12-20
- **Completed**: 2025-12-21 10:30

**Logs/Issues:**
```
TypeError: Cannot read property 'length' of undefined
```

**Revision Notes:**
1. Add null checks before accessing array properties
2. Implement defensive programming

**Expected Output:**
- [✓] Null checks added
- [✓] Tests passing

**Related to Lesson**: LESSON-001

**AI Execution Log:**
```
- Extracted: sample.zip → /tmp/sample/
- Modified: src/utils.js (added null checks on lines 45, 67, 89)
- Created: /revisions/sample-revised.zip
- Tests run: All 12 tests passing
```

---

## Lessons Learned

> This section helps prevent repeating the same mistakes. AI should analyze completed revisions and add patterns here.

### LESSON-001: Always Add Null/Undefined Checks
- **Pattern**: Accessing properties on potentially undefined objects
- **Solution**: Implement optional chaining (?.) and nullish coalescing (??)
- **Example**: 
  ```javascript
  // Bad
  const length = data.items.length;
  
  // Good
  const length = data?.items?.length ?? 0;
  ```
- **Related Revisions**: REVISION-000, REVISION-XXX
- **Date Added**: 2025-12-21

### LESSON-002: Template for New Lessons
- **Pattern**: [Describe the recurring issue pattern]
- **Solution**: [Best practice to avoid this]
- **Example**: 
  ```language
  [Code example showing before/after]
  ```
- **Related Revisions**: [List revision IDs]
- **Date Added**: YYYY-MM-DD

---

## AI Automation Checklist

When processing a revision, the AI must:

1. **Pre-flight Checks**
   - [ ] Verify zip file exists at specified path
   - [ ] Check if `/revisions/` folder exists (create if not)
   - [ ] Update status to `[→]` In Progress
   - [ ] Validate revision notes are clear and actionable

2. **Extraction & Analysis**
   - [ ] Extract zip to temporary location
   - [ ] Analyze file structure and dependencies
   - [ ] Review logs and identify root causes
   - [ ] Create execution plan

3. **Implementation**
   - [ ] Make changes according to revision notes
   - [ ] Verify each item in "Expected Output" checklist
   - [ ] Run tests if applicable
   - [ ] Check for similar issues in other files

4. **Packaging & Documentation**
   - [ ] Create revised zip with `-revised` suffix
   - [ ] Save to `/revisions/` folder
   - [ ] Update "AI Execution Log" with detailed actions
   - [ ] Update status to `[✓]` Completed
   - [ ] Add completion timestamp

5. **Learning & Improvement**
   - [ ] Analyze if this relates to existing lessons
   - [ ] Create new lesson if pattern is identified
   - [ ] Link revision to relevant lesson ID
   - [ ] Update lesson with additional revision references

---

## Quick Reference

### Status Indicators
- `[ ]` - Pending (not started)
- `[→]` - In Progress (AI is working on it)
- `[✓]` - Completed (revision done)
- `[✗]` - Cancelled (no longer needed)

### Priority Levels
- **Critical**: Blocks production, immediate attention
- **High**: Important, should be next in queue
- **Medium**: Normal priority
- **Low**: Nice to have, can wait

### File Naming Convention
- Original: `project-name.zip`
- Revised: `project-name-revised.zip` (in `/revisions/` folder)
- Multiple revisions: `project-name-revised-v2.zip`, etc.

### Folder Structure
```
workspace/
├── revisions.md (this file)
├── revisions/ (created automatically)
│   ├── project-a-revised.zip
│   ├── project-b-revised.zip
│   └── ...
└── submissions/ (recommended location for original zips)
    ├── project-a.zip
    ├── project-b.zip
    └── ...
```

---

## Tips for Best Results

### For Humans (You):
1. **Be Specific**: Include exact file names, line numbers, or function names when possible
2. **Include Context**: Paste full error logs, not just error messages
3. **Set Priorities**: Help AI know what to work on first
4. **Reference Lessons**: Check if there's an existing lesson for the issue
5. **One Issue Per Revision**: Break complex problems into separate revisions

### For AI:
1. **Read Carefully**: Parse revision notes and logs thoroughly before acting
2. **Verify Understanding**: If notes are unclear, ask for clarification
3. **Document Everything**: Log all changes in the execution log
4. **Learn Patterns**: After 2-3 similar issues, create a lesson
5. **Test Thoroughly**: Verify expected outputs before marking complete
6. **Be Atomic**: Complete one revision fully before moving to the next

---

## Statistics

- **Total Revisions**: 1
- **Completed**: 1
- **Pending**: 1
- **In Progress**: 0
- **Cancelled**: 0
- **Lessons Learned**: 2
- **Success Rate**: 100%

---

*Last Updated: 2025-12-21*
*Template Version: 1.0*

