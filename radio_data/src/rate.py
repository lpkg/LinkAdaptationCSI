from itpp import bvec, vec, zeros, zeros_b

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
