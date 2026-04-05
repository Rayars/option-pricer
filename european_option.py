import numpy as np
from scipy.stats import norm

def BS(S, K, r, T, q, sigma, option_type='call'):
    d1 = np.log(S/K)+(r-q+0.5*sigma**2)*T/(sigma*np.sqrt(T))
    d2 = d1 - sigma*np.sqrt(T)

    if option_type == 'call':
        price = S*np.exp(-q*T)*norm.cdf(d1)-K*np.exp(-r*T)*norm.cdf(d2)
    elif option_type == 'put':
        price = K*np.exp(-r*T)*norm.cdf(-d2)-S*np.exp(-q*T)*norm.cdf(-d1)

    return price

def Vega(S, K, r, T, q, sigma):
    d1 = np.log(S/K)+(r-q+0.5*sigma**2)*T/(sigma*np.sqrt(T))
    vega = S*np.exp(-q*T)*np.sqrt(T)*norm.pdf(d1)
    return vega