from itpp import cvec, ivec
from itpp.comm import QAM, modulator_2d, Soft_Method

'''Create and return 2D modulator instance'''    
def modulate_bits(modulation_order, bits):
    symbols, bits2symbols = _constellation(modulation_order)
    modulator_ = modulator_2d(symbols, bits2symbols)
    
    return modulator_.modulate_bits(bits)

'''Create and return 2D demodulator instance'''    
def demodulate_soft_values(modulation_order, noise_variance, soft_values):
    symbols, bits2symbols = _constellation(modulation_order)
    modulator_ = modulator_2d(symbols, bits2symbols)
    
    return modulator_.demodulate_soft_bits(soft_values, noise_variance, Soft_Method.LOGMAP)

'''2D constellations for complex signals'''
def _constellation(modulation_order):
    symbols = QAM(2 ** modulation_order).get_symbols()
    bits2symbols = QAM(2 ** modulation_order).get_bits2symbols()

    return (symbols, bits2symbols)