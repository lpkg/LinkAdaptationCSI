import logging

from itpp.comm import turbo_codec
from itpp import vec, ivec, bvec
from itpp import zeros, zeros_b
from itpp import imat

#from . import constants
    
def encode( block_length, bits ):
    '''Create the codec instance and set parameters'''
    codec = turbo_codec()
    
    '''Prepare codec parameters'''
    gen_sequence = '11,13'
    gen = ivec( gen_sequence )
    constraint_length = 4
    
    codec.set_parameters(gen, gen, constraint_length, ivec())
    codec.set_interleaver(_interleaver_sequence(block_length))
    
    '''Encode with the given code rate and bitarray comprising uncoded bits'''
    '''Generate and return encoded bits'''
    encoded_bits = bvec()
    codec.encode(bits, encoded_bits)
    return encoded_bits        

def decode( block_length, bits):
    '''Create the codec instance and set parameters'''
    codec = turbo_codec()
    
    '''Prepare codec parameters'''
    gen_sequence = '11,13'
    gen = ivec( gen_sequence )
    constraint_length = 4
    
    codec.set_parameters(gen, gen, constraint_length, ivec())
    codec.set_interleaver(_interleaver_sequence(block_length))
    
    '''Encode with the given code rate and bitarray comprising uncoded bits'''
    '''Generate and return decoded bits'''
    decoded_bits = bvec()
    codec.decode(bits, decoded_bits, bvec())
    return decoded_bits 

def rate_match(rate_matched_block_size, input_block_size):
    
    def _rate_match_by_truncation(input_bits):
        nrof_blocks = int(input_bits.length() / input_block_size)
        rate_matched_bits = zeros_b(nrof_blocks * rate_matched_block_size)
        
        for block_index in range(nrof_blocks):
            # Extract the current block bring rate matched
            rate_matched_block = input_bits.mid(block_index * input_block_size, rate_matched_block_size) 
            
            # Truncate the rightmost bits and insert into the rate matched bits
            rate_matched_bits.set_subvector(block_index * rate_matched_block_size, rate_matched_block)

        return rate_matched_bits
    
    def _rate_match_by_repetition(input_bits):
        nrof_blocks = int(input_bits.length() / input_block_size)
        rate_matched_bits = bvec(nrof_blocks * rate_matched_block_size)
        rate_matched_bits.clear()

        # Determine the number of full repetitions of each input block        
        nrof_repetitions = int(rate_matched_block_size / input_block_size)
        
        for block_index in range(nrof_blocks):
            # Extract the current block being rate matched
            current_input_block = input_bits.mid(block_index * input_block_size, input_block_size) 
            
            # Repeat the input bits and insert into the rate matched bits
            for repetition_index in range(nrof_repetitions):
                write_index = block_index * rate_matched_block_size + repetition_index * input_block_size
                rate_matched_bits.set_subvector(write_index, current_input_block)
            
            # Fill in the remaining bits (if any) with leftmost bits of the input block
            write_index = block_index * rate_matched_block_size + nrof_repetitions * input_block_size
            rate_matched_bits.set_subvector(write_index, current_input_block.left(rate_matched_block_size - nrof_repetitions * input_block_size))
            
        return rate_matched_bits

        
    if input_block_size >= rate_matched_block_size:
        return _rate_match_by_truncation
    else:
        return _rate_match_by_repetition
    
    
def de_rate_match(input_block_size, de_rate_matched_block_size):
    
    def _de_rate_match_by_zero_padding(input_values):
        nrof_blocks = int(input_values.length() / input_block_size)
        de_rate_matched_values = zeros(nrof_blocks * de_rate_matched_block_size)
        
        for block_index in range(nrof_blocks):
            # Extract the current block bring rate matched
            current_input_block = input_values.mid(block_index * input_block_size, input_block_size) 
            
            # Truncate the rightmost bits and insert into the rate matched bits
            de_rate_matched_values.set_subvector(block_index * de_rate_matched_block_size, current_input_block)

        return de_rate_matched_values
    
    def _de_rate_match_by_accumulation(input_values):
        nrof_blocks = int(input_values.length() / input_block_size)
        de_rate_matched_values = vec(nrof_blocks * de_rate_matched_block_size)
        de_rate_matched_values.clear()

        # Determine the number of full repetitions of each input block        
        nrof_repetitions = int(input_block_size / de_rate_matched_block_size)
        nrof_extra_values = input_block_size - nrof_repetitions * de_rate_matched_block_size
        
        # Pre-allocate vector to store accumulated values for efficiency
        current_de_rate_matched_block = vec(de_rate_matched_block_size)
        for block_index in range(nrof_blocks):
            current_de_rate_matched_block.clear()
            
            #First, accumulate the extra bits left over after complete block repeitions
            read_index = block_index * input_block_size + nrof_repetitions * de_rate_matched_block_size
            current_de_rate_matched_block.set_subvector(0, input_values.mid(read_index, nrof_extra_values))
            
            # Accumulate the input values into the de rate matched valuess
            for repetition_index in range(nrof_repetitions):
                read_index = block_index * input_block_size + repetition_index * de_rate_matched_block_size
                current_de_rate_matched_block += input_values.mid(read_index, de_rate_matched_block_size)            
            
            de_rate_matched_values.set_subvector(block_index * de_rate_matched_block_size, current_de_rate_matched_block)
        
        return de_rate_matched_values

        
    if input_block_size <= de_rate_matched_block_size:
        return _de_rate_match_by_zero_padding
    else:
        return _de_rate_match_by_accumulation

''' Interleaver specification
    3GPP TS 36.212 v12.2.0 Table 5.1.3-3
'''
def _interleaver_sequence( block_size ):

    K = block_size
    
    '''Get the index of parameters to be used from interleaver table
    '''
    index = 0
    if (40 <= K and K <= 512 and (K % 8 == 0)):
        index = (K - 40) / 8
    elif (528 <= K and K <= 1024 and (K % 16 == 0)):
        index = 60 + ((K - 528) / 16)
    elif (1056 <= K and K <= 2048 and (K % 32 == 0)):
        index = 92 + ((K - 1056) / 32)
    elif (2112 <= K and K <= 6144 and (K % 64 == 0)):
        index = 124 + ((K - 2112) / 64);
    else:
        error_str = 'Invalid interleaver size: ' + str(K) 
        logging.error(error_str) 
        #raise ValueError, error_str 
    
    '''Get the parameters to generate the interleaver sequence
    '''
    f1 = _TURBO_INTERNAL_INTERLEAVER_TABLE.get(int(index), 1);
    f2 = _TURBO_INTERNAL_INTERLEAVER_TABLE.get(int(index), 2);
    
    '''Mapping from output index 'i' to input index 'PI_i'
    '''
    PI_mapping = lambda i: (f1 * i + f2 * i * i) % K
    PI = ivec(K) # Placeholder for input indices
    for i in range(K):
        PI[i] = PI_mapping(i)
    
    return PI

_TURBO_INTERNAL_INTERLEAVER_TABLE = imat('40 3 10;'
                                         '48 7 12;'
                                         '56 19 42;'
                                         '64 7 16;'
                                         '72 7 18;'
                                         '80 11 20;'
                                         '88 5 22;'
                                         '96 11 24;'
                                         '104 7 26;'
                                         '112 41 84;'
                                         '120 103 90;'
                                         '128 15 32;'
                                         '136 9 34;'
                                         '144 17 108;'
                                         '152 9 38;'
                                         '160 21 120;'
                                         '168 101 84;'
                                         '176 21 44;'
                                         '184 57 46;'
                                         '192 23 48;'
                                         '200 13 50;'
                                         '208 27 52;'
                                         '216 11 36;'
                                         '224 27 56;'
                                         '232 85 58;'
                                         '240 29 60;'
                                         '248 33 62;'
                                         '256 15 32;'
                                         '264 17 198;'
                                         '272 33 68;'
                                         '280 103 210;'
                                         '288 19 36;'
                                         '296 19 74;'
                                         '304 37 76;'
                                         '312 19 78;'
                                         '320 21 120;'
                                         '328 21 82;'
                                         '336 115 84;'
                                         '344 193 86;'
                                         '352 21 44;'
                                         '360 133 90;'
                                         '368 81 46;'
                                         '376 45 94;'
                                         '384 23 48;'
                                         '392 243 98;'
                                         '400 151 40;'
                                         '408 155 102;'
                                         '416 25 52;'
                                         '424 51 106;'
                                         '432 47 72;'
                                         '440 91 110;'
                                         '448 29 168;'
                                         '456 29 114;'
                                         '464 247 58;'
                                         '472 29 118;'
                                         '480 89 180;'
                                         '488 91 122;'
                                         '496 157 62;'
                                         '504 55 84;'
                                         '512 31 64;'
                                         '528 17 66;'
                                         '544 35 68;'
                                         '560 227 420;'
                                         '576 65 96;'
                                         '592 19 74;'
                                         '608 37 76;'
                                         '624 41 234;'
                                         '640 39 80;'
                                         '656 185 82;'
                                         '672 43 252;'
                                         '688 21 86;'
                                         '704 155 44;'
                                         '720 79 120;'
                                         '736 139 92;'
                                         '752 23 94;'
                                         '768 217 48;'
                                         '784 25 98;'
                                         '800 17 80;'
                                         '816 127 102;'
                                         '832 25 52;'
                                         '848 239 106;'
                                         '864 17 48;'
                                         '880 137 110;'
                                         '896 215 112;'
                                         '912 29 114;'
                                         '928 15 58;'
                                         '944 147 118;'
                                         '960 29 60;'
                                         '976 59 122;'
                                         '992 65 124;'
                                         '1008 55 84;'
                                         '1024 31 64;'
                                         '1056 17 66;'
                                         '1088 171 204;'
                                         '1120 67 140;'
                                         '1152 35 72;'
                                         '1184 19 74;'
                                         '1216 39 76;'
                                         '1248 19 78;'
                                         '1280 199 240;'
                                         '1312 21 82;'
                                         '1344 211 252;'
                                         '1376 21 86;'
                                         '1408 43 88;'
                                         '1440 149 60;'
                                         '1472 45 92;'
                                         '1504 49 846;'
                                         '1536 71 48;'
                                         '1568 13 28;'
                                         '1600 17 80;'
                                         '1632 25 102;'
                                         '1664 183 104;'
                                         '1696 55 954;'
                                         '1728 127 96;'
                                         '1760 27 110;'
                                         '1792 29 112;'
                                         '1824 29 114;'
                                         '1856 57 116;'
                                         '1888 45 354;'
                                         '1920 31 120;'
                                         '1952 59 610;'
                                         '1984 185 124;'
                                         '2016 113 420;'
                                         '2048 31 64;'
                                         '2112 17 66;'
                                         '2176 171 136;'
                                         '2240 209 420;'
                                         '2304 253 216;'
                                         '2368 367 444;'
                                         '2432 265 456;'
                                         '2496 181 468;'
                                         '2560 39 80;'
                                         '2624 27 164;'
                                         '2688 127 504;'
                                         '2752 143 172;'
                                         '2816 43 88;'
                                         '2880 29 300;'
                                         '2944 45 92;'
                                         '3008 157 188;'
                                         '3072 47 96;'
                                         '3136 13 28;'
                                         '3200 111 240;'
                                         '3264 443 204;'
                                         '3328 51 104;'
                                         '3392 51 212;'
                                         '3456 451 192;'
                                         '3520 257 220;'
                                         '3584 57 336;'
                                         '3648 313 228;'
                                         '3712 271 232;'
                                         '3776 179 236;'
                                         '3840 331 120;'
                                         '3904 363 244;'
                                         '3968 375 248;'
                                         '4032 127 168;'
                                         '4096 31 64;'
                                         '4160 33 130;'
                                         '4224 43 264;'
                                         '4288 33 134;'
                                         '4352 477 408;'
                                         '4416 35 138;'
                                         '4480 233 280;'
                                         '4544 357 142;'
                                         '4608 337 480;'
                                         '4672 37 146;'
                                         '4736 71 444;'
                                         '4800 71 120;'
                                         '4864 37 152;'
                                         '4928 39 462;'
                                         '4992 127 234;'
                                         '5056 39 158;'
                                         '5120 39 80;'
                                         '5184 31 96;'
                                         '5248 113 902;'
                                         '5312 41 166;'
                                         '5376 251 336;'
                                         '5440 43 170;'
                                         '5504 21 86;'
                                         '5568 43 174;'
                                         '5632 45 176;'
                                         '5696 45 178;'
                                         '5760 161 120;'
                                         '5824 89 182;'
                                         '5888 323 184;'
                                         '5952 47 186;'
                                         '6016 23 94;'
                                         '6080 47 190;'
                                         '6144 263 480')