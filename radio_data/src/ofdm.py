# COPYRIGHT_NOTICE

from itpp.signal import ifft, fft
from itpp import cmat
from itpp import cvec

def multiplex_symbols(nrof_ofdm_symbols_per_frame,
                      nrof_subcarriers,
                      constellation_symbols):
    
    nrof_frames = int(constellation_symbols.length() / (nrof_subcarriers * nrof_ofdm_symbols_per_frame))
    frame_symbols = cmat(nrof_subcarriers * nrof_ofdm_symbols_per_frame, nrof_frames)
    frame_symbols.clear()
    
    # Pre-allocate vector to store frame symbols for efficiency
    current_frame_symbols = cvec(nrof_subcarriers * nrof_ofdm_symbols_per_frame)
    for frame_index in range(nrof_frames):
        current_frame_symbols.clear()
        for ofdm_symbol_index in range(nrof_ofdm_symbols_per_frame):
            read_index = frame_index * nrof_subcarriers * nrof_ofdm_symbols_per_frame + ofdm_symbol_index * nrof_subcarriers
            current_frame_symbols.set_subvector(ofdm_symbol_index * nrof_subcarriers, (nrof_subcarriers ** 0.5) * ifft(constellation_symbols.mid(read_index, nrof_subcarriers)))
            
        frame_symbols.set_col(frame_index, current_frame_symbols)
        
    return frame_symbols
        
        
def de_multiplex_symbols(nrof_ofdm_symbols_per_frame,
                         nrof_subcarriers,
                         frame_symbols):
    
    nrof_frames = frame_symbols.cols()
    constellation_symbols = cvec(nrof_subcarriers * nrof_ofdm_symbols_per_frame * nrof_frames)
    constellation_symbols.clear()
    
    for frame_index in range(nrof_frames):
        for ofdm_symbol_index in range(nrof_ofdm_symbols_per_frame):
            write_index = frame_index * nrof_subcarriers * nrof_ofdm_symbols_per_frame + ofdm_symbol_index * nrof_subcarriers
            constellation_symbols.set_subvector(write_index, (1.0 / (nrof_subcarriers ** 0.5)) * fft(frame_symbols.get_col(frame_index).mid(ofdm_symbol_index * nrof_subcarriers, nrof_subcarriers)))
            
    return constellation_symbols
