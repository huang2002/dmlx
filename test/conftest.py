import sys
from pathlib import Path

import pytest

TEST_MODULE_PATH = str(Path(__file__).parent.parent.resolve())


@pytest.fixture()
def test_module() -> None:
    sys.path.append(TEST_MODULE_PATH)
