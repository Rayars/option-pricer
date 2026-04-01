"""Asian option pricing via Monte Carlo simulation and geometric closed-form."""

import math
from dataclasses import dataclass
import numpy as np
from scipy.stats import norm


@dataclass
class AsianOption:
    """Price an Asian (average-price) option.

    Two averaging methods are supported:

    * **arithmetic** – the payoff uses the arithmetic average of simulated
      asset prices along each path.  Priced via Monte Carlo simulation.
    * **geometric** – the payoff uses the geometric average.  An exact
      closed-form solution exists and is used by default when
      ``averaging="geometric"``.

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
    n_steps : int
        Number of averaging observation dates along the path (default 252).
    q : float, optional
        Continuous dividend yield (default 0).
    option_type : str
        ``"call"`` or ``"put"`` (case-insensitive, default ``"call"``).
    averaging : str
        ``"arithmetic"`` or ``"geometric"`` (case-insensitive,
        default ``"arithmetic"``).
    n_simulations : int
        Number of Monte Carlo paths (default 100 000).
    seed : int or None
        Random seed for reproducibility (default ``None``).
    """

    S: float
    K: float
    T: float
    r: float
    sigma: float
    n_steps: int = 252
    q: float = 0.0
    option_type: str = "call"
    averaging: str = "arithmetic"
    n_simulations: int = 100_000
    seed: int | None = None

    def __post_init__(self) -> None:
        if self.S <= 0:
            raise ValueError("S (asset price) must be positive.")
        if self.K <= 0:
            raise ValueError("K (strike price) must be positive.")
        if self.T <= 0:
            raise ValueError("T (time to expiration) must be positive.")
        if self.sigma <= 0:
            raise ValueError("sigma (volatility) must be positive.")
        if self.n_steps < 1:
            raise ValueError("n_steps must be at least 1.")
        if self.n_simulations < 1:
            raise ValueError("n_simulations must be at least 1.")
        self.option_type = self.option_type.lower()
        if self.option_type not in ("call", "put"):
            raise ValueError("option_type must be 'call' or 'put'.")
        self.averaging = self.averaging.lower()
        if self.averaging not in ("arithmetic", "geometric"):
            raise ValueError("averaging must be 'arithmetic' or 'geometric'.")

    # ------------------------------------------------------------------
    # Geometric closed-form (Kemna & Vorst, 1990)
    # ------------------------------------------------------------------

    def _geometric_closed_form(self) -> float:
        """Exact price for the continuously-monitored geometric Asian option."""
        n = self.n_steps
        T = self.T

        # Adjusted parameters for the geometric average
        sigma_adj = self.sigma * math.sqrt((2 * n + 1) / (6 * (n + 1)))
        r_adj = 0.5 * (
            self.r - self.q - 0.5 * self.sigma ** 2
        ) + 0.5 * sigma_adj ** 2

        d1 = (math.log(self.S / self.K) + (r_adj + 0.5 * sigma_adj ** 2) * T) / (
            sigma_adj * math.sqrt(T)
        )
        d2 = d1 - sigma_adj * math.sqrt(T)

        discount = math.exp(-self.r * T)
        if self.option_type == "call":
            return discount * (
                self.S * math.exp(r_adj * T) * norm.cdf(d1)
                - self.K * norm.cdf(d2)
            )
        return discount * (
            self.K * norm.cdf(-d2)
            - self.S * math.exp(r_adj * T) * norm.cdf(-d1)
        )

    # ------------------------------------------------------------------
    # Monte Carlo (arithmetic or geometric)
    # ------------------------------------------------------------------

    def _monte_carlo(self) -> tuple[float, float]:
        """Return (price, standard_error) via Monte Carlo simulation."""
        rng = np.random.default_rng(self.seed)

        dt = self.T / self.n_steps
        drift = (self.r - self.q - 0.5 * self.sigma ** 2) * dt
        vol_sqrt_dt = self.sigma * math.sqrt(dt)

        # Shape: (n_simulations, n_steps)
        Z = rng.standard_normal((self.n_simulations, self.n_steps))
        log_returns = drift + vol_sqrt_dt * Z
        # Cumulative log-price paths (starting at log(S))
        log_prices = math.log(self.S) + np.cumsum(log_returns, axis=1)
        prices = np.exp(log_prices)  # (n_simulations, n_steps)

        if self.averaging == "arithmetic":
            avg = prices.mean(axis=1)
        else:
            avg = np.exp(np.log(prices).mean(axis=1))

        discount = math.exp(-self.r * self.T)
        if self.option_type == "call":
            payoffs = np.maximum(avg - self.K, 0.0)
        else:
            payoffs = np.maximum(self.K - avg, 0.0)

        discounted = discount * payoffs
        price = discounted.mean()
        stderr = discounted.std(ddof=1) / math.sqrt(self.n_simulations)
        return float(price), float(stderr)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def price(self) -> float:
        """Return the option price.

        Uses the closed-form solution for geometric averaging, and Monte Carlo
        simulation for arithmetic averaging.
        """
        if self.averaging == "geometric":
            return self._geometric_closed_form()
        price, _ = self._monte_carlo()
        return price

    def price_with_stderr(self) -> tuple[float, float]:
        """Return ``(price, standard_error)`` from the Monte Carlo estimator.

        For geometric averaging this returns ``(closed_form_price, 0.0)``.
        """
        if self.averaging == "geometric":
            return self._geometric_closed_form(), 0.0
        return self._monte_carlo()
