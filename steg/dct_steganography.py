import cv2
import numpy as np
import struct
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
import pathlib
from concurrent.futures import ThreadPoolExecutor
import zlib
from typing import Tuple, Optional, Callable

def generate_key(password: str, salt: bytes = None) -> tuple:
    """Generate encryption key from password using PBKDF2"""
    if not salt:
        salt = os.urandom(16)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return Fernet(key), salt

def validate_image_path(image_path: str) -> None:
    """Validate image path and format"""
    if not isinstance(image_path, str):
        raise ValueError("Image path must be a string")
    
    path = pathlib.Path(image_path)
    if not path.exists():
        raise FileNotFoundError("Image file does not exist")
    
    if path.suffix.lower() not in ['.png', '.jpg', '.jpeg']:
        raise ValueError("Unsupported image format")

def zigzag_indices(block_size):
    indices = np.arange(block_size**2).reshape(block_size, block_size)
    return np.concatenate([np.diagonal(indices[::-1, :], i)[::(2*(i % 2)-1)]
                            for i in range(1-block_size, block_size)])

def estimate_capacity(image_path: str) -> int:
    """Estimate the maximum data capacity of the image"""
    image = cv2.imread(image_path)
    height, width = image.shape[:2]
    return (height // 8) * (width // 8) - 4  # Subtract 4 bytes for length header

def process_block(args: Tuple) -> Tuple:
    """Process a single block for parallel execution"""
    block, data_byte, zigzag_order = args
    block_float = np.float32(block)
    dct_block = cv2.dct(block_float)
    if data_byte is not None:
        dct_block.flat[zigzag_order[1]] = data_byte
    block_hidden = cv2.idct(dct_block)
    return np.uint8(block_hidden), dct_block.flat[zigzag_order[1]]

def secure_hide_data_dct(
    image_path: str, 
    data: bytes, 
    password: str, 
    progress_callback: Optional[Callable[[float], None]] = None
) -> str:
    """Enhanced secure hide_data_dct with compression and parallel processing"""
    try:
        validate_image_path(image_path)
        if not data or not isinstance(data, bytes):
            raise ValueError("Invalid data format")

        # Compress data before encryption
        compressed_data = zlib.compress(data, level=9)
        
        # Generate encryption key and encrypt data
        fernet, salt = generate_key(password)
        encrypted_data = fernet.encrypt(compressed_data)
        final_data = salt + encrypted_data

        image = cv2.imread(image_path)
        if image is None:
            raise ValueError("Failed to load image")

        height, width = image.shape[:2]
        block_size = 8
        total_blocks = (height // block_size) * (width // block_size)

        if len(final_data) + 4 > total_blocks:
            raise ValueError("Data size too large for image")

        # Prepare data with length header
        final_data = struct.pack('>I', len(final_data)) + final_data
        data_length = len(final_data)

        # Prepare blocks for parallel processing
        blocks = []
        zigzag_order = zigzag_indices(block_size)
        
        for row in range(0, height, block_size):
            for col in range(0, width, block_size):
                block = image[row:row+block_size, col:col+block_size]
                data_byte = final_data[len(blocks)] if len(blocks) < data_length else None
                blocks.append((block, data_byte, zigzag_order))

        # Process blocks in parallel
        processed_blocks = []
        with ThreadPoolExecutor() as executor:
            for i, result in enumerate(executor.map(process_block, blocks)):
                processed_blocks.append(result[0])
                if progress_callback:
                    progress_callback(i / len(blocks))

        # Reconstruct image
        for i, (row, col) in enumerate([(r, c) 
                                      for r in range(0, height, block_size) 
                                      for c in range(0, width, block_size)]):
            if i < len(processed_blocks):
                image[row:row+block_size, col:col+block_size] = processed_blocks[i]

        output_path = f'hidden_dct_image_{os.urandom(4).hex()}.png'
        cv2.imwrite(output_path, image, [cv2.IMWRITE_PNG_COMPRESSION, 9])
        return output_path

    except Exception as e:
        raise RuntimeError(f"Failed to hide data: {str(e)}")
    finally:
        # Clear sensitive data
        if 'fernet' in locals(): del fernet
        if 'encrypted_data' in locals(): del encrypted_data
        if 'compressed_data' in locals(): del compressed_data

def secure_extract_data_dct(
    image_path: str, 
    password: str,
    progress_callback: Optional[Callable[[float], None]] = None
) -> bytes:
    """Enhanced secure extract_data_dct with parallel processing"""
    try:
        validate_image_path(image_path)
        hidden_image = cv2.imread(image_path)
        if hidden_image is None:
            raise ValueError("Failed to load image")

        height, width = hidden_image.shape[:2]
        block_size = 8

        # Prepare blocks for parallel processing
        blocks = []
        zigzag_order = zigzag_indices(block_size)
        
        for row in range(0, height, block_size):
            for col in range(0, width, block_size):
                block = hidden_image[row:row+block_size, col:col+block_size]
                blocks.append((block, None, zigzag_order))

        # Extract data in parallel
        extracted_data = []
        with ThreadPoolExecutor() as executor:
            for i, result in enumerate(executor.map(process_block, blocks)):
                extracted_data.append(result[1])
                if progress_callback:
                    progress_callback(i / len(blocks))

        # Process extracted data
        data_length = struct.unpack('>I', bytes(extracted_data[:4]))[0]
        extracted_bytes = bytes(extracted_data[4:4+data_length])
        
        # Split salt and decrypt
        salt = extracted_bytes[:16]
        encrypted_data = extracted_bytes[16:]
        fernet, _ = generate_key(password, salt)
        
        try:
            decrypted_data = fernet.decrypt(encrypted_data)
            # Decompress data
            decompressed_data = zlib.decompress(decrypted_data)
            return decompressed_data
        except Exception:
            raise ValueError("Invalid password or corrupted data")

    except Exception as e:
        raise RuntimeError(f"Failed to extract data: {str(e)}")
    finally:
        if 'fernet' in locals(): del fernet
        if 'decrypted_data' in locals(): del decrypted_data
