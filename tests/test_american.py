"""Tests for American option pricing (CRR binomial tree)."""

import math
import pytest
from option_pricer import AmericanOption, EuropeanOption


ATM_PARAMS = dict(S=100, K=100, T=1.0, r=0.05, sigma=0.20)


class TestAmericanCallPrice:
    def test_call_price_positive(self):
        opt = AmericanOption(**ATM_PARAMS, option_type="call")
        assert opt.price() > 0

    def test_call_price_at_least_intrinsic(self):
        opt = AmericanOption(S=110, K=100, T=1.0, r=0.05, sigma=0.20, option_type="call")
        assert opt.price() >= 10.0

    def test_call_price_increases_with_spot(self):
        prices = [
            AmericanOption(S=s, K=100, T=1.0, r=0.05, sigma=0.20, option_type="call").price()
            for s in [80, 90, 100, 110, 120]
        ]
        assert prices == sorted(prices)


class TestAmericanPutPrice:
    def test_put_price_positive(self):
        opt = AmericanOption(**ATM_PARAMS, option_type="put")
        assert opt.price() > 0

    def test_put_price_at_least_intrinsic(self):
        opt = AmericanOption(S=90, K=100, T=1.0, r=0.05, sigma=0.20, option_type="put")
        assert opt.price() >= 10.0

    def test_put_price_decreases_with_spot(self):
        prices = [
            AmericanOption(S=s, K=100, T=1.0, r=0.05, sigma=0.20, option_type="put").price()
            for s in [80, 90, 100, 110, 120]
        ]
        assert prices == sorted(prices, reverse=True)


class TestAmericanVsEuropean:
    """American options are worth at least as much as their European counterparts."""

    def test_american_call_ge_european_call_no_dividend(self):
        """Without dividends the American call equals the European call."""
        am = AmericanOption(**ATM_PARAMS, option_type="call", n_steps=500).price()
        eu = EuropeanOption(**ATM_PARAMS, option_type="call").price()
        # American ≥ European; without dividends they should be very close.
        assert am >= eu - 0.01  # allow tiny numerical tolerance

    def test_american_put_ge_european_put(self):
        am = AmericanOption(**ATM_PARAMS, option_type="put", n_steps=500).price()
        eu = EuropeanOption(**ATM_PARAMS, option_type="put").price()
        assert am >= eu - 0.01

    def test_american_put_strictly_greater_deep_itm(self):
        """Deep ITM American put should be worth more than European put."""
        am = AmericanOption(S=60, K=100, T=1.0, r=0.10, sigma=0.20,
                            option_type="put", n_steps=500).price()
        eu = EuropeanOption(S=60, K=100, T=1.0, r=0.10, sigma=0.20,
                            option_type="put").price()
        assert am > eu

    def test_american_call_with_dividend_ge_european(self):
        params = dict(S=100, K=100, T=1.0, r=0.05, sigma=0.20, q=0.08)
        am = AmericanOption(**params, option_type="call", n_steps=500).price()
        eu = EuropeanOption(**params, option_type="call").price()
        assert am >= eu - 0.01


class TestAmericanPriceConvergence:
    """Price should converge to the Black-Scholes European price for calls
    (no dividends) as n_steps increases."""

    def test_convergence_atm_call(self):
        eu = EuropeanOption(**ATM_PARAMS, option_type="call").price()
        am = AmericanOption(**ATM_PARAMS, option_type="call", n_steps=1000).price()
        assert math.isclose(am, eu, rel_tol=0.01)  # within 1 %


class TestAmericanValidation:
    def test_negative_spot_raises(self):
        with pytest.raises(ValueError):
            AmericanOption(S=-1, K=100, T=1, r=0.05, sigma=0.20)

    def test_zero_steps_raises(self):
        with pytest.raises(ValueError):
            AmericanOption(S=100, K=100, T=1, r=0.05, sigma=0.20, n_steps=0)

    def test_invalid_option_type_raises(self):
        with pytest.raises(ValueError):
            AmericanOption(S=100, K=100, T=1, r=0.05, sigma=0.20, option_type="barrier")
