import numpy as np
from scipy.stats import norm

np.random.seed(1000)

def generate_paths(M, n):
    Z = np.random.uniform(low=-1, high=1, size=(M, n))
    return Z

if __name__ == "__main__":
    M = 10
    n = 10
    paths = generate_paths(M, n)
    print(paths.shape)