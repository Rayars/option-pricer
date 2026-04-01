"""Tests for Asian option pricing."""

import math
import pytest
from option_pricer import AsianOption


ATM_PARAMS = dict(S=100, K=100, T=1.0, r=0.05, sigma=0.20, n_steps=252)


class TestAsianGeometricClosedForm:
    """Geometric Asian options have a known closed-form solution."""

    def test_call_price_positive(self):
        opt = AsianOption(**ATM_PARAMS, option_type="call", averaging="geometric")
        assert opt.price() > 0

    def test_put_price_positive(self):
        opt = AsianOption(**ATM_PARAMS, option_type="put", averaging="geometric")
        assert opt.price() > 0

    def test_geometric_call_less_than_european_call(self):
        """Asian call <= European call (averaging reduces effective spot)."""
        from option_pricer import EuropeanOption
        asian = AsianOption(**ATM_PARAMS, option_type="call", averaging="geometric").price()
        euro = EuropeanOption(S=100, K=100, T=1.0, r=0.05, sigma=0.20).price()
        assert asian < euro

    def test_price_with_stderr_zero_stderr(self):
        opt = AsianOption(**ATM_PARAMS, averaging="geometric")
        price, stderr = opt.price_with_stderr()
        assert stderr == 0.0
        assert price > 0

    def test_price_increases_with_spot(self):
        prices = [
            AsianOption(S=s, K=100, T=1.0, r=0.05, sigma=0.20, n_steps=50,
                        option_type="call", averaging="geometric").price()
            for s in [80, 100, 120]
        ]
        assert prices == sorted(prices)

    def test_atm_call_reference_value(self):
        """Geometric ATM call ≈ 5.54 (discrete monitoring, n=252)."""
        opt = AsianOption(**ATM_PARAMS, option_type="call", averaging="geometric")
        assert math.isclose(opt.price(), 5.54, abs_tol=0.10)


class TestAsianArithmeticMonteCarlo:
    """Arithmetic Asian options require Monte Carlo; results have variance."""

    def test_call_price_positive(self):
        opt = AsianOption(**ATM_PARAMS, option_type="call", averaging="arithmetic",
                          n_simulations=20_000, seed=0)
        assert opt.price() > 0

    def test_put_price_positive(self):
        opt = AsianOption(**ATM_PARAMS, option_type="put", averaging="arithmetic",
                          n_simulations=20_000, seed=0)
        assert opt.price() > 0

    def test_arithmetic_call_less_than_european_call(self):
        from option_pricer import EuropeanOption
        asian = AsianOption(**ATM_PARAMS, option_type="call", averaging="arithmetic",
                            n_simulations=50_000, seed=42).price()
        euro = EuropeanOption(S=100, K=100, T=1.0, r=0.05, sigma=0.20).price()
        assert asian < euro

    def test_price_with_stderr_returns_tuple(self):
        opt = AsianOption(**ATM_PARAMS, averaging="arithmetic",
                          n_simulations=10_000, seed=1)
        price, stderr = opt.price_with_stderr()
        assert price > 0
        assert stderr > 0

    def test_reproducibility_with_seed(self):
        kwargs = dict(**ATM_PARAMS, option_type="call", averaging="arithmetic",
                      n_simulations=10_000, seed=7)
        p1 = AsianOption(**kwargs).price()
        p2 = AsianOption(**kwargs).price()
        assert p1 == p2

    def test_atm_arithmetic_call_plausible(self):
        """Arithmetic ATM call should be close to geometric (within ~0.50)."""
        geo = AsianOption(**ATM_PARAMS, averaging="geometric").price()
        arith = AsianOption(**ATM_PARAMS, averaging="arithmetic",
                            n_simulations=100_000, seed=0).price()
        assert abs(arith - geo) < 0.50


class TestAsianValidation:
    def test_negative_spot_raises(self):
        with pytest.raises(ValueError):
            AsianOption(S=-1, K=100, T=1, r=0.05, sigma=0.20)

    def test_invalid_averaging_raises(self):
        with pytest.raises(ValueError):
            AsianOption(S=100, K=100, T=1, r=0.05, sigma=0.20, averaging="median")

    def test_invalid_option_type_raises(self):
        with pytest.raises(ValueError):
            AsianOption(S=100, K=100, T=1, r=0.05, sigma=0.20, option_type="swap")

    def test_zero_steps_raises(self):
        with pytest.raises(ValueError):
            AsianOption(S=100, K=100, T=1, r=0.05, sigma=0.20, n_steps=0)
