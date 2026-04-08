# Insights: Python Refactoring Patterns

## Success Patterns

### Structured Logging Without Dependencies
**Finding**: Custom StructuredLogger wrapper works well without adding structlog dependency
**Evidence**: Built minimal wrapper in 20 lines that handles structured key=value format
**Action**: Use custom StructuredLogger for simple structured logging needs
**Impact**: Medium (avoids dependency, sufficient for most use cases)

### Pydantic Settings Over Manual Singleton
**Finding**: Pydantic Settings provides validation, env vars, and type safety automatically
**Evidence**: Replaced 25-line singleton config with 20-line Pydantic Settings
**Action**: Always prefer Pydantic Settings for configuration management
**Impact**: High (better testing, validation, type safety)

### Shared Utils Module
**Finding**: Consolidating duplicate functions (parse_time, parse_duration) into utils.py reduces bugs
**Evidence**: Both scheduler.py and status.py had identical implementations
**Action**: Create utils.py for shared functions before implementing in multiple files
**Impact**: High (prevents bugs from code drift)

## Failure Patterns

### Config Mock Path Changes
**Finding**: Refactoring config from `config.config` to `settings` breaks existing test mocks
**Evidence**: 7 tests failed because mock path `config.config.pools_config` no longer valid
**Action**: When refactoring config, immediately update test mocks to new import path
**Impact**: High (caused 15 min delay in testing phase)

### HTTPError Import in Tests
**Finding**: Mocking httpx exceptions requires importing httpx.HTTPError explicitly
**Evidence**: Test failed with TypeError when mocking generic Exception instead of httpx.HTTPError
**Action**: When testing httpx-based code, import and mock httpx.HTTPError explicitly
**Impact**: Medium (caused test failure)

### Bare Except Clauses
**Finding**: Original code had bare `except:` that swallows all exceptions
**Evidence**: api.py broadcast() used bare except
**Action**: Always use `except Exception:` for explicit exception handling
**Impact**: High (security/correctness issue)

## Efficiency Patterns

### Priority-Ordered Refactoring
**Finding**: Following high → medium → low priority order prevents scope creep
**Evidence**: Completed critical fixes (bare except, logging) before medium (utils, config)
**Action**: Always define priority order before starting refactoring
**Impact**: Medium (ensures critical issues addressed first)

### Docker-Based Testing
**Finding**: Docker test image provides consistent environment, catches dependency issues
**Evidence**: Test failures revealed pydantic-settings missing from requirements initially
**Action**: Always rebuild Docker image after dependency changes
**Impact**: High (prevents CI failures)
