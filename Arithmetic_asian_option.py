import numpy as np
from Geometric_asian_option import geo_CF_asian_option

M = int(1e4)

def Arith_MC_asian_option(S, K, r, T, n, sigma, option_type='call', m_paths=M):
    dt = T / n
    drift = (r - 0.5 * sigma**2) * dt
    diffusion = sigma * np.sqrt(dt)

    z = np.random.standard_normal((m_paths, n))
    log_paths = np.cumsum(drift + diffusion * z, axis=1)
    spots = S * np.exp(log_paths)

    arith_mean = np.mean(spots, axis=1)
    geo_mean = np.exp(np.mean(np.log(spots), axis=1))

    discount = np.exp(-r * T)
    if option_type == 'call':
        arith_payoff = discount * np.maximum(arith_mean - K, 0.0)
        geo_payoff = discount * np.maximum(geo_mean - K, 0.0)
    elif option_type == 'put':
        arith_payoff = discount * np.maximum(K - arith_mean, 0.0)
        geo_payoff = discount * np.maximum(K - geo_mean, 0.0)
    else:
        raise ValueError("option_type must be 'call' or 'put'")

    p_mean = float(np.mean(arith_payoff))
    p_std = float(np.std(arith_payoff, ddof=1)) if m_paths > 1 else 0.0
    conf_mc = (p_mean - 1.96 * p_std / np.sqrt(m_paths), p_mean + 1.96 * p_std / np.sqrt(m_paths))

    # non-biased estimate
    cov_xy = float(np.cov(arith_payoff, geo_payoff, ddof=1)[0, 1]) if m_paths > 1 else 0.0
    geo_var = float(np.var(geo_payoff, ddof=1)) if m_paths > 1 else 0.0
    theta = cov_xy / geo_var if geo_var > 0 else 0.0

    geo_c = float(geo_CF_asian_option(S, K, r, T, n, sigma, option_type))
    z_payoff = arith_payoff + theta * (geo_c - geo_payoff)
    z_mean = float(np.mean(z_payoff))
    z_std = float(np.std(z_payoff, ddof=1)) if m_paths > 1 else 0.0
    conf_cv = (z_mean - 1.96 * z_std / np.sqrt(m_paths), z_mean + 1.96 * z_std / np.sqrt(m_paths))

    return p_mean, z_mean, conf_mc, conf_cv
