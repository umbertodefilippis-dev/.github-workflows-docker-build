import numpy as np
import spiceypy as spice
import os

def data_reduction(meas_acc, matrix, matrixdot,MSAD_SRF,GM,state,tolGG,et0):

    #Get the geometry information (TO DO: Update SPICE kernel with HAA on-ground calibration info)
    """
    R1 = np.array((917.466, -102.805, 944.107))/1000      #Position of Acc1 CoM wrt the SRF origin
    R0 = np.array((833.377, -102.874, 944.156))/1000      #Position of Acc0 CoM wrt the SRF origin 
    R2 = np.array((1008.238, -126.173, 944.548))/1000     #Position of Acc2 CoM wrt the SRF origin 
    """
    [R0,lt] = spice.spkpos('JUICE_HAA_AM_X', et0, 'JUICE_SPACECRAFT', 'LT', 'JUICE_SPACECRAFT')
    [R1,lt] = spice.spkpos('JUICE_HAA_AM_Y', et0, 'JUICE_SPACECRAFT', 'LT', 'JUICE_SPACECRAFT')
    [R2,lt] = spice.spkpos('JUICE_HAA_AM_Z', et0, 'JUICE_SPACECRAFT', 'LT', 'JUICE_SPACECRAFT')
    
    R0 = R0*1000
    R1 = R1*1000
    R2 = R2*1000

    R10 = R1-R0                                           #Position of Acc0 CoM wrt the Acc1 CoM
    R12 = R1-R2                                           #Position of Acc2 CoM wrt the Acc1 CoM
    R11 = R1-R1 

    # Reshape the matrix to be of shape (3, N)
    
    OMEGA = matrix.reshape((3, -1))
    OMEGADOT = matrixdot.reshape((3, -1))
    ACC = meas_acc.reshape((3,-1))
    #----------------------------------------------------------------------
    # MEASURED ACCELERATION [m/s^2] from 3 sensing masses
    #----------------------------------------------------------------------
    
    Acc0 = ACC[0,:]
    Acc1 = ACC[1,:]
    Acc2 = ACC[2,:]
    
    # Example: Create a reduced acceleration array (modify based on your specific logic)

    appAcc10 = np.dot(np.linalg.inv(MSAD_SRF),np.cross(OMEGA.T,np.cross(OMEGA.T, R10.T)).T + np.cross(OMEGADOT.T, R10.T).T)
    appAcc12 = np.dot(np.linalg.inv(MSAD_SRF),np.cross(OMEGA.T,np.cross(OMEGA.T, R12.T)).T + np.cross(OMEGADOT.T, R12.T).T)
    a_GG = np.zeros([3,state.shape[1]])
    for i in range(state.shape[1]):
        denominator = np.linalg.norm(state[0:3, i]) ** 3
        if GM/denominator < tolGG:
            a_GG[:,i]=np.squeeze(np.zeros([3,1]))
        else:

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
            a_GG[:,i]=np.squeeze(np.vstack((a_GG0_sim, a_GG1_sim, a_GG2_sim)))
        

    Acc0_reduced = Acc0-appAcc10[0,:]+a_GG[0,:]
    Acc1_reduced = Acc1
    Acc2_reduced = Acc2-appAcc12[2,:]+a_GG[2,:]
    Acc_reduced=np.stack((np.array(Acc0_reduced), np.array(Acc1_reduced), np.array(Acc2_reduced)), axis=0)
    return Acc_reduced