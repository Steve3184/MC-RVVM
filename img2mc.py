import sys
import struct

def bin_to_mc(input_file, output_file, namespace="rv32"):
    with open(input_file, 'rb') as f:
        data = f.read()
    
    data += b'\x00' * ((4 - len(data) % 4) % 4)
    words = [struct.unpack('<i', data[i:i+4])[0] for i in range(0, len(data), 4)]
    
    with open(output_file, 'w') as f:
        f.write(f"# Loading {input_file} into storage {namespace}:kernel Image\n")
        f.write(f"data modify storage {namespace}:kernel Image set value []\n")
        
        batch_size = 128
        for i in range(0, len(words), batch_size):
            batch = words[i:i+batch_size]
            batch_str = ",".join(map(str, batch))
            f.write(f"data modify storage {namespace}:temp Batch set value [{batch_str}]\n")
            f.write(f"data modify storage {namespace}:kernel Image append from storage {namespace}:temp Batch[]\n")
        
        f.write(f"data remove storage {namespace}:temp Batch\n")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: img2mc.py <input_bin> <output_mcfunction>")
    else:
        namespace = "rv32"
        if len(sys.argv) > 3:
            namespace = sys.argv[3]
        bin_to_mc(sys.argv[1], sys.argv[2], namespace)