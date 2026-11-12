"""Servidor HTTP local para el explorador interactivo de GrafoDeps."""
import argparse
import ast
import json
import tokenize
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import TypedDict
from urllib.parse import urlsplit

from grafodeps.model import build_digraph, degree_report, find_cycles
from grafodeps.scanner import find_modules, scan_project

WEB_ROOT = Path(__file__).with_name("web")
MAX_REQUEST_BYTES = 8192
MAX_DEFINITIONS_PER_MODULE = 40
MAX_METHODS_PER_CLASS = 30
MAX_DOCSTRING_LENGTH = 360


class Edge(TypedDict):
    source: str
    target: str


class GraphPayload(TypedDict):
    project: str
    modules: list[str]
    edges: list[Edge]
    cycles: list[list[str]]
    degrees: dict[str, dict[str, int]]
    analysis: dict[str, dict]


def _short_text(text: str, limit: int = MAX_DOCSTRING_LENGTH) -> str:
    normalized = " ".join(text.split())
    return normalized if len(normalized) <= limit else normalized[: limit - 3].rstrip() + "..."


def _function_signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    return f"({_short_text(ast.unparse(node.args), 240)})"


def _method_analysis(node: ast.FunctionDef | ast.AsyncFunctionDef) -> dict:
    return {
        "name": node.name,
        "signature": _function_signature(node),
        "line": node.lineno,
        "description": _short_text(ast.get_docstring(node) or ""),
    }


