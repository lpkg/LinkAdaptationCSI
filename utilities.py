import numpy as np
import scipy
from scipy import special
import matplotlib.pyplot as plt

# Stack the channel snr-per-subcarrier vectors for the previous 'mem' frames
def stack_features( features, mem = 1 ):
    nrof_samples, input_dim = features.shape
    stacked_feature_size = int( input_dim * mem )
    
    stacked_features = np.ndarray( ( nrof_samples, stacked_feature_size ) )
    for i in range( nrof_samples ):
        if i < mem:
            stacked_features[ i, :  int( input_dim * ( i + 1 ) ) ] = np.ndarray.flatten( features[ : i + 1, : ] )
        else:
            stacked_features[ i, : ]   = np.ndarray.flatten( features[ i : i - mem : -1, : ] )
            
    return stacked_features
##################################################################################
    
# Scale the channel coefficients from dataset and add channel estimation noise if required.
def calculate_channel_coefficients_scaled_fixed_snr( channel_coeff, snrs_db, channel_estimation_noise ):
    
    # random seed
    np.random.seed( int(100*abs(channel_coeff[0][0] + channel_coeff[100][5])) )
    
    channel_coeff_scaled = np.ndarray( channel_coeff.shape, dtype=np.complex128 )

    signal_mag = np.sqrt( 10 ** ( 0.1 * snrs_db ) )
    channel_coeff_scaled[:, :] = channel_coeff[:, :] * signal_mag
        
    if channel_estimation_noise:
        noise_real = np.sqrt(0.5) * np.random.normal( size = channel_coeff_scaled.shape )
        noise_imag = np.sqrt(0.5) * np.random.normal( size = channel_coeff_scaled.shape )
        
        channel_coeff_scaled = channel_coeff_scaled + noise_real + 1j * noise_imag
        
    return channel_coeff_scaled
################################################################################

# Scale the channel coefficients from dataset and add channel estimation noise if required.
def calculate_channel_coefficients_scaled( channel_coeff, snrs_db, channel_estimation_noise ):
    
    
    nrof_samples, nrof_subcarriers, _ = channel_coeff.shape
    
    channel_coeff_scaled = np.ndarray( channel_coeff.shape, dtype=np.complex128 )
    for snr_index, snr_db in enumerate( snrs_db ):
        signal_mag = np.sqrt( 10 ** ( 0.1 * snr_db ) )
        channel_coeff_scaled[:, :, snr_index] = channel_coeff[:, :, snr_index] * signal_mag
        
    if channel_estimation_noise:
        noise_real = np.sqrt(0.5) * np.random.normal( size = channel_coeff_scaled.shape )
        noise_imag = np.sqrt(0.5) * np.random.normal( size = channel_coeff_scaled.shape )
        
        channel_coeff_scaled = channel_coeff_scaled + noise_real + 1j * noise_imag
        
    return channel_coeff_scaled
################################################################################

# Determine the MCS that maximizes the expected throughput
def determine_best_mcs( ack_probabilities, block_sizes, target_error_rate = 1.0 ):
    
    ack_prob = np.copy( ack_probabilities )
    nrof_samples, _, nrof_snrs = ack_prob.shape
        
    # Suppress the MCS values with a ack probility above the target error rate
    ack_prob[ ack_prob < ( 1.0 - target_error_rate ) ] = 0
    
    best_mcs = np.ndarray( ( nrof_samples, nrof_snrs ), dtype=np.int32 )
    for snr_index in range( nrof_snrs ):
        expected_tputs = np.multiply( ack_prob[:, :, snr_index], block_sizes )
        best_mcs[:, snr_index] = np.argmax( expected_tputs, axis=1 )

    return best_mcs
################################################################################

