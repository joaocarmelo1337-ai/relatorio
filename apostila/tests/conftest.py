import sys
from pathlib import Path

import pytest
import yaml

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from engine.normas import Normas  # noqa: E402


@pytest.fixture(scope="session")
def normas():
    return Normas.carregar(RAIZ / "config" / "normas.yaml")


@pytest.fixture
def cfg():
    with open(RAIZ / "config" / "exemplo_padrao.yaml", encoding="utf-8") as fh:
        return yaml.safe_load(fh)
