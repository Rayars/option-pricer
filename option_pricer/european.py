"""European option pricing using the Black-Scholes model."""

import math
from dataclasses import dataclass, field
from scipy.stats import norm


@dataclass
class EuropeanOption:
    """Price a European call or put option using the Black-Scholes formula.

    Parameters
    ----------
    S : float
        Current underlying asset price.
    K : float
        Strike price.
    T : float
        Time to expiration in years.
    r : float
        Continuously compounded risk-free rate (e.g. 0.05 for 5 %).
    sigma : float
        Annualised volatility of the underlying (e.g. 0.20 for 20 %).
    q : float, optional
        Continuous dividend yield (default 0).
    option_type : str
        ``"call"`` or ``"put"`` (case-insensitive, default ``"call"``).
    """

    S: float
    K: float
    T: float
    r: float
    sigma: float
    q: float = 0.0
    option_type: str = "call"

    def __post_init__(self) -> None:
        if self.S <= 0:
            raise ValueError("S (asset price) must be positive.")
        if self.K <= 0:
            raise ValueError("K (strike price) must be positive.")
        if self.T <= 0:
            raise ValueError("T (time to expiration) must be positive.")
        if self.sigma <= 0:
            raise ValueError("sigma (volatility) must be positive.")
        self.option_type = self.option_type.lower()
        if self.option_type not in ("call", "put"):
            raise ValueError("option_type must be 'call' or 'put'.")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @property
    def _d1(self) -> float:
        return (
            math.log(self.S / self.K) + (self.r - self.q + 0.5 * self.sigma ** 2) * self.T
        ) / (self.sigma * math.sqrt(self.T))

    @property
    def _d2(self) -> float:
        return self._d1 - self.sigma * math.sqrt(self.T)

    # ------------------------------------------------------------------
    # Price
    # ------------------------------------------------------------------

    def price(self) -> float:
        """Return the Black-Scholes option price."""
        d1, d2 = self._d1, self._d2
        discount = math.exp(-self.r * self.T)
        forward_factor = math.exp(-self.q * self.T)
        if self.option_type == "call":
            return (
                self.S * forward_factor * norm.cdf(d1)
                - self.K * discount * norm.cdf(d2)
            )
        # put
        return (
            self.K * discount * norm.cdf(-d2)
            - self.S * forward_factor * norm.cdf(-d1)
        )

    # ------------------------------------------------------------------
    # Greeks
    # ------------------------------------------------------------------

    def delta(self) -> float:
        """First derivative of option price with respect to S."""
        fwd = math.exp(-self.q * self.T)
        if self.option_type == "call":
            return fwd * norm.cdf(self._d1)
        return fwd * (norm.cdf(self._d1) - 1)

    def gamma(self) -> float:
        """Second derivative of option price with respect to S."""
        fwd = math.exp(-self.q * self.T)
        return fwd * norm.pdf(self._d1) / (self.S * self.sigma * math.sqrt(self.T))

    def vega(self) -> float:
        """Derivative of option price with respect to sigma (per 1 % move)."""
        fwd = math.exp(-self.q * self.T)
        return self.S * fwd * norm.pdf(self._d1) * math.sqrt(self.T) / 100

    def theta(self) -> float:
        """Derivative of option price with respect to T (per calendar day)."""
        d1, d2 = self._d1, self._d2
        fwd = math.exp(-self.q * self.T)
        discount = math.exp(-self.r * self.T)
        common = (
            -self.S * fwd * norm.pdf(d1) * self.sigma / (2 * math.sqrt(self.T))
        )
        if self.option_type == "call":
            return (
                common
                - self.r * self.K * discount * norm.cdf(d2)
                + self.q * self.S * fwd * norm.cdf(d1)
            ) / 365
        return (
            common
            + self.r * self.K * discount * norm.cdf(-d2)
            - self.q * self.S * fwd * norm.cdf(-d1)
        ) / 365

    def rho(self) -> float:
        """Derivative of option price with respect to r (per 1 % move)."""
        discount = math.exp(-self.r * self.T)
        if self.option_type == "call":
            return self.K * self.T * discount * norm.cdf(self._d2) / 100
        return -self.K * self.T * discount * norm.cdf(-self._d2) / 100

    def greeks(self) -> dict:
        """Return all Greeks as a dictionary."""
        return {
            "delta": self.delta(),
            "gamma": self.gamma(),
            "vega": self.vega(),
            "theta": self.theta(),
            "rho": self.rho(),
        }
