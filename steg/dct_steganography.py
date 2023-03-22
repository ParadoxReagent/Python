import cv2
import numpy as np
import struct


def zigzag_indices(block_size):
    indices = np.arange(block_size**2).reshape(block_size, block_size)
    return np.concatenate([np.diagonal(indices[::-1, :], i)[::(2*(i % 2)-1)]
                            for i in range(1-block_size, block_size)])


def hide_data_dct(image_path, data, progress_callback=None):
    image = cv2.imread(image_path)
    height, width = image.shape[:2]
    block_size = 8

    # Calculate the total number of 8x8 blocks in the image
    total_blocks = (height // block_size) * (width // block_size)

    # Check if the data can be hidden in the image
    data_length = len(data)
    if data_length + 4 > total_blocks:  # +4 for data length header (4 bytes)
        raise ValueError("Data size is too large for the given image.")

    data_index = 0

    # Add data length header (4 bytes) to the data
    data = struct.pack('>I', data_length) + data
    data_length += 4

    zigzag_order = zigzag_indices(block_size)

    for row in range(0, height, block_size):
        for col in range(0, width, block_size):
            block = image[row:row+block_size, col:col+block_size]

            # Apply DCT
            block_float = np.float32(block)
            dct_block = cv2.dct(block_float)

            # Hide data in DCT coefficients using zigzag ordering
            if data_index < data_length:
                dct_block.flat[zigzag_order[1]] = data[data_index]
                data_index += 1

            # Inverse DCT
            block_hidden = cv2.idct(dct_block)
            image[row:row+block_size, col:col+block_size] = np.uint8(block_hidden)

            if data_index >= data_length:
                break

    cv2.imwrite('hidden_dct_image.jpg', image)


def extract_data_dct(image_path):
    hidden_image = cv2.imread(image_path)
    height, width = hidden_image.shape[:2]
    block_size = 8

    extracted_data = []

    zigzag_order = zigzag_indices(block_size)

    for row in range(0, height, block_size):
        for col in range(0, width, block_size):
            block = hidden_image[row:row+block_size, col:col+block_size]

            # Apply DCT
            block_float = np.float32(block)
            dct_block = cv2.dct(block_float)

            # Extract data from DCT coefficients using zigzag ordering
            extracted_data.append(int(dct_block.flat[zigzag_order[1]]))

    # Retrieve data length header (4 bytes)
    data_length = struct.unpack('>I', bytes(extracted_data[:4]))[0]
    return bytes(extracted_data[4:4+data_length])
