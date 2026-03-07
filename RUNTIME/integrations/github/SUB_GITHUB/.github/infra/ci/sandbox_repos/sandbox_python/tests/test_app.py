# DOC_LINK: DOC-TEST-TESTS-TEST-APP-115
import sys
from pathlib import Path

_SRC_PATH = Path(__file__).resolve().parents[1] / "src"
if str(_SRC_PATH) not in sys.path:
    )

from src.app import add


def test_add():
    assert add(1, 2) == 3

