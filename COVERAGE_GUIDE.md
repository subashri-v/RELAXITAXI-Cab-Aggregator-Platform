# Coverage Configuration Guide

## Overview

Coverage measurement is configured via the `.coveragerc` file. This allows you to easily add new modules to coverage as you write tests for them, without needing to modify the CI pipeline.

## How It Works

1. **Single Source of Truth**: The `.coveragerc` file controls which modules are included in coverage measurement
2. **No CI Changes Needed**: When you add a new module, just update `.coveragerc` - the CI pipeline automatically picks it up
3. **Flexible**: Add or remove modules as needed without touching workflow files

## Current Coverage

Currently, coverage is measured for:
- `src/ride_utils.py` ✅

## Adding New Modules to Coverage

When you write tests for a new module and want to include it in coverage:

### Step 1: Write Tests
Create or update test files in the `tests/` directory for your module.

### Step 2: Update `.coveragerc`

Open `.coveragerc` and **remove** the module from the `omit` list:

```ini
[run]
omit =
    # Always exclude these
    */tests/*
    */test_*.py
    # ... other excludes ...
    
    # Modules to EXCLUDE from coverage (remove from this list to include them)
    */app.py
    */shared_state.py        # Remove this line to include shared_state.py
    */pages/book_ride.py     # Remove this line to include book_ride.py
    # ... etc
```

**Important**: To **include** a module, **remove** it from the `omit` list (or comment it out).

### Step 3: Commit and Push

That's it! The CI pipeline will automatically:
- Measure coverage for the new module
- Include it in the coverage report
- Enforce the 75% threshold on all included modules combined

## Examples

### Example 1: Adding `shared_state.py` to Coverage

1. Write tests in `tests/test_shared_state.py`
2. Edit `.coveragerc` and remove `*/shared_state.py` from the `omit` list:
   ```ini
   omit =
       # ... other excludes ...
       # */shared_state.py    # Commented out or removed - now included!
       */app.py
       # ... etc
   ```
3. Commit and push

### Example 2: Adding a Page Module

1. Write tests in `tests/test_book_ride.py`
2. Edit `.coveragerc` and remove `*/pages/book_ride.py` from the `omit` list:
   ```ini
   omit =
       # ... other excludes ...
       # */pages/book_ride.py    # Commented out or removed - now included!
       */pages/driver_view.py
       # ... etc
   ```
3. Commit and push

### Example 3: Adding Multiple Modules at Once

1. Write tests for multiple modules
2. Edit `.coveragerc` and remove all the modules you want to include:
   ```ini
   omit =
       # ... always exclude these ...
       
       # Modules to EXCLUDE from coverage
       # All of these are commented out, so they WILL be included:
       # */shared_state.py
       # */app.py
       # */pages/book_ride.py
       # */pages/driver_view.py
       # */pages/track_ride.py
       
       # Only ride_utils.py is not in omit list, so it's included
   ```
3. Commit and push

## Module Path Format

Use the following format in `.coveragerc` `omit` list:
- `*/ride_utils.py` - excludes `src/ride_utils.py`
- `*/shared_state.py` - excludes `src/shared_state.py`
- `*/pages/book_ride.py` - excludes `src/pages/book_ride.py`
- `*/pages/*.py` - excludes all files in `src/pages/` (wildcard)

**Remember**: To **include** a module in coverage, **remove** it from the `omit` list!

## Coverage Threshold

The coverage threshold is set to **75%** in `pytest.ini`. This applies to the **combined coverage** of all modules listed in `.coveragerc`.

For example:
- If you have `ride_utils.py` at 100% and `shared_state.py` at 50%, the combined coverage might be 75% (depending on file sizes)
- The pipeline will pass if the combined coverage is ≥ 75%

## Verifying Coverage Locally

Run coverage locally to verify before pushing:

```bash
# Run tests with coverage
pytest tests/ -v --cov=src --cov-config=.coveragerc --cov-report=term --cov-report=html

# View HTML report
# Open htmlcov/index.html in your browser
```

## Troubleshooting

### Module Not Included in Coverage

**Problem**: You removed a module from the `omit` list but it's not showing in coverage reports.

**Solution**: 
1. Check that you actually removed it from the `omit` list (not just commented it)
2. Verify the path format in `.coveragerc` matches the actual file path
3. Make sure you're using `--cov-config=.coveragerc` in pytest commands
4. Verify the file exists and is in the `src/` directory
5. Run coverage locally to test: `pytest tests/ --cov=src --cov-config=.coveragerc --cov-report=term`

### Coverage Below 75%

**Problem**: Coverage is below the 75% threshold.

**Solution**:
1. Write more tests for the modules
2. Check which lines are not covered (use `--cov-report=term-missing`)
3. Consider if you need to add all modules, or just the well-tested ones

### Want to Remove a Module from Coverage

**Problem**: You want to stop measuring coverage for a module.

**Solution**: Simply add the module path back to the `omit` list in `.coveragerc`.

## Best Practices

1. **Add modules gradually**: Start with modules that have good test coverage
2. **Keep tests up to date**: As you add modules to coverage, ensure they have adequate tests
3. **Review coverage reports**: Regularly check which lines are not covered
4. **Document changes**: When adding modules, consider updating this guide if needed

## Files Involved

- **`.coveragerc`**: Configuration file that specifies which modules to include
- **`pytest.ini`**: Test configuration (includes coverage settings)
- **`.github/workflows/ci.yml`**: CI pipeline (uses `.coveragerc` automatically)

## Summary

✅ **To add a module**: Edit `.coveragerc`, **remove** the module path from the `omit` list  
✅ **No CI changes needed**: The pipeline automatically uses `.coveragerc`  
✅ **Single source of truth**: All coverage configuration in one file  
✅ **Flexible**: Easy to add or remove modules as needed  
✅ **Simple workflow**: Write tests → Remove from omit list → Commit → Done!

