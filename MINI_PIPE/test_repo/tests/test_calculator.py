"""
Basic tests for calculator module.

Intentionally incomplete to give ACMS something to improve.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from calculator import add, subtract


def test_add():
    """Test addition."""
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
    assert add(0, 0) == 0


def test_subtract():
    """Test subtraction."""
    assert subtract(5, 3) == 2
    assert subtract(0, 0) == 0


# Missing tests for multiply and divide
# Missing edge case tests (division by zero, etc.)