def _definition_analysis(node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) -> dict:
    if isinstance(node, ast.ClassDef):
        methods = [
            item for item in node.body
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        return {
            "kind": "Clase",
            "name": node.name,
            "signature": "",
            "line": node.lineno,
            "description": _short_text(ast.get_docstring(node) or ""),
            "decorators": [ast.unparse(decorator) for decorator in node.decorator_list],
            "methods": [_method_analysis(method) for method in methods[:MAX_METHODS_PER_CLASS]],
            "omitted_methods": max(0, len(methods) - MAX_METHODS_PER_CLASS),
        }

    kind = "Función asíncrona" if isinstance(node, ast.AsyncFunctionDef) else "Función"
    return {
        "kind": kind,
        "name": node.name,
        "signature": _function_signature(node),
        "line": node.lineno,
        "description": _short_text(ast.get_docstring(node) or ""),
        "decorators": [ast.unparse(decorator) for decorator in node.decorator_list],
        "methods": [],
        "omitted_methods": 0,
    }


def _module_summary(module_docstring: str | None, nodes: list[ast.AST]) -> str:
    if module_docstring:
        return _short_text(module_docstring)
    if not nodes:
        return (
            "No declara funciones ni clases a nivel de módulo; puede contener "
            "importaciones, constantes o código de inicialización."
        )

    grouped = []
    for kind, singular, plural in (
        ("Función", "función", "funciones"),
        ("Función asíncrona", "función asíncrona", "funciones asíncronas"),
        ("Clase", "clase", "clases"),
    ):
        names = [node.name for node in nodes if (
            (kind == "Clase" and isinstance(node, ast.ClassDef))
            or (kind == "Función" and isinstance(node, ast.FunctionDef))
            or (kind == "Función asíncrona" and isinstance(node, ast.AsyncFunctionDef))
        )]
        if names:
            count = len(names)
            shown_names = ", ".join(names[:3])
            if count > 3:
                shown_names += f" y {count - 3} más"
            noun = singular if count == 1 else plural
            grouped.append(f"{count} {noun} ({shown_names})")
    return "Declara " + " y ".join(grouped) + "."


def analyze_module(source_file: Path) -> dict:
    with tokenize.open(source_file) as source:
        tree = ast.parse(source.read(), filename=str(source_file))

    module_docstring = ast.get_docstring(tree)
    nodes = [
        node for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    ]
    return {
        "summary": _module_summary(module_docstring, nodes),
        "definitions": [_definition_analysis(node) for node in nodes[:MAX_DEFINITIONS_PER_MODULE]],
        "omitted_definitions": max(0, len(nodes) - MAX_DEFINITIONS_PER_MODULE),
    }


class APIError(Exception):
    def __init__(self, status: int, code: str, message: str):
        super().__init__(message)
        self.status = status
        self.code = code


def build_payload(project: str | Path) -> GraphPayload:
    raw_project = str(project).strip()
    if not raw_project or len(raw_project) > 4096:
        raise APIError(400, "INVALID_PROJECT", "Indica una ruta de carpeta válida.")

    try:
        root = Path(raw_project).expanduser().resolve(strict=True)
    except (OSError, RuntimeError):
        raise APIError(400, "INVALID_PROJECT", "No se encontró la carpeta del proyecto.") from None

    if not root.is_dir():
        raise APIError(400, "INVALID_PROJECT", "La ruta seleccionada no es una carpeta.")

    try:
        modules, edges = scan_project(root)
        module_files = find_modules(root)
        analysis = {module: analyze_module(module_files[module]) for module in modules}
        for module in modules:
            analysis[module]["imports"] = sorted(target for source, target in edges if source == module)
            analysis[module]["imported_by"] = sorted(source for source, target in edges if target == module)
    except SyntaxError:
        raise APIError(422, "SYNTAX_ERROR", "Un archivo Python del proyecto tiene sintaxis inválida.") from None
    except (OSError, UnicodeError):
        raise APIError(422, "ANALYSIS_ERROR", "No se pudo leer uno o más archivos Python del proyecto.") from None

    if not modules:
        raise APIError(422, "EMPTY_PROJECT", "La carpeta no contiene módulos Python analizables.")

    graph = build_digraph(modules, edges)
    return {
        "project": root.name or str(root),
        "modules": modules,
        "edges": [{"source": source, "target": target} for source, target in edges],
        "cycles": find_cycles(graph),
        "degrees": degree_report(graph),
        "analysis": analysis,
    }


class GraphRequestHandler(SimpleHTTPRequestHandler):
    server_version = "GrafoDepsLocal/1.0"
    sys_version = ""

    def __init__(self, *args, directory: str | None = None, **kwargs):
        super().__init__(*args, directory=directory or str(WEB_ROOT), **kwargs)

    def _send_security_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "img-src 'self' data: blob:; connect-src 'self'; object-src 'none'; "
            "base-uri 'none'; frame-ancestors 'none'",
        )
        self.send_header("Cache-Control", "no-store")

    def end_headers(self):
        self._send_security_headers()
        super().end_headers()

    def _local_origin_allowed(self) -> bool:
        port = self.server.server_port
        allowed_hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
        host = self.headers.get("Host", "")
        if host not in allowed_hosts:
            return False
        origin = self.headers.get("Origin")
        return origin is None or origin == f"http://{host}"

    def _send_json(self, status: int, data: dict):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if not self._local_origin_allowed():
            self._send_json(421, {"error": {"code": "MISDIRECTED_REQUEST", "message": "Solicitud no permitida."}})
            return
        if urlsplit(self.path).path.startswith("/api/"):
            self._send_json(404, {"error": {"code": "NOT_FOUND", "message": "Recurso no encontrado."}})
            return
        super().do_GET()

    def do_POST(self):
        if not self._local_origin_allowed():
            self._send_json(421, {"error": {"code": "MISDIRECTED_REQUEST", "message": "Solicitud no permitida."}})
            return
        if urlsplit(self.path).path != "/api/analyze":
            self._send_json(404, {"error": {"code": "NOT_FOUND", "message": "Recurso no encontrado."}})
            return
        if self.headers.get_content_type() != "application/json":
            self._send_json(415, {"error": {"code": "UNSUPPORTED_MEDIA_TYPE", "message": "Se requiere application/json."}})
            return

        try:
            content_length = int(self.headers.get("Content-Length", ""))
        except ValueError:
            self._send_json(400, {"error": {"code": "INVALID_REQUEST", "message": "Longitud de solicitud inválida."}})
            return
        if content_length < 0:
            self._send_json(400, {"error": {"code": "INVALID_REQUEST", "message": "Longitud de solicitud inválida."}})
            return
        if content_length > MAX_REQUEST_BYTES:
            self._send_json(413, {"error": {"code": "REQUEST_TOO_LARGE", "message": "La solicitud supera el tamaño permitido."}})
            return

        try:
            request_data = json.loads(self.rfile.read(content_length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send_json(400, {"error": {"code": "INVALID_JSON", "message": "El cuerpo no contiene JSON válido."}})
            return
        if not isinstance(request_data, dict) or set(request_data) != {"project"} or not isinstance(request_data["project"], str):
            self._send_json(400, {"error": {"code": "INVALID_REQUEST", "message": "Se requiere un campo project de tipo texto."}})
            return

        try:
            payload = build_payload(request_data["project"])
        except APIError as error:
            self._send_json(error.status, {"error": {"code": error.code, "message": str(error)}})
            return
        self._send_json(200, payload)

    def log_message(self, format, *args):
        if self.command == "GET":
            super().log_message(format, *args)


def create_server(host: str = "127.0.0.1", port: int = 8765) -> ThreadingHTTPServer:
    if host not in {"127.0.0.1", "localhost"}:
        raise ValueError("El servidor del explorador solo puede escuchar en loopback.")
    handler = partial(GraphRequestHandler, directory=str(WEB_ROOT))
    server = ThreadingHTTPServer((host, port), handler)
    server.daemon_threads = True
    return server


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inicia el explorador web local de GrafoDeps.")
    parser.add_argument("--port", type=int, default=8765, help="puerto local (predeterminado: 8765)")
    args = parser.parse_args(argv)
    server = create_server(port=args.port)
    url = f"http://127.0.0.1:{server.server_port}"
    print(f"Explorador GrafoDeps: {url}")
    print("Para detenerlo, presiona Ctrl+C en esta terminal.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
