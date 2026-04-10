import importlib.util
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from implied_volatility import implied_volatility_newton
from Arithmetic_asian_option import Arith_MC_asian_option
from Geometric_asian_option import geo_CF_asian_option
from Arithmetic_basket_option import Arith_MC_basket_option
from Geometric_basket_option import geo_CF_basket_option
from KIKO_put_option import quasi_mc_kiko_put
from american_option import american_option


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
            elif self.path == "/api/basket-option":
                self._handle_basket_option(payload)
            elif self.path == "/api/american-option":
                self._handle_american_option(payload)
            elif self.path == "/api/kiko-put-option":
                self._handle_kiko_put_option(payload)
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

    def _handle_american_option(self, payload: dict[str, Any]) -> None:
        spot = float(payload["spot"])
        strike = float(payload["strike"])
        rate = float(payload["rate"])
        maturity = float(payload["maturity"])
        volatility = float(payload["volatility"])
        n_steps = int(payload.get("nSteps", 50))
        option_type = str(payload.get("optionType", "put")).lower()

        if option_type not in {"call", "put"}:
            raise ValueError("optionType must be 'call' or 'put'")
        if spot <= 0 or strike <= 0 or maturity <= 0 or volatility <= 0:
            raise ValueError("spot/strike/maturity/volatility must be positive")
        if n_steps <= 0:
            raise ValueError("nSteps must be a positive integer")

        price = float(american_option(spot, strike, rate, maturity, n_steps, volatility, option_type))
        self._send_json(200, {"price": price})

    def _handle_basket_option(self, payload: dict[str, Any]) -> None:
        spot1 = float(payload["spot1"])
        spot2 = float(payload["spot2"])
        strike = float(payload["strike"])
        rate = float(payload["rate"])
        maturity = float(payload["maturity"])
        volatility1 = float(payload["volatility1"])
        volatility2 = float(payload["volatility2"])
        correlation = float(payload["correlation"])
        n_paths = int(payload.get("nPaths", 100000))
        option_type = str(payload.get("optionType", "call")).lower()

        if option_type not in {"call", "put"}:
            raise ValueError("optionType must be 'call' or 'put'")
        if min(spot1, spot2, strike, maturity, volatility1, volatility2) <= 0:
            raise ValueError("spot/strike/maturity/volatility must be positive")
        if not -1.0 <= correlation <= 1.0:
            raise ValueError("correlation must be between -1 and 1")
        if n_paths <= 0:
            raise ValueError("nPaths must be a positive integer")

        geometric_value = float(
            geo_CF_basket_option(spot1, spot2, strike, rate, maturity, volatility1, volatility2, correlation, option_type)
        )
        standard_mc_value, control_variate_mc_value, standard_mc_ci, control_variate_ci = Arith_MC_basket_option(
            spot1,
            spot2,
            strike,
            rate,
            maturity,
            volatility1,
            volatility2,
            correlation,
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

    def _handle_kiko_put_option(self, payload: dict[str, Any]) -> None:
        spot = float(payload["spot"])
        strike = float(payload["strike"])
        rate = float(payload["rate"])
        maturity = float(payload["maturity"])
        volatility = float(payload["volatility"])
        lower_barrier = float(payload["lowerBarrier"])
        upper_barrier = float(payload["upperBarrier"])
        rebate = float(payload["rebate"])
        n_steps = int(payload.get("nSteps", 50))
        n_paths = int(payload.get("nPaths", 8192))
        spot_shift_value = payload.get("spotShift")
        spot_shift = float(spot_shift_value) if spot_shift_value is not None else None

        if min(spot, strike, maturity, volatility, lower_barrier, upper_barrier) <= 0:
            raise ValueError("spot/strike/maturity/volatility/barriers must be positive")
        if rebate < 0:
            raise ValueError("rebate must be non-negative")
        if n_steps <= 0 or n_paths <= 0:
            raise ValueError("nSteps and nPaths must be positive integers")
        if not lower_barrier < spot < upper_barrier:
            raise ValueError("lowerBarrier < spot < upperBarrier must hold")
        if spot_shift is not None and spot_shift <= 0:
            raise ValueError("spotShift must be positive")

        price, delta = quasi_mc_kiko_put(
            spot,
            strike,
            rate,
            maturity,
            volatility,
            lower_barrier,
            upper_barrier,
            n_steps,
            rebate,
            n_paths=n_paths,
            spot_shift=spot_shift,
        )
        self._send_json(200, {"price": float(price), "delta": float(delta)})


def run_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    httpd = ThreadingHTTPServer((host, port), Handler)
    print(f"Python pricing API running at http://{host}:{port}")
    httpd.serve_forever()


if __name__ == "__main__":
    run_server()
