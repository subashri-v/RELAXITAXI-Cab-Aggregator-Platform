# Coverage Configuration Guide

## Overview

Coverage is configured in `.coveragerc`, the single source of truth used by the CI
pipeline, `pytest.ini`, and `check_coverage.py`. **Every module under `src/` is
measured**, so the number CI enforces is the real overall coverage.

## Current Coverage

All of `src/` is measured (app, pages, `db_utils`, `ride_utils`, `session_utils`,
`ui_helpers`), roughly 98% at the time of writing.

## Excluding a Module (rare)

If a module genuinely shouldn't be measured, add its pattern to the `omit` list in
`.coveragerc`:

- `*/pages/experimental.py` - excludes one file
- `*/pages/*.py` - excludes every page (wildcard)

New modules added to `src/` are measured automatically. No config change is needed.

## Coverage Threshold

The pipeline's Coverage Stage runs `pytest tests/ --cov-fail-under=75` against the
full suite, so it fails if **combined** coverage of all of `src/` drops below 75%.
The threshold is deliberately not in `pytest.ini`, because partial runs (e.g. the
Test Stage running one file) could never reach it.

## Checking Coverage Locally

```bash
python check_coverage.py        # full suite, same config as CI
# HTML report: htmlcov_full/index.html
```

or directly:

```bash
pytest tests/ --cov=src --cov-config=.coveragerc --cov-report=term-missing
```

## Testing Streamlit Pages

Pages are top-level scripts, so they are tested with Streamlit's `AppTest`
(see `tests/test_pages_apptest.py`). Two helpers make this work:

- `session_utils.goto` is stubbed, because `st.switch_page` can't resolve targets under AppTest.
- `time.sleep` is patched for the pages' poll-and-rerun loops.

## Files Involved

- **`.coveragerc`**: what is measured (all of `src/` minus the omit list)
- **`pytest.ini`**: test configuration and coverage report options
- **`.github/workflows/ci.yml`**: Coverage Stage (enforces 75%)
- **`check_coverage.py`**: local full-project coverage run
