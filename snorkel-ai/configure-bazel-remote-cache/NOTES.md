# Maintainer Notes — configure-bazel-remote-cache

## Intended Agent Failure Modes

1. **Shallow fix**: Agent creates `.bazelrc` but doesn't verify cache effectiveness
   - Test verifies >95% cache hits, so shallow fixes will fail
   - Test verifies no compile actions executed, catching incomplete configurations

2. **Missing cache configuration**: Agent forgets to configure remote cache
   - Test checks for `.bazelrc` file existence and content
   - Build will fail or show low cache hit rate

3. **Incorrect cache URL**: Agent uses wrong port or host
   - bazel-remote runs on localhost:8080, wrong URL will cause cache misses
   - Test verifies cache hit percentage, catching configuration errors

4. **Not cleaning before second build**: Agent doesn't simulate fresh checkout
   - Without `bazel clean --expunge`, local cache might be used instead of remote
   - Test verifies compile actions = 0, which requires proper clean

5. **Incorrect build event parsing**: Agent doesn't properly extract cache statistics
   - Build event JSON format is complex, incorrect parsing leads to wrong statistics
   - Test verifies internal consistency of statistics

6. **Not waiting for bazel-remote**: Agent starts building before cache server is ready
   - Solution includes health check, but agents might skip it
   - Will cause cache connection errors or low hit rates

## Test Design Rationale

- **Behavioral validation only**: Tests check outputs (JSON file, `.bazelrc` content), not implementation
- **Cache hit threshold (95%)**: High threshold ensures remote cache is actually being used effectively
- **Compile action verification**: Ensures no compilation happens in second build (all from cache)
- **Internal consistency check**: Verifies statistics are mathematically consistent
- **No source grepping**: Tests only read generated files, not source code

## Determinism and Reproducibility

- **Pinned versions**: Bazel 7.1.1, bazel-remote 2.6.1 (pinned in Dockerfile)
- **No network calls**: All dependencies installed at build time
- **Deterministic builds**: Bazel builds are deterministic with proper configuration
- **Cache persistence**: Cache stored in `/cache` directory, persists across builds
- **Fixed port**: bazel-remote always on localhost:8080

## Build Event Protocol Parsing

Bazel's build event protocol outputs JSON in NDJSON format (one JSON object per line). The solution script parses:
- `action.completed` events for action completion
- `cacheHit` field to determine cache hits
- `type` field to identify compile actions

The parsing handles multiple possible JSON structures to be robust.

## Expected Agent Behavior

1. Agent should discover that `.bazelrc` is missing
2. Agent should configure remote cache to `http://localhost:8080`
3. Agent should build project to prime cache
4. Agent should clean local state (`bazel clean --expunge`)
5. Agent should rebuild and verify cache hits
6. Agent should parse build event JSON to extract statistics
7. Agent should generate verification report

## Common Pitfalls

- Forgetting to wait for bazel-remote to start
- Using wrong cache URL format
- Not cleaning local cache before second build
- Incorrectly parsing build event JSON
- Not building all targets (missing `//...`)
- Not capturing build events with `--build_event_json_file`

