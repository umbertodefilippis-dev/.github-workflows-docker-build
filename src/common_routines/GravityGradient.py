import numpy as np
import spiceypy as spice

def GravityGradient(R0,R1,R2,GM,state):
    MSAD_SRF = np.array([
    [-1.33161E-03, -9.99988E-01, -1.33567E-04],
    [-4.70998E-04, -8.37999E-05, 9.99979E-01],
    [-1.00001, 1.76662E-03, 6.41689E-03]
    ])

    MSAD_SRF = np.eye(3)
 

    # Reshape the matrix to be of shape (3, N)
    
    state = -state
    denominator = np.linalg.norm(state) ** 3
    GG = GM / denominator * (3 * np.outer(state, state) / denominator**(1/1.5) - np.eye(3))
    a_GG0 = np.dot(GG, R0) * 1000
    a_GG1 = np.dot(GG, R1) * 1000
    a_GG2 = np.dot(GG, R2) * 1000
    a_GG0_sim = -np.dot(a_GG0, MSAD_SRF[:, 0])
    a_GG1_sim = -np.dot(a_GG1, MSAD_SRF[:, 1])
    a_GG2_sim = -np.dot(a_GG2, MSAD_SRF[:, 2])    
    a_GG = np.squeeze(np.vstack((a_GG0_sim, a_GG1_sim, a_GG2_sim)))
    return a_GG
