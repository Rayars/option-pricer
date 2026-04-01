"""American option pricing using the Cox-Ross-Rubinstein binomial tree."""

import math
from dataclasses import dataclass
import numpy as np


@dataclass
class AmericanOption:
    """Price an American call or put option using the CRR binomial tree.

    The tree allows early exercise at every node, making it suitable for
    American-style options.  The accuracy improves with the number of steps.

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
        Number of time steps in the binomial tree (default 500).
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
    n_steps: int = 500
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
        if self.n_steps < 1:
            raise ValueError("n_steps must be at least 1.")
        self.option_type = self.option_type.lower()
        if self.option_type not in ("call", "put"):
            raise ValueError("option_type must be 'call' or 'put'.")

    # ------------------------------------------------------------------
    # Price
    # ------------------------------------------------------------------

    def price(self) -> float:
        """Return the American option price via the CRR binomial tree."""
        n = self.n_steps
        dt = self.T / n

        # CRR parameters
        u = math.exp(self.sigma * math.sqrt(dt))
        d = 1.0 / u
        disc = math.exp(-self.r * dt)
        p = (math.exp((self.r - self.q) * dt) - d) / (u - d)
        q_prob = 1.0 - p

        # Terminal asset prices (vectorised)
        j = np.arange(n + 1)
        S_T = self.S * (u ** (n - j)) * (d ** j)

        # Terminal option values
        if self.option_type == "call":
            values = np.maximum(S_T - self.K, 0.0)
        else:
            values = np.maximum(self.K - S_T, 0.0)

        # Backward induction with early-exercise check
        for i in range(n - 1, -1, -1):
            S_now = self.S * (u ** (i - np.arange(i + 1))) * (d ** np.arange(i + 1))
            values = disc * (p * values[:-1] + q_prob * values[1:])
            if self.option_type == "call":
                intrinsic = np.maximum(S_now - self.K, 0.0)
            else:
                intrinsic = np.maximum(self.K - S_now, 0.0)
            values = np.maximum(values, intrinsic)

        return float(values[0])
