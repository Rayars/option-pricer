# option-pricer

A Python library for pricing financial options. Supports **European**, **Asian**, and **American** option styles.

## Installation

```bash
pip install -r requirements.txt
```

## Quick start

```python
from option_pricer import EuropeanOption, AsianOption, AmericanOption

# --- European option (Black-Scholes) ---
euro = EuropeanOption(S=100, K=100, T=1.0, r=0.05, sigma=0.20, option_type="call")
print(f"European call price : {euro.price():.4f}")   # ≈ 10.4506
print(f"Greeks              : {euro.greeks()}")

# --- Asian option ---
# Arithmetic average (Monte Carlo)
asian_arith = AsianOption(
    S=100, K=100, T=1.0, r=0.05, sigma=0.20,
    averaging="arithmetic", n_simulations=100_000, seed=42
)
print(f"Asian arith call    : {asian_arith.price():.4f}")

# Geometric average (closed-form)
asian_geo = AsianOption(
    S=100, K=100, T=1.0, r=0.05, sigma=0.20,
    averaging="geometric"
)
print(f"Asian geo call      : {asian_geo.price():.4f}")

# --- American option (CRR binomial tree) ---
amer = AmericanOption(S=100, K=100, T=1.0, r=0.05, sigma=0.20, option_type="put")
print(f"American put price  : {amer.price():.4f}")
```

## Implemented models

### European options — `EuropeanOption`

Uses the **Black-Scholes** closed-form solution.

| Parameter | Description |
|-----------|-------------|
| `S` | Current asset price |
| `K` | Strike price |
| `T` | Time to expiration (years) |
| `r` | Risk-free rate (continuously compounded) |
| `sigma` | Annualised volatility |
| `q` | Continuous dividend yield (default `0`) |
| `option_type` | `"call"` or `"put"` (default `"call"`) |

Methods: `price()`, `delta()`, `gamma()`, `vega()`, `theta()`, `rho()`, `greeks()`

### Asian options — `AsianOption`

Average-price (average-rate) options.

| Parameter | Description |
|-----------|-------------|
| `S`, `K`, `T`, `r`, `sigma`, `q` | Same as above |
| `n_steps` | Number of averaging dates (default `252`) |
| `option_type` | `"call"` or `"put"` |
| `averaging` | `"arithmetic"` (Monte Carlo) or `"geometric"` (closed-form) |
| `n_simulations` | Monte Carlo paths (default `100_000`) |
| `seed` | Random seed for reproducibility |

Methods: `price()`, `price_with_stderr()`

### American options — `AmericanOption`

Uses the **Cox-Ross-Rubinstein (CRR) binomial tree** with early-exercise
checking at every node.

| Parameter | Description |
|-----------|-------------|
| `S`, `K`, `T`, `r`, `sigma`, `q` | Same as above |
| `n_steps` | Binomial tree steps (default `500`) |
| `option_type` | `"call"` or `"put"` |

Methods: `price()`

## Running tests

```bash
python -m pytest tests/ -v
```
