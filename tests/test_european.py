"""Tests for European option pricing (Black-Scholes)."""

import math
import pytest
from option_pricer import EuropeanOption


# ---------------------------------------------------------------------------
# Reference values computed with the standard Black-Scholes formula
# S=100, K=100, T=1, r=0.05, sigma=0.20 (ATM, no dividends)
# Call  ≈ 10.4506
# Put   ≈  5.5735
# ---------------------------------------------------------------------------

ATM_PARAMS = dict(S=100, K=100, T=1.0, r=0.05, sigma=0.20)


class TestEuropeanCallPrice:
    def test_atm_call_price(self):
        opt = EuropeanOption(**ATM_PARAMS, option_type="call")
        assert math.isclose(opt.price(), 10.4506, abs_tol=1e-3)

    def test_itm_call_price_greater_than_intrinsic(self):
        opt = EuropeanOption(S=110, K=100, T=1.0, r=0.05, sigma=0.20, option_type="call")
        assert opt.price() > 10.0  # intrinsic value

    def test_otm_call_price_positive(self):
        opt = EuropeanOption(S=90, K=100, T=1.0, r=0.05, sigma=0.20, option_type="call")
        assert opt.price() > 0

    def test_call_price_increases_with_spot(self):
        prices = [
            EuropeanOption(S=s, K=100, T=1.0, r=0.05, sigma=0.20, option_type="call").price()
            for s in [80, 90, 100, 110, 120]
        ]
        assert prices == sorted(prices)

    def test_call_price_increases_with_volatility(self):
        prices = [
            EuropeanOption(S=100, K=100, T=1.0, r=0.05, sigma=s, option_type="call").price()
            for s in [0.10, 0.20, 0.30, 0.40]
        ]
        assert prices == sorted(prices)


class TestEuropeanPutPrice:
    def test_atm_put_price(self):
        opt = EuropeanOption(**ATM_PARAMS, option_type="put")
        assert math.isclose(opt.price(), 5.5735, abs_tol=1e-3)

    def test_put_price_positive(self):
        opt = EuropeanOption(S=90, K=100, T=1.0, r=0.05, sigma=0.20, option_type="put")
        assert opt.price() > 0


class TestPutCallParity:
    """C - P = S*e^(-qT) - K*e^(-rT)."""

    def test_put_call_parity_no_dividend(self):
        call = EuropeanOption(**ATM_PARAMS, option_type="call").price()
        put = EuropeanOption(**ATM_PARAMS, option_type="put").price()
        S, K, r, T = 100, 100, 0.05, 1.0
        expected = S - K * math.exp(-r * T)
        assert math.isclose(call - put, expected, abs_tol=1e-8)

    def test_put_call_parity_with_dividend(self):
        params = dict(S=100, K=100, T=1.0, r=0.05, sigma=0.20, q=0.02)
        call = EuropeanOption(**params, option_type="call").price()
        put = EuropeanOption(**params, option_type="put").price()
        S, K, r, q, T = 100, 100, 0.05, 0.02, 1.0
        expected = S * math.exp(-q * T) - K * math.exp(-r * T)
        assert math.isclose(call - put, expected, abs_tol=1e-8)


class TestEuropeanGreeks:
    def test_call_delta_between_zero_and_one(self):
        opt = EuropeanOption(**ATM_PARAMS, option_type="call")
        assert 0 < opt.delta() < 1

    def test_put_delta_between_minus_one_and_zero(self):
        opt = EuropeanOption(**ATM_PARAMS, option_type="put")
        assert -1 < opt.delta() < 0

    def test_gamma_positive(self):
        for otype in ("call", "put"):
            opt = EuropeanOption(**ATM_PARAMS, option_type=otype)
            assert opt.gamma() > 0

    def test_vega_positive(self):
        for otype in ("call", "put"):
            opt = EuropeanOption(**ATM_PARAMS, option_type=otype)
            assert opt.vega() > 0

    def test_call_theta_negative(self):
        opt = EuropeanOption(**ATM_PARAMS, option_type="call")
        assert opt.theta() < 0

    def test_call_rho_positive(self):
        opt = EuropeanOption(**ATM_PARAMS, option_type="call")
        assert opt.rho() > 0

    def test_put_rho_negative(self):
        opt = EuropeanOption(**ATM_PARAMS, option_type="put")
        assert opt.rho() < 0

    def test_greeks_dict_keys(self):
        opt = EuropeanOption(**ATM_PARAMS)
        g = opt.greeks()
        assert set(g.keys()) == {"delta", "gamma", "vega", "theta", "rho"}

    def test_atm_call_delta_near_half(self):
        opt = EuropeanOption(**ATM_PARAMS, option_type="call")
        assert math.isclose(opt.delta(), 0.6368, abs_tol=1e-3)


class TestEuropeanValidation:
    def test_negative_spot_raises(self):
        with pytest.raises(ValueError):
            EuropeanOption(S=-1, K=100, T=1, r=0.05, sigma=0.20)

    def test_zero_strike_raises(self):
        with pytest.raises(ValueError):
            EuropeanOption(S=100, K=0, T=1, r=0.05, sigma=0.20)

    def test_zero_time_raises(self):
        with pytest.raises(ValueError):
            EuropeanOption(S=100, K=100, T=0, r=0.05, sigma=0.20)

    def test_zero_volatility_raises(self):
        with pytest.raises(ValueError):
            EuropeanOption(S=100, K=100, T=1, r=0.05, sigma=0)

    def test_invalid_option_type_raises(self):
        with pytest.raises(ValueError):
            EuropeanOption(S=100, K=100, T=1, r=0.05, sigma=0.20, option_type="future")
