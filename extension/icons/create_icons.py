import struct
import zlib

def create_png(width, height, color_hex):
    """Create a simple solid color PNG"""
    # Parse color
    r = int(color_hex[1:3], 16)
    g = int(color_hex[3:5], 16)
    b = int(color_hex[5:7], 16)
    
    # Create raw pixel data (RGB)
    raw_data = b''
    for y in range(height):
        raw_data += b'\x00'  # Filter byte (none)
        for x in range(width):
            raw_data += bytes([r, g, b])
    
    # Compress pixel data
    compressed = zlib.compress(raw_data, 9)
    
    # PNG signature
    signature = b'\x89PNG\r\n\x1a\n'
    
    # IHDR chunk
    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    ihdr_crc = zlib.crc32(b'IHDR' + ihdr_data) & 0xffffffff
    ihdr = struct.pack('>I', 13) + b'IHDR' + ihdr_data + struct.pack('>I', ihdr_crc)
    
    # IDAT chunk
    idat_crc = zlib.crc32(b'IDAT' + compressed) & 0xffffffff
    idat = struct.pack('>I', len(compressed)) + b'IDAT' + compressed + struct.pack('>I', idat_crc)
    
    # IEND chunk
    iend_crc = zlib.crc32(b'IEND') & 0xffffffff
    iend = struct.pack('>I', 0) + b'IEND' + struct.pack('>I', iend_crc)
    
    return signature + ihdr + idat + iend

# Create icons
sizes = ['16', '32', '48', '128']
color = '#14b8a6'  # Teal color

for size in sizes:
    png_data = create_png(int(size), int(size), color)
    with open(f'icon-{size}.png', 'wb') as f:
        f.write(png_data)
    print(f'✅ Created icon-{size}.png')

print('\n✅ All icons created!')
