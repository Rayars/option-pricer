import numpy as np
from scipy.stats import norm
from european_option import BS, Vega

def implied_volatility_newton(S, K, r, T, q, V, option_type='call'):
    sigma_hat = np.sqrt(2*abs(np.log(S/K)+(r-q)*T)/T)  
    tol = 1e-8
    max_iter = 1000
    sigma_diff = float('inf')
    iter = 0
    sigma = sigma_hat
    while (sigma_diff > tol) and (iter < max_iter):
        C = BS(S, K, r, T, q, sigma, option_type)
        C_Vega = Vega(S, K, r, T, q, sigma)
        sigma_diff = (C-V)/C_Vega
        C_true = sigma - sigma_diff
        sigma = C_true
        iter += 1
    return sigma
