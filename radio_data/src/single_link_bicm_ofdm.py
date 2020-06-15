import logging
import numpy as np

import itpp

from . import codec, modem, ofdm


'''Simulate block transmission and reception over a single link and given channel coefficients and configuration parameters.
   The transmission steps are:
   1. Generate random info bits
   2. Encode info bits
   3. Interleave encoded bits
'''
def simulate(transport_block_size, 
             modorder,
             nrof_subcarriers,
             snr_db, 
             channel_coeff_freq_domain_np):

    #channel_coeff_freq_domain_str = ';'.join([' '.join([str(c).replace('j','i').replace('(','').replace(')','') for c in r]) for r in channel_coeff_freq_domain_np])
    #channel_coeff_freq_domain = itpp.cmat(channel_coeff_freq_domain_str)
    
    channel_coeff_freq_domain = itpp.numpy_array_to_mat( channel_coeff_freq_domain_np )

    nrof_subframe_ofdm_symbols = 12
    
    #--------- TRANSMITTER PROCESSING ----------
    
    # Generate random transmit bits for subframe
    nrof_frames = channel_coeff_freq_domain.cols()
    info_bits_uncoded = itpp.random.randb(transport_block_size * nrof_frames) # bmat[block_size, nrof_samples]
    
    # Channel encode the transmit data bits
    info_bits_encoded = codec.encode( transport_block_size, info_bits_uncoded )

    encoded_block_size = int(info_bits_encoded.length() / nrof_frames)
    
    interleaver_bin = itpp.comm.sequence_interleaver_bin(encoded_block_size)
    interleaver_bin.randomize_interleaver_sequence()
    
    interleaver_double = itpp.comm.sequence_interleaver_double(encoded_block_size)
    interleaver_double.set_interleaver_sequence(interleaver_bin.get_interleaver_sequence())
    
    info_bits_interleaved = interleaver_bin.interleave(info_bits_encoded)
    
    # Rate match the encoded bits
    transmit_block_size = int(nrof_subcarriers * nrof_subframe_ofdm_symbols * modorder)
    info_bits_rate_matched = codec.rate_match(transmit_block_size, encoded_block_size)(info_bits_interleaved)
    
    # Modulate the rate matched bits
    info_symbols_modulated = modem.modulate_bits( modorder, info_bits_rate_matched )
    
    # Obtain the OFDM frequency-domain signal
    transmit_signal_freq_domain = ofdm.multiplex_symbols(nrof_subframe_ofdm_symbols,
                                                         nrof_subcarriers,
                                                         info_symbols_modulated)

    #--------- CHANNEL EFFECTS ----------
    # Apply the channel to the transmitted signal
    received_signal_freq_domain = itpp.elem_mult_mat(transmit_signal_freq_domain, channel_coeff_freq_domain)
       
    # Add receiver noise
    noise_std_dev = itpp.math.sqrt(1.0 / pow(10, 0.1 * snr_db)) # Signal and channel power is normalized to 1 
    received_signal_freq_domain_noisy = received_signal_freq_domain + noise_std_dev * itpp.randn_c(received_signal_freq_domain.rows(), received_signal_freq_domain.cols())
    
    #--------- RECEIVER PROCESSING ----------
    
    # Remove the effect of channel
    received_signal_freq_domain_compensated = itpp.elem_div_mat(received_signal_freq_domain_noisy, channel_coeff_freq_domain) 
        
    # Obtain the time-domain symbols
    received_symbols_modulated = ofdm.de_multiplex_symbols(nrof_subframe_ofdm_symbols,
                                                           nrof_subcarriers,
                                                           received_signal_freq_domain_compensated)

    # Demodulate the received symbols according to the modulation order
    received_soft_values = modem.demodulate_soft_values(modorder, 
                                                        noise_std_dev * noise_std_dev, 
                                                        received_symbols_modulated)

    # De-rate match the received soft values
    received_soft_values_de_rate_matched = codec.de_rate_match(transmit_block_size, encoded_block_size)(received_soft_values)
    
    received_soft_values_deinterleaved = interleaver_double.deinterleave(received_soft_values_de_rate_matched, 0)
    
    # Channel decode the data bits according to the code rate
    received_bits_decoded = codec.decode( transport_block_size, received_soft_values_deinterleaved )

    # Count block errors
    bler, block_success = error_counter(info_bits_uncoded, received_bits_decoded, transport_block_size)

#     print 'bler', bler
    logging.info('SNR:%0.2f dB, BLER: %0.4f' %(snr_db, bler))
    
#     channel_to_noise_ratio = channel_coeff_freq_domain.elem_div(noise_realization)
    
    return (bler, block_success)

def error_counter(blocks_in, blocks_out, blocksize):
    nrof_blocks = int(blocks_in.length() / blocksize)
    block_success = itpp.zeros_b(nrof_blocks)
    nrof_errors = 0
    
    for block_index in range(nrof_blocks):
        if (blocks_in.mid(block_index * blocksize, blocksize) != blocks_out.mid(block_index * blocksize, blocksize)):
            block_success[block_index] = itpp.bin(0)
            nrof_errors += 1
        else:
            block_success[block_index] = itpp.bin(1)

            
    block_error_ratio = float(nrof_errors) / float(nrof_blocks)
    
    block_success_np = np.array( block_success )
    
    return (block_error_ratio, block_success_np)
