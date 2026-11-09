from pathlib import Path

import pytest


def write_project(root: Path, files: dict[str, str]) -> Path:
    for rel, content in files.items():
        f = root / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(content, encoding="utf-8")
    return root


@pytest.fixture
def sample_project(tmp_path):
    """Tienda con un ciclo pricing <-> tax y un módulo aislado."""
    return write_project(tmp_path / "proj", {
        "shop/__init__.py": "",
        "shop/main.py": "import os\nimport shop.cart\nfrom shop import utils\n",
        "shop/cart.py": "from shop.pricing import total\n",
        "shop/pricing.py": "from . import tax\n",
        "shop/tax.py": "from shop.pricing import total\nimport json\n",
        "shop/utils.py": "",
        "shop/lonely.py": "x = 1\n",
    })
