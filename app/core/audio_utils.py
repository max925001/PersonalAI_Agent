import array
import audioop
import miniaudio
from loguru import logger


def ulaw_to_pcm(ulaw_bytes: bytes) -> bytes:
    """Converts 8kHz 8-bit Mu-law bytes to 8kHz 16-bit Mono PCM bytes."""
    return audioop.ulaw2lin(ulaw_bytes, 2)


def pcm_to_ulaw(pcm_bytes: bytes) -> bytes:
    """Converts 8kHz 16-bit Mono PCM bytes to 8kHz 8-bit Mu-law bytes."""
    return audioop.lin2ulaw(pcm_bytes, 2)


def resample_pcm_8k_to_16k(pcm_bytes: bytes) -> bytes:
    """Resamples 8kHz 16-bit PCM to 16kHz 16-bit PCM using linear interpolation."""
    in_array = array.array('h')
    in_array.frombytes(pcm_bytes)
    
    if not in_array:
        return b""
        
    out_array = array.array('h')
    for i in range(len(in_array) - 1):
        s1 = in_array[i]
        s2 = in_array[i + 1]
        out_array.append(s1)
        out_array.append((s1 + s2) // 2)
        
    if len(in_array) > 0:
        out_array.append(in_array[-1])
        out_array.append(in_array[-1])
        
    return out_array.tobytes()


def resample_pcm_16k_to_8k(pcm_bytes: bytes) -> bytes:
    """Downsamples 16kHz 16-bit PCM to 8kHz 16-bit PCM by averaging adjacent samples."""
    in_array = array.array('h')
    in_array.frombytes(pcm_bytes)
    
    if not in_array:
        return b""
        
    out_array = array.array('h')
    for i in range(0, len(in_array) - 1, 2):
        out_array.append((in_array[i] + in_array[i + 1]) // 2)
        
    return out_array.tobytes()


def resample_pcm_generic(pcm_samples: array.array, from_rate: int, to_rate: int) -> array.array:
    """Generic resampling using linear interpolation."""
    if from_rate == to_rate:
        return pcm_samples
        
    ratio = from_rate / to_rate
    out_len = int(len(pcm_samples) / ratio)
    out_array = array.array('h')
    
    for i in range(out_len):
        idx = i * ratio
        idx_low = int(idx)
        idx_high = min(idx_low + 1, len(pcm_samples) - 1)
        weight = idx - idx_low
        s1 = pcm_samples[idx_low]
        s2 = pcm_samples[idx_high]
        interpolated = int(s1 * (1 - weight) + s2 * weight)
        out_array.append(interpolated)
        
    return out_array


def mp3_to_ulaw_8k(mp3_bytes: bytes) -> bytes:
    """Decodes MP3 bytes and encodes them directly to 8kHz Mono Mu-law bytes for Twilio."""
    try:
        # 1. Decode MP3 to raw PCM via miniaudio
        decoded = miniaudio.decode(mp3_bytes)
        
        # 2. Extract 16-bit samples
        raw_samples = array.array('h', decoded.samples)
        
        # 3. Downmix to Mono if stereo/multichannel
        if decoded.nchannels > 1:
            mono_samples = array.array('h')
            for i in range(0, len(raw_samples), decoded.nchannels):
                # Take average of all channels
                channels_sum = sum(raw_samples[i : i + decoded.nchannels])
                mono_samples.append(channels_sum // decoded.nchannels)
            raw_samples = mono_samples
            
        # 4. Resample to 8kHz (Twilio standard)
        resampled_samples = resample_pcm_generic(raw_samples, decoded.sample_rate, 8000)
        
        # 5. Convert 8kHz PCM to Mu-law
        return pcm_to_ulaw(resampled_samples.tobytes())
        
    except Exception as e:
        logger.error(f"Failed to transcode MP3 to Mu-law: {e}")
        return b""
