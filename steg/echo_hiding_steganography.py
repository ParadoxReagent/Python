import numpy as np
from scipy.io import wavfile
import struct


def hide_data_echo(audio_path, data):
    sample_rate, audio = wavfile.read(audio_path)

    delay = 64
    echo_gain = 0.5

    # Add data length header (4 bytes) to the data
    data_length = len(data)
    data = struct.pack('>I', data_length) + data
    data_length += 4

    # Convert the data into a binary representation
    binary_data = ''.join(format(byte, '08b') for byte in data)

    # Calculate the number of samples required to hide the data
    samples_per_bit = delay * 2
    total_samples = len(binary_data) * samples_per_bit

    if total_samples > len(audio):
        raise ValueError("Data size is too large for the given audio file.")

    # Generate the echo signal
    echo_signal = np.zeros_like(audio)
    for i, bit in enumerate(binary_data):
        start_sample = i * samples_per_bit
        end_sample = start_sample + delay
        echo = audio[start_sample:end_sample] * echo_gain

        if bit == '1':
            echo_signal[start_sample + delay:end_sample + delay] = echo

    # Mix the echo signal with the original audio
    stego_audio = audio + echo_signal

    # Save the audio file with the hidden data
    wavfile.write('hidden_echo_audio.wav', sample_rate, stego_audio)


def extract_data_echo(audio_path):
    sample_rate, stego_audio = wavfile.read(audio_path)

    delay = 64
    samples_per_bit = delay * 2

    binary_data = ''
    for i in range(0, len(stego_audio) - samples_per_bit, samples_per_bit):
        original_segment = stego_audio[i:i + delay]
        echo_segment = stego_audio[i + delay:i + samples_per_bit]

        corr = np.sum(original_segment * echo_segment)
        threshold = np.sum(original_segment**2) * 0.5 * 0.5
        binary_data += '1' if corr > threshold else '0'

    # Retrieve data length header (4 bytes)
    data_length = struct.unpack('>I', bytes(int(binary_data[i:i + 8], 2) for i in range(0, 32, 8)))[0]
    extracted_data = bytearray(int(binary_data[i:i + 8], 2) for i in range(32, 32 + data_length * 8, 8))
    return extracted_data
