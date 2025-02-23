import numpy as np
from scipy.io import wavfile
from scipy import signal
import struct
import zlib
from tqdm import tqdm
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
import secrets
from concurrent.futures import ThreadPoolExecutor
import multiprocessing
from typing import List, Tuple, Optional, Union, ByteString

class EchoHidingConfig:
    def __init__(self, delay=64, echo_gain=0.5, min_snr=15, password=None,
                 frequency_band=(1000, 4000), # Frequency band for hiding (Hz)
                 quality_threshold=35.0,      # Minimum PSNR in dB
                 use_parallel=True):          # Enable parallel processing
        self.delay = delay
        self.echo_gain = echo_gain
        self.min_snr = min_snr  # minimum signal-to-noise ratio in dB
        self.password = password.encode() if password else None
        self.salt = os.urandom(16)  # Generate fresh salt for each instance
        self.frequency_band = frequency_band
        self.quality_threshold = quality_threshold
        self.use_parallel = use_parallel
        self.num_threads = multiprocessing.cpu_count()

def generate_key(password: bytes, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password))

def validate_audio_file(audio_path: str) -> None:
    if not os.path.exists(audio_path):
        raise ValueError("Audio file does not exist")
    
    # Check file size (e.g., max 100MB)
    if os.path.getsize(audio_path) > 100_000_000:
        raise ValueError("Audio file too large")
    
    # Validate file extension
    if not audio_path.lower().endswith(('.wav', '.wave')):
        raise ValueError("Unsupported audio format")

def normalize_audio(audio):
    max_amplitude = np.max(np.abs(audio))
    if max_amplitude > 0:
        return audio / max_amplitude
    return audio

def analyze_audio_segment(segment):
    """Analyze audio segment for optimal echo parameters"""
    rms = np.sqrt(np.mean(segment**2))
    zero_crossings = np.sum(np.diff(np.signbit(segment)))
    return rms, zero_crossings

def apply_bandpass_filter(audio, sample_rate, freq_band):
    """Apply bandpass filter to isolate optimal frequency band"""
    nyquist = sample_rate / 2
    b, a = signal.butter(4, [freq_band[0]/nyquist, freq_band[1]/nyquist], btype='band')
    return signal.filtfilt(b, a, audio)

def calculate_psnr(original, modified):
    """Calculate Peak Signal-to-Noise Ratio"""
    mse = np.mean((original - modified) ** 2)
    if mse == 0:
        return float('inf')
    return 20 * np.log10(np.max(np.abs(original)) / np.sqrt(mse))

def process_audio_chunk(args: Tuple[np.ndarray, str, EchoHidingConfig]) -> np.ndarray:
    """Process audio chunk for parallel processing"""
    chunk, binary_data_segment, config = args
    echo_signal = np.zeros_like(chunk)
    
    samples_per_bit = config.delay * 2
    for i, bit in enumerate(binary_data_segment):
        start_sample = i * samples_per_bit
        end_sample = start_sample + config.delay
        if start_sample >= len(chunk):
            break
            
        echo = chunk[start_sample:min(end_sample, len(chunk))] * config.echo_gain
        if bit == '1' and start_sample + config.delay < len(chunk):
            echo_signal[start_sample + config.delay:min(end_sample + config.delay, len(chunk))] = echo
            
    return echo_signal

def extract_chunk_data(args: Tuple[np.ndarray, EchoHidingConfig]) -> str:
    """Extract binary data from audio chunk"""
    chunk, config = args
    binary_data = ''
    samples_per_bit = config.delay * 2
    
    for i in range(0, len(chunk) - samples_per_bit, samples_per_bit):
        original_segment = chunk[i:i + config.delay]
        echo_segment = chunk[i + config.delay:i + samples_per_bit]
        
        corr = np.correlate(original_segment, echo_segment)[0]
        auto_corr = np.correlate(original_segment, original_segment)[0]
        threshold = auto_corr * config.echo_gain * 0.5
        
        binary_data += '1' if corr > threshold else '0'
    
    return binary_data