# Calculate the average realized throughput for the selected MCSs
def calculate_average_throughput( selected_mcs, realized_ack, block_sizes ):
    
    nrof_samples, nrof_snrs = selected_mcs.shape
    
    avg_tput_vs_snr = []
    for snr_index in range( nrof_snrs ):
        realized_tputs = np.multiply( realized_ack[:, :, snr_index], block_sizes )

        # Evaluate and store the achieved overall throughput
        total_tput = 0
        for i in range( nrof_samples ):
            mcs = selected_mcs[ i, snr_index ]
            total_tput = total_tput + realized_tputs[ i,  mcs ]
        
        avg_tput_vs_snr.append( ( total_tput /  nrof_samples ) / 1e-3 )  # 1 ms frame duration

    return np.array(avg_tput_vs_snr)
################################################################################

# Calculate the average realized error rate for the selected MCSs
def calculate_error_rate( selected_mcs, realized_ack ):
    nrof_samples, nrof_snrs = selected_mcs.shape
    
    error_rate_vs_snr = []
    for snr_index in range( nrof_snrs ):

        total_acks = 0
        for i in range( nrof_samples ):
            mcs = selected_mcs[ i, snr_index ]
            total_acks = total_acks + realized_ack[i, mcs, snr_index]
        
        error_rate_vs_snr.append( 1.0 - ( total_acks /  nrof_samples ) )  # 1 ms frame duration

    return np.array(error_rate_vs_snr)
################################################################################

# Shuffle data for training
def shuffle_data( features, target ):
    assert features.shape[ 0 ] == target.shape[ 0 ], 'shuffle_data(...): features and targets should have same number of samples.'
    
    shuffled_indices = np.random.permutation( features.shape[ 0 ] )

    return ( features[ shuffled_indices, ... ], target[ shuffled_indices, ... ] )


# This function implements the theoretical autocorrelation function, i.e. Bessel
def autocorrelation(m,f_d,T_s):
  
  bessel_function_zero_order_first_kind=scipy.special.j0(2*np.pi*f_d*m*T_s)
  return bessel_function_zero_order_first_kind
################################################################################

# This function generates an upper-triangular matrix; useful when computing the
# Wiener coefficients
def create_upper_matrix(values, size):
    
    upper = np.zeros((size, size))
    upper[np.triu_indices(size, 0)] = values
    return(upper)
################################################################################  

# This function generates a lower-triangular matrix; useful when computing the
# Wiener coefficients
def create_lower_matrix(values, size):
    
    lower = np.zeros((size, size))
    lower[np.tril_indices(size, 0)] = values
    return(lower)
################################################################################

# This function computes the Wiener coefficients scaled according to the snr
def Wiener_filter_coeff_scaled(autocorrelation_of_reference,crosscorrelation,delta,N,snr,noise,f_d,sampling_interval):
    
    b = autocorrelation_of_reference
    for i in range(1,len(autocorrelation_of_reference)):
        b = np.concatenate((b,autocorrelation_of_reference[:-i]))
        
    upper_half = create_upper_matrix(np.conj(b), len(autocorrelation_of_reference))
    lower_half = create_lower_matrix(np.flip(b,axis = 0), len(autocorrelation_of_reference))
    T = lower_half+upper_half

  
    for i in range(0, len(autocorrelation_of_reference)):
        
        if noise == True:
        
            T[i,i] = autocorrelation_of_reference[0]* ( 1 + snr) / snr
        
        else:
        
            T[i,i]=autocorrelation_of_reference[0]

    if noise == True and delta == 0:
        crosscorrelation[0] = crosscorrelation[0]*(( 1 + snr) / snr)

    v = np.transpose( crosscorrelation )
    a = np.conj(np.dot(np.linalg.inv(T),v))
  
    return a

################################################################################

# This function reshapes the data
def flatten_axis( data ):
    N, M, P = data.shape
    reshaped_data  = np.ndarray( [ N * P, M ],dtype = data.dtype )
    for p in range( P ):
        reshaped_data[ N * p : N * ( p + 1 ), :] = data[:, :, p] 
    return reshaped_data

def flatten_snr_axis( data ):
    N, M, P = data.shape
    reshaped_data  = np.ndarray( [ N * P, M ] )
    for p in range( P ):
        reshaped_data[ N * p : N * ( p + 1 ), :] = data[:, :, p] 
    return reshaped_data

