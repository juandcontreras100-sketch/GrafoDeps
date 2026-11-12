import json
import threading
from http.client import HTTPConnection
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from grafodeps.webapp import build_payload, create_server


def test_build_payload_exposes_graph_cycles_and_degrees(sample_project):
    payload = build_payload(sample_project)

    assert payload["project"] == "proj"
    assert {"source": "shop.cart", "target": "shop.pricing"} in payload["edges"]
    assert payload["cycles"] == [["shop.pricing", "shop.tax"]]
    assert payload["degrees"]["shop.pricing"] == {"in": 2, "out": 1}
    assert payload["analysis"]["shop.cart"]["imports"] == ["shop.pricing"]
    assert payload["analysis"]["shop.cart"]["imported_by"] == ["shop.main"]
    assert payload["analysis"]["shop.main"]["summary"] == "No declara funciones ni clases a nivel de módulo; puede contener importaciones, constantes o código de inicialización."


def test_module_analysis_describes_docstrings_and_top_level_definitions(sample_project):
    source = sample_project / "shop" / "main.py"
    source.write_text(
        '"""Coordina el cálculo de una compra."""\n'
        "def calculate_total(items, tax_rate=0):\n"
        '    """Suma los productos y calcula el impuesto."""\n'
        "    return sum(items) * (1 + tax_rate)\n"
        "class Receipt:\n"
        '    """Representa el recibo de una compra."""\n'
        "    def render(self):\n"
        '        """Devuelve el recibo como texto."""\n'
        "        return 'receipt'\n",
        encoding="utf-8",
    )

    payload = build_payload(sample_project)
    analysis = payload["analysis"]["shop.main"]

    assert analysis["summary"] == "Coordina el cálculo de una compra."
    assert analysis["definitions"] == [
        {
            "kind": "Función",
            "name": "calculate_total",
            "signature": "(items, tax_rate=0)",
            "line": 2,
            "description": "Suma los productos y calcula el impuesto.",
            "decorators": [],
            "methods": [],
            "omitted_methods": 0,
        },
        {
            "kind": "Clase",
            "name": "Receipt",
            "signature": "",
            "line": 5,
            "description": "Representa el recibo de una compra.",
            "decorators": [],
            "methods": [
                {
                    "name": "render",
                    "signature": "(self)",
                    "line": 7,
                    "description": "Devuelve el recibo como texto.",
                },
            ],
            "omitted_methods": 0,
        },
    ]


def test_module_analysis_falls_back_to_observed_structure_without_docstrings(sample_project):
    source = sample_project / "shop" / "main.py"
    source.write_text("def calculate_total(items):\n    return sum(items)\n", encoding="utf-8")

    analysis = build_payload(sample_project)["analysis"]["shop.main"]

    assert analysis["summary"] == "Declara 1 función (calculate_total)."
    assert analysis["definitions"][0]["description"] == ""


def test_local_server_serves_ui_and_analyzes_selected_project(sample_project):
    server = create_server(port=0)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"

    try:
        with urlopen(base_url) as response:
            page = response.read().decode("utf-8")
            assert response.status == 200
            assert "GrafoDeps" in page
            assert "¿Qué hace este módulo?" in page
            assert "Importaciones directas" in page
            assert "Importado directamente por" in page
            assert "img-src 'self' data: blob:" in response.headers["Content-Security-Policy"]

        request = Request(
            f"{base_url}/api/analyze",
            data=json.dumps({"project": str(sample_project)}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request) as response:
            result = json.loads(response.read())

        assert response.status == 200
        assert result["project"] == "proj"
        assert len(result["modules"]) == 7
        assert len(result["edges"]) == 5
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def test_api_rejects_missing_project_with_structured_error():
    server = create_server(port=0)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"

    try:
        request = Request(
            f"{base_url}/api/analyze",
            data=json.dumps({"project": "Z:\\folder-that-does-not-exist"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with pytest.raises(HTTPError) as error:
            urlopen(request)

        assert error.value.code == 400
        body = json.loads(error.value.read())
        assert body["error"]["code"] == "INVALID_PROJECT"
        assert "stack" not in body["error"]["message"].lower()
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def test_server_rejects_requests_with_untrusted_host_header():
    server = create_server(port=0)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()

    try:
        connection = HTTPConnection("127.0.0.1", server.server_port)
        connection.request("GET", "/", headers={"Host": "attacker.example"})
        response = connection.getresponse()

        assert response.status == 421
        connection.close()
    finally:
        server.shutdown()
        thread.join()
        server.server_close()
