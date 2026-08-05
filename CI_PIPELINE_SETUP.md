# CI Pipeline Setup Documentation

## Overview

This document describes the CI pipeline implementation for the RelaxiTaxi cab aggregator system project. The pipeline implements all required stages as per the project requirements.

## Pipeline Structure

The CI pipeline consists of 5 main stages:

1. **Build Stage** - Install dependencies and verify build
2. **Test Stage** - Run unit, integration, and system tests
3. **Coverage Stage** - Measure code coverage with 75% threshold
4. **Lint Stage** - Static code analysis with pylint (≥7.5/10) and flake8
5. **Security Scan Stage** - Security vulnerability scanning with bandit and safety

## Stage Details

### 1. Build Stage

**Purpose**: Install dependencies and verify the build completes successfully

**Actions**:
- Checks out code
- Sets up Python (3.9, 3.10, 3.11)
- Installs dependencies from `requirements.txt`
- Verifies all dependencies are installed correctly

**Success Criteria**:
- ✅ Dependencies install successfully
- ✅ Build completes without errors
- ✅ Environment setup is correct

### 2. Test Stage

**Purpose**: Execute all test suites (unit, integration, system tests)

**Actions**:
- Runs unit tests (`test_ride_utils.py`)
- Runs integration tests (`test_integration.py`)
- Runs all test suites together
- Uploads test results as artifacts

**Success Criteria**:
- ✅ Unit tests execute and pass
- ✅ Integration tests execute and pass
- ✅ All tests pass
- ✅ Test results are logged and visible

### 3. Coverage Stage

**Purpose**: Measure code coverage and enforce 75-80% threshold

**Actions**:
- Runs tests with coverage measurement
- Generates coverage reports (HTML, XML, terminal)
- Enforces 75% coverage threshold (fails if below)
- Extracts and displays coverage percentage
- Uploads coverage reports as artifacts

**Configuration**:
- Coverage threshold: **75%** (configurable in `pytest.ini`)
- Reports generated: HTML, XML, terminal

**Success Criteria**:
- ✅ Coverage report generated
- ✅ Meets 75% threshold (fails if below)
- ✅ HTML report saved as artifact
- ✅ Coverage metrics visible in logs

### 4. Lint Stage

**Purpose**: Static code analysis with pylint and flake8

**Actions**:
- Runs pylint on `src/` and `tests/` directories
- Extracts pylint score from report
- Enforces score ≥ 7.5/10 (fails if below)
- Runs flake8 for additional code quality checks
- Saves lint reports as artifacts

**Configuration**:
- Pylint configuration: `.pylintrc`
- Pylint threshold: **≥ 7.5/10**
- Flake8: Checks for syntax errors and code style

**Success Criteria**:
- ✅ Linting tool configured (pylint)
- ✅ Lint score ≥ 7.5/10 (enforced)
- ✅ Lint report saved as artifact
- ✅ Quality gates enforced (pipeline fails if below threshold)

### 5. Security Scan Stage

**Purpose**: Detect security vulnerabilities in code and dependencies

**Actions**:
- Runs Bandit security scanner on source code
- Scans for hardcoded secrets, SQL injection, etc.
- Runs Safety scanner on dependencies
- Checks for known CVEs in dependencies
- Saves security reports as artifacts

**Tools Used**:
- **Bandit**: Code security analysis
- **Safety**: Dependency vulnerability scanning

**Configuration**:
- Bandit config: `.bandit`
- Excludes test directories and virtual environments

**Success Criteria**:
- ✅ Security scanner runs successfully
- ✅ No critical vulnerabilities (or documented exceptions)
- ✅ Security report saved as artifact
- ✅ Scans both code and dependencies

## Pipeline Triggers

The pipeline runs automatically on:

- ✅ **Every push to any branch** (`branches: ['**']`)
- ✅ **Every Pull Request** to any branch
- ✅ **Prevents merge if checks fail** (enforced by GitHub branch protection rules)

## Artifacts Generated

The pipeline generates and saves the following artifacts:

1. **Test Results** - Test execution logs and results
2. **Coverage Reports** - HTML and XML coverage reports
3. **Lint Reports** - Pylint and Flake8 reports
4. **Security Reports** - Bandit and Safety scan reports

All artifacts are retained for 30 days and can be downloaded from the GitHub Actions interface.

## Configuration Files

### `requirements.txt`
Contains all project dependencies including:
- Core dependencies (streamlit, geopy, folium, etc.)
- Testing dependencies (pytest, pytest-cov, pytest-mock)
- Linting dependencies (pylint, flake8)
- Security scanning dependencies (bandit, safety)

### `pytest.ini`
Pytest configuration with:
- Test discovery settings
- Coverage configuration (75% threshold)
- Test markers (unit, integration, system)

### `.pylintrc`
Pylint configuration with:
- Code style rules
- Error suppression settings
- Scoring configuration

### `.bandit`
Bandit security scanner configuration with:
- Directory exclusions
- Skipped checks

## Quality Gates

The pipeline enforces the following quality gates:

1. **Coverage Threshold**: 75% (configurable)
2. **Pylint Score**: ≥ 7.5/10 (enforced)
3. **Security**: No critical vulnerabilities (warns on high severity)
4. **Tests**: All tests must pass

## Failure Behavior

- **Build Stage Failure**: Pipeline stops, no subsequent stages run
- **Test Stage Failure**: Pipeline stops, coverage stage does not run
- **Coverage Below Threshold**: Pipeline fails with error message
- **Pylint Score Below 7.5**: Pipeline fails with error message
- **Critical Security Issues**: Pipeline warns (can be configured to fail)

## Local Testing

To test the pipeline locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests with coverage
pytest tests/ -v --cov=src --cov-report=html --cov-fail-under=75

# Run pylint
pylint src/ tests/ --output-format=text --reports=yes --score=yes

# Run bandit
bandit -r src/ -f txt

# Run safety
safety check
```

## GitHub Branch Protection

To enable branch protection and prevent merges when CI fails:

1. Go to repository Settings → Branches
2. Add branch protection rule for `main` and `develop`
3. Enable "Require status checks to pass before merging"
4. Select the CI pipeline jobs:
   - `build`
   - `test`
   - `coverage`
   - `lint`
   - `security`

## Monitoring and Debugging

### Viewing Pipeline Results

1. Go to the **Actions** tab in GitHub
2. Click on a workflow run to see detailed logs
3. Download artifacts to view reports

### Common Issues

1. **Coverage below threshold**: Add more tests or adjust threshold
2. **Pylint score below 7.5**: Fix code quality issues or adjust `.pylintrc`
3. **Security vulnerabilities**: Review and fix security issues reported by bandit/safety
4. **Test failures**: Fix failing tests before merging

## Updates and Maintenance

### Updating Coverage Threshold

Edit `pytest.ini`:
```ini
--cov-fail-under=80  # Change from 75 to 80
```

### Updating Pylint Threshold

Edit `.github/workflows/ci.yml` in the lint stage:
```yaml
if score < 8.0:  # Change from 7.5 to 8.0
```

### Adding New Test Suites

Add test files to `tests/` directory and they will be automatically discovered by pytest.

## Conclusion

The CI pipeline is fully configured and meets all requirements:

- ✅ Build stage with dependency installation
- ✅ Test stage with unit and integration tests
- ✅ Coverage stage with 75% threshold enforcement
- ✅ Lint stage with pylint ≥ 7.5/10 enforcement
- ✅ Security scan stage with bandit and safety
- ✅ Runs on all branches and PRs
- ✅ Prevents merge on failure (with branch protection)

The pipeline ensures code quality, test coverage, and security before code is merged into the main branch.

