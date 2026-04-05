import numpy as np
from scipy.stats import norm

def geo_CF_asian_option(S, K, r, T, n, sigma, option_type = 'call'):
    sigmahat = sigma * np.sqrt((n + 1) * (2 * n + 1) / (6 * n**2))
    miuhat = (r - 0.5 * sigma**2) * ((n + 1) / (2 * n)) + 0.5 * sigmahat**2
    d1hat = (np.log(S / K) + (miuhat + 0.5 * sigmahat**2) * T) / (sigmahat * np.sqrt(T))
    d2hat = d1hat - sigmahat * np.sqrt(T)

    if option_type == 'call':
        return np.exp(-r * T) * (S * np.exp(miuhat * T) * norm.cdf(d1hat) - K * norm.cdf(d2hat))
    elif option_type == 'put':
        return np.exp(-r * T) * (K * norm.cdf(-d2hat) - S * np.exp(miuhat * T) * norm.cdf(-d1hat))
    else:
        raise ValueError("option_type must be 'call' or 'put'")
    
