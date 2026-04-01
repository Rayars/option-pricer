import importlib.util
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent
MODULE_PATH = REPO_ROOT / "european-option.py"


def load_bs_function():
    spec = importlib.util.spec_from_file_location("european_option_module", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Failed to load european-option.py")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.BS


BS = load_bs_function()


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, body: dict[str, Any]) -> None:
        encoded = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.end_headers()
        self.wfile.write(encoded)

    def do_OPTIONS(self) -> None:
        self._send_json(200, {"ok": True})

    def do_POST(self) -> None:
        if self.path != "/api/european-option":
            self._send_json(404, {"error": "Not Found"})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(content_length) or b"{}")

            spot = float(payload["spot"])
            strike = float(payload["strike"])
            rate = float(payload["rate"])
            maturity = float(payload["maturity"])
            dividend_yield = float(payload["dividendYield"])
            sigma = float(payload["volatility"])

            if spot <= 0 or strike <= 0 or maturity <= 0 or sigma <= 0:
                raise ValueError("spot/strike/maturity/volatility must be positive")

            call_price = float(BS(spot, strike, rate, maturity, dividend_yield, sigma, "call"))
            put_price = float(BS(spot, strike, rate, maturity, dividend_yield, sigma, "put"))

            self._send_json(
                200,
                {
                    "callPrice": call_price,
                    "putPrice": put_price,
                },
            )
        except Exception as exc:
            self._send_json(400, {"error": str(exc)})


def run_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    httpd = ThreadingHTTPServer((host, port), Handler)
    print(f"Python pricing API running at http://{host}:{port}")
    httpd.serve_forever()


if __name__ == "__main__":
    run_server()
