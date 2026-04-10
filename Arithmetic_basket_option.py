import numpy as np

from Geometric_basket_option import geo_CF_basket_option

M = int(1e5)


def Arith_MC_basket_option(
    S1,
    S2,
    K,
    r,
    T,
    sigma1,
    sigma2,
    rho,
    option_type="call",
    m_paths=M,
    seed=1000,
):
    rng = np.random.default_rng(seed)
    z = rng.standard_normal((m_paths, 2))
    z[:, 1] = rho * z[:, 0] + np.sqrt(1.0 - rho**2) * z[:, 1]

    s1_terminal = S1 * np.exp((r - 0.5 * sigma1**2) * T + sigma1 * np.sqrt(T) * z[:, 0])
    s2_terminal = S2 * np.exp((r - 0.5 * sigma2**2) * T + sigma2 * np.sqrt(T) * z[:, 1])

    arith_mean = 0.5 * (s1_terminal + s2_terminal)
    geo_mean = np.sqrt(s1_terminal * s2_terminal)
    discount = np.exp(-r * T)

    if option_type == "call":
        arith_payoff = discount * np.maximum(arith_mean - K, 0.0)
        geo_payoff = discount * np.maximum(geo_mean - K, 0.0)
    elif option_type == "put":
        arith_payoff = discount * np.maximum(K - arith_mean, 0.0)
        geo_payoff = discount * np.maximum(K - geo_mean, 0.0)
    else:
        raise ValueError("option_type must be 'call' or 'put'")

    p_mean = float(np.mean(arith_payoff))
    p_std = float(np.std(arith_payoff, ddof=1)) if m_paths > 1 else 0.0
    conf_mc = (p_mean - 1.96 * p_std / np.sqrt(m_paths), p_mean + 1.96 * p_std / np.sqrt(m_paths))

    cov_xy = float(np.cov(arith_payoff, geo_payoff, ddof=1)[0, 1]) if m_paths > 1 else 0.0
    geo_var = float(np.var(geo_payoff, ddof=1)) if m_paths > 1 else 0.0
    theta = cov_xy / geo_var if geo_var > 0 else 0.0

    geo_c = float(geo_CF_basket_option(S1, S2, K, r, T, sigma1, sigma2, rho, option_type))
    z_payoff = arith_payoff + theta * (geo_c - geo_payoff)
    z_mean = float(np.mean(z_payoff))
    z_std = float(np.std(z_payoff, ddof=1)) if m_paths > 1 else 0.0
    conf_cv = (z_mean - 1.96 * z_std / np.sqrt(m_paths), z_mean + 1.96 * z_std / np.sqrt(m_paths))

    return p_mean, z_mean, conf_mc, conf_cv
