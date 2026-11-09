"""Crea el proyecto de ejemplo `examples/tienda` (8 módulos, 1 ciclo) usado en capturas y pruebas manuales."""
from pathlib import Path

FILES = {
    "tienda/__init__.py": "",
    "tienda/main.py": "import tienda.carrito\nfrom tienda import usuarios\n",
    "tienda/carrito.py": "from tienda.precios import total\nfrom tienda import inventario\n",
    "tienda/precios.py": "from . import impuestos\n",
    "tienda/impuestos.py": "from tienda.precios import total\n",
    "tienda/usuarios.py": "from tienda import notificaciones\n",
    "tienda/notificaciones.py": "",
    "tienda/inventario.py": "from tienda import notificaciones\n",
}

if __name__ == "__main__":
    for rel, content in FILES.items():
        f = Path("examples") / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(content, encoding="utf-8")
    print("examples/tienda creado")
