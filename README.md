# GrafoDeps

GrafoDeps analiza importaciones entre módulos Python y las presenta como un
grafo dirigido. Incluye una interfaz web local para explorar módulos,
dependencias y ciclos, además de una herramienta de línea de comandos.

## Requisitos

- Python 3.10 o posterior
- `pip`

## Instalación

Clona el repositorio y entra en su carpeta:

```powershell
git clone https://github.com/juandcontreras100-sketch/GrafoDeps.git
cd GrafoDeps
```

Crea un entorno virtual, actívalo e instala las dependencias:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

En macOS o Linux, activa el entorno con:

```sh
source .venv/bin/activate
```

## Explorador web

Inicia el servidor local:

```powershell
python -m grafodeps.webapp
```

Abre <http://127.0.0.1:8765> en el navegador. Escribe la ruta de una carpeta
con código Python y pulsa **Analizar proyecto**. Para detener el servidor,
presiona `Ctrl+C` en la terminal.

El servidor escucha solo en el equipo local. GrafoDeps inspecciona el código
estáticamente: no ejecuta el proyecto y no detecta de forma completa
importaciones dinámicas.

## Línea de comandos

Analiza el proyecto de ejemplo incluido:

```powershell
python -m grafodeps.cli examples
```

También puedes analizar una carpeta propia:

```powershell
python -m grafodeps.cli "C:\ruta\al\proyecto"
```

Para generar una imagen PNG del grafo:

```powershell
python -m grafodeps.cli examples --out grafo.png
```

La opción `--help` muestra las demás opciones, incluidas las de camino más
corto y dependencias transitivas.

## Ejemplo incluido

`examples/tienda/` es un proyecto pequeño de tienda que permite probar el
análisis. Incluye dependencias entre módulos y un ciclo entre `precios` e
`impuestos`.

## Pruebas

```powershell
python -m pytest -q
```

## Estructura principal

- `grafodeps/scanner.py`: descubre módulos y extrae importaciones reconocidas.
- `grafodeps/model.py`: construye el grafo y calcula ciclos, grados y caminos.
- `grafodeps/render.py`: dibuja el grafo como imagen.
- `grafodeps/cli.py`: interfaz de línea de comandos.
- `grafodeps/webapp.py` y `grafodeps/web/`: servidor local e interfaz web.
- `examples/`: proyecto de demostración.
- `tests/`: pruebas automatizadas.
