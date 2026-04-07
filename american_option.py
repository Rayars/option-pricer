import numpy as np
from european_option import BS

def american_option(S, K, r, T, n, sigma, option_type = "call"):
    if option_type == "call":
        return BS(S, K, r, T, 0.0, sigma, option_type)
    elif option_type == "put":
        return american_put(S, K, r, T, n, sigma, option_type = "put")
    raise ValueError("option_type must be 'call' or 'put'")

def american_put(S, K, r, T, n, sigma, option_type = "put"):
    deltat = T/n
    DF = np.exp(-r*deltat)
    u = np.exp(sigma * np.sqrt(deltat))
    d = 1/u
    p = (np.exp(r*deltat) - d)/(u-d)

    if not (0.0 < p < 1.0):
        raise ValueError("invalid tree parameters: choose a larger n or check inputs")

    high_value = S * u ** n
    stock_values = high_value * (d / u) ** np.arange(n + 1)
    option_values = np.maximum(K - stock_values, 0.0)

    # Standard CRR backward induction for an American put.
    for step in range(n - 1, -1, -1):
        stock_values = stock_values[: step + 1] / u
        continuation_values = DF * (
            p * option_values[: step + 1] + (1.0 - p) * option_values[1 : step + 2]
        )
        exercise_values = np.maximum(K - stock_values, 0.0)
        option_values = np.maximum(continuation_values, exercise_values)

    return float(option_values[0])


    
