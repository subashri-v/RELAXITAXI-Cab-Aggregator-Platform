"""Measure overall test coverage across all of src/ (same config as the CI pipeline).

Usage:  python check_coverage.py
"""
import subprocess
import sys

result = subprocess.run(
    [
        sys.executable, "-m", "pytest", "tests/",
        "--cov=src",
        "--cov-config=.coveragerc",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov_full",
        "-q",
    ],
    check=False,
)
print("\nHTML report: htmlcov_full/index.html")
sys.exit(result.returncode)
