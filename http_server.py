import importlib.util
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from implied_volatility import implied_volatility_newton
from Arithmetic_asian_option import Arith_MC_asian_option
from Geometric_asian_option import geo_CF_asian_option


REPO_ROOT = Path(__file__).resolve().parent
MODULE_PATH = REPO_ROOT / "european_option.py"


def load_bs_function():
    spec = importlib.util.spec_from_file_location("european_option_module", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Failed to load european_option.py")

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
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(content_length) or b"{}")

            if self.path == "/api/european-option":
                self._handle_european_option(payload)
            elif self.path == "/api/implied-volatility":
                self._handle_implied_volatility(payload)
            elif self.path == "/api/asian-option":
                self._handle_asian_option(payload)
            else:
                self._send_json(404, {"error": "Not Found"})
        except Exception as exc:
            self._send_json(400, {"error": str(exc)})

    def _handle_european_option(self, payload: dict[str, Any]) -> None:
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

    def _handle_implied_volatility(self, payload: dict[str, Any]) -> None:
        spot = float(payload["spot"])
        strike = float(payload["strike"])
        rate = float(payload["rate"])
        maturity = float(payload["maturity"])
        dividend_yield = float(payload["dividendYield"])
        market_price = float(payload["marketPrice"])
        option_type = str(payload.get("optionType", "call")).lower()

        if option_type not in {"call", "put"}:
            raise ValueError("optionType must be 'call' or 'put'")
        if spot <= 0 or strike <= 0 or maturity <= 0:
            raise ValueError("spot/strike/maturity must be positive")
        if market_price <= 0:
            raise ValueError("marketPrice must be positive")

        sigma = float(
            implied_volatility_newton(
                spot,
                strike,
                rate,
                maturity,
                dividend_yield,
                market_price,
                option_type,
            )
        )

        if sigma <= 0:
            raise ValueError("failed to converge to a positive implied volatility")

        self._send_json(200, {"impliedVolatility": sigma})

    def _handle_asian_option(self, payload: dict[str, Any]) -> None:
        spot = float(payload["spot"])
        strike = float(payload["strike"])
        rate = float(payload["rate"])
        maturity = float(payload["maturity"])
        volatility = float(payload["volatility"])
        n_steps = int(payload.get("nSteps", 50))
        n_paths = int(payload.get("nPaths", 10000))
        option_type = str(payload.get("optionType", "call")).lower()

        if option_type not in {"call", "put"}:
            raise ValueError("optionType must be 'call' or 'put'")
        if spot <= 0 or strike <= 0 or maturity <= 0 or volatility <= 0:
            raise ValueError("spot/strike/maturity/volatility must be positive")
        if n_steps <= 0 or n_paths <= 0:
            raise ValueError("nSteps and nPaths must be positive integers")

        geometric_value = float(geo_CF_asian_option(spot, strike, rate, maturity, n_steps, volatility, option_type))
        standard_mc_value, control_variate_mc_value, standard_mc_ci, control_variate_ci = Arith_MC_asian_option(
            spot,
            strike,
            rate,
            maturity,
            n_steps,
            volatility,
            option_type=option_type,
            m_paths=n_paths,
        )
        self._send_json(
            200,
            {
                "geometricValue": geometric_value,
                "standardMcValue": float(standard_mc_value),
                "controlVariateMcValue": float(control_variate_mc_value),
                "standardMcConfidenceInterval": [float(standard_mc_ci[0]), float(standard_mc_ci[1])],
                "controlVariateConfidenceInterval": [float(control_variate_ci[0]), float(control_variate_ci[1])],
            },
        )


def run_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    httpd = ThreadingHTTPServer((host, port), Handler)
    print(f"Python pricing API running at http://{host}:{port}")
    httpd.serve_forever()


if __name__ == "__main__":
    run_server()
