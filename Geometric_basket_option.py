import numpy as np
from scipy.stats import norm


def geo_CF_basket_option(S1, S2, K, r, T, sigma1, sigma2, rho, option_type="call"):
    bg0 = np.sqrt(S1 * S2)
    sigma_bg_sq = (sigma1**2 + 2.0 * rho * sigma1 * sigma2 + sigma2**2) / 4.0
    sigma_bg = np.sqrt(sigma_bg_sq)
    mu_bg = r - 0.25 * (sigma1**2 + sigma2**2) + 0.5 * sigma_bg_sq

    d1hat = (np.log(bg0 / K) + (mu_bg + 0.5 * sigma_bg_sq) * T) / (sigma_bg * np.sqrt(T))
    d2hat = d1hat - sigma_bg * np.sqrt(T)

    if option_type == "call":
        return np.exp(-r * T) * (bg0 * np.exp(mu_bg * T) * norm.cdf(d1hat) - K * norm.cdf(d2hat))
    if option_type == "put":
        return np.exp(-r * T) * (K * norm.cdf(-d2hat) - bg0 * np.exp(mu_bg * T) * norm.cdf(-d1hat))
    raise ValueError("option_type must be 'call' or 'put'")