def hide_data_echo(audio_path: str, data: ByteString, config: Optional[EchoHidingConfig] = None) -> None:
    try:
        validate_audio_file(audio_path)
        if config is None:
            config = EchoHidingConfig()

        # Add random delay to prevent timing attacks
        secrets.SystemRandom().randint(1, 100)
        
        # Encrypt data if password is provided
        if config.password:
            fernet = Fernet(generate_key(config.password, config.salt))
            data = config.salt + fernet.encrypt(data)
        
        sample_rate, audio = wavfile.read(audio_path)
        
        # Handle multi-channel audio
        if len(audio.shape) > 1:
            # Use mean of channels for processing
            audio_mono = np.mean(audio, axis=1)
        else:
            audio_mono = audio.copy()
        
        # Apply bandpass filter to isolate optimal frequency band
        audio_filtered = apply_bandpass_filter(audio_mono, sample_rate, config.frequency_band)
        
        # Analyze audio segments for optimal parameters
        segment_size = sample_rate // 10  # 100ms segments
        segments = np.array_split(audio_filtered, len(audio_filtered) // segment_size)
        
        # Adapt echo gain based on local audio characteristics
        gains = []
        for segment in segments:
            rms, crossings = analyze_audio_segment(segment)
            optimal_gain = min(config.echo_gain, 0.8 * config.echo_gain * (1 / (rms + 1e-6)))
            gains.append(optimal_gain)
        
        # Split binary data for parallel processing
        binary_data = ''.join(format(byte, '08b') for byte in data)
        chunk_size = len(binary_data) // config.num_threads
        binary_chunks = [binary_data[i:i + chunk_size] 
                        for i in range(0, len(binary_data), chunk_size)]

        # Parallel processing for echo generation
        if config.use_parallel:
            chunks = np.array_split(audio_filtered, config.num_threads)
            with ThreadPoolExecutor(max_workers=config.num_threads) as executor:
                echo_signals = list(executor.map(process_audio_chunk, 
                    [(chunk, chunk_data, config) 
                     for chunk, chunk_data in zip(chunks, binary_chunks)]))
                echo_signal = np.concatenate(echo_signals)
        else:
            echo_signal = process_audio_chunk((audio_filtered, binary_data, config))

        # Mix and check quality
        stego_audio = normalize_audio(audio + echo_signal)
        psnr = calculate_psnr(audio, stego_audio)
        
        if psnr < config.quality_threshold:
            raise ValueError(f"Audio quality below threshold: {psnr:.2f} dB")

        # Preserve original audio format and channels
        if len(audio.shape) > 1:
            # Apply echo to all channels
            stego_audio = np.column_stack([stego_audio for _ in range(audio.shape[1])])

        # Save with original bit depth
        wavfile.write('hidden_echo_audio.wav', sample_rate, stego_audio)

    except Exception as e:
        raise ValueError(f"Failed to hide data: {str(e)}")

def extract_data_echo(audio_path: str, config: Optional[EchoHidingConfig] = None) -> ByteString:
    try:
        validate_audio_file(audio_path)
        if config is None:
            config = EchoHidingConfig()

        # Add random delay to prevent timing attacks
        secrets.SystemRandom().randint(1, 100)
        
        sample_rate, stego_audio = wavfile.read(audio_path)
        
        # Handle multi-channel audio
        if len(stego_audio.shape) > 1:
            stego_audio = np.mean(stego_audio, axis=1)
        
        # Apply same bandpass filter as hiding
        stego_audio = apply_bandpass_filter(stego_audio, sample_rate, config.frequency_band)
        
        # Parallel processing for extraction
        if config.use_parallel:
            chunks = np.array_split(stego_audio, config.num_threads)
            with ThreadPoolExecutor(max_workers=config.num_threads) as executor:
                binary_chunks = list(executor.map(extract_chunk_data, 
                    [(chunk, config) for chunk in chunks]))
                binary_data = ''.join(binary_chunks)
        else:
            binary_data = extract_chunk_data((stego_audio, config))

        try:
            # Extract checksum and verify
            checksum_bytes = bytes(int(binary_data[i:i + 8], 2) for i in range(0, 32, 8))
            original_checksum = struct.unpack('>I', checksum_bytes)[0]
            
            # Extract the actual data
            data_binary = binary_data[32:]
            extracted_data = bytearray(int(data_binary[i:i + 8], 2) 
                                    for i in range(0, len(data_binary) - len(data_binary) % 8, 8))
            
            # Verify checksum
            if zlib.crc32(extracted_data) != original_checksum:
                raise ValueError("Checksum verification failed")
            
            if config.password:
                # First 16 bytes are the salt
                salt = extracted_data[:16]
                encrypted_data = extracted_data[16:]
                
                fernet = Fernet(generate_key(config.password, salt))
                try:
                    extracted_data = fernet.decrypt(encrypted_data)
                except Exception:
                    raise ValueError("Invalid password or corrupted data")
            
            return extracted_data
        except Exception as e:
            raise ValueError(f"Failed to extract data: {str(e)}")

    except Exception as e:
        raise ValueError("Failed to extract data from audio file")
