import math

import numpy as np
from scipy.stats import norm, qmc


def _sobol_standard_normals(n_paths, n_steps, seed):
    sampler = qmc.Sobol(d=n_steps, scramble=True, seed=seed)
    if n_paths <= 0:
        raise ValueError("n_paths must be positive")

    power = int(math.ceil(math.log2(n_paths)))
    uniforms = sampler.random_base2(power)[:n_paths]

    eps = np.finfo(float).eps
    uniforms = np.clip(uniforms, eps, 1.0 - eps)
    return norm.ppf(uniforms)


def _kiko_path_payoffs(S, K, r, T, sigma, lower_barrier, upper_barrier, n_steps, rebate, normals):
    dt = T / n_steps
    log_paths = np.cumsum((r - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * normals, axis=1)
    paths = S * np.exp(log_paths)

    knocked_out = paths >= upper_barrier
    has_knock_out = np.any(knocked_out, axis=1)
    first_knock_out = np.argmax(knocked_out, axis=1)
    knock_out_times = (first_knock_out + 1) * dt

    payoffs = np.zeros(paths.shape[0], dtype=float)
    payoffs[has_knock_out] = rebate * np.exp(-r * knock_out_times[has_knock_out])

    survivors = ~has_knock_out
    if np.any(survivors):
        survivor_paths = paths[survivors]
        knocked_in = np.any(survivor_paths <= lower_barrier, axis=1)
        terminal_prices = survivor_paths[:, -1]
        payoffs[survivors] = np.where(
            knocked_in,
            np.exp(-r * T) * np.maximum(K - terminal_prices, 0.0),
            0.0,
        )

    return payoffs


def quasi_mc_kiko_put(
    S,
    K,
    r,
    T,
    sigma,
    lower_barrier,
    upper_barrier,
    n_steps,
    rebate,
    n_paths=8192,
    seed=1000,
    spot_shift=None,
):
    normals = _sobol_standard_normals(n_paths, n_steps, seed)

    base_payoffs = _kiko_path_payoffs(
        S,
        K,
        r,
        T,
        sigma,
        lower_barrier,
        upper_barrier,
        n_steps,
        rebate,
        normals,
    )
    price = float(np.mean(base_payoffs))

    if spot_shift is None:
        spot_shift = max(0.5, 0.01 * S)
    if spot_shift >= S:
        raise ValueError("spot_shift must be smaller than the spot price")

    up_payoffs = _kiko_path_payoffs(
        S + spot_shift,
        K,
        r,
        T,
        sigma,
        lower_barrier,
        upper_barrier,
        n_steps,
        rebate,
        normals,
    )
    down_payoffs = _kiko_path_payoffs(
        S - spot_shift,
        K,
        r,
        T,
        sigma,
        lower_barrier,
        upper_barrier,
        n_steps,
        rebate,
        normals,
    )
    delta = float((np.mean(up_payoffs) - np.mean(down_payoffs)) / (2.0 * spot_shift))

    return price, delta
