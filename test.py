import numpy as np
from math import ceil



def getWindow(dec:np.ndarray, to:np.ndarray, matrix:np.ndarray):
    sx, ex = min(dec[0], to[0]), min(dec[1], to[1])
    sy, ey = max(dec[0], to[0])+1, max(dec[1], to[1])+1
    return matrix[max(sx, 0):max(sy, 0), max(ex, 0):max(ey, 0)]


matrix = np.zeros((10, 10), dtype=int)

n = 0
for i in range(matrix.shape[0]):
    for j in range(matrix.shape[1]):
        matrix[i][j] = n
        n += 1

print(matrix)
print('-'*50)
print(getWindow(np.array([0, 0]), np.array([3, 3]), matrix))
print(getWindow(np.array([1, 1]), np.array([3, 3]), matrix))