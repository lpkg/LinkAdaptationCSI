import itpp

def channel_frequency_response(fft_size,
                               relative_speed,
                               channel_model,
                               nrof_subframes):
    
    carrier_freq = 2.0e9 # 2 GHz
    subcarrier_spacing = 15000 # Hz
    
    sampling_frequency = subcarrier_spacing * fft_size
    sampling_interval = 1.0 / sampling_frequency

    relative_speed = relative_speed # in m/s
    doppler_frequency = (carrier_freq / 3e8) * relative_speed
    norm_doppler = doppler_frequency * sampling_interval

    frame_duration = 1.0e-3 # 1 ms
    frame_samples = int(frame_duration / sampling_interval)
    
    model = None
    if channel_model == 'ITU_PEDESTRIAN_A':
        model = itpp.comm.CHANNEL_PROFILE.ITU_Pedestrian_A
    elif channel_model == 'ITU_PEDESTRIAN_B':
        model = itpp.comm.CHANNEL_PROFILE.ITU_Pedestrian_B
    elif channel_model == 'ITU_VEHICULAR_A':
        model = itpp.comm.CHANNEL_PROFILE.ITU_Vehicular_A
    elif channel_model == 'ITU_VEHICULAR_B':
        model = itpp.comm.CHANNEL_PROFILE.ITU_Vehicular_B
    else:
        print('Specified channel model %s not configured in %s'%(model, __file__))

    channel_spec = itpp.comm.Channel_Specification(model)
    channel = itpp.comm.TDL_Channel(channel_spec, sampling_interval)
    
    nrof_taps = channel.taps()
        
    channel.set_norm_doppler(norm_doppler)
    
    # Generate channel coefficients for a few frames
    channel_coeff = itpp.cmat()
    channel_coeff.set_size(nrof_subframes, nrof_taps, False)
    
    for frame_index in range(nrof_subframes):
        frame_start_sample = int(frame_index * frame_samples)
        channel.set_time_offset(frame_start_sample)
        frame_channel_coeff = itpp.cmat()
        channel.generate(1, frame_channel_coeff)
        channel_coeff.set_row(frame_index, frame_channel_coeff.get_row(0))
        
    freq_resp = itpp.cmat()
    channel.calc_frequency_response(channel_coeff, freq_resp, fft_size)
    
    return freq_resp