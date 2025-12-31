import argparse
import os
import shutil
import json
import struct
from decoder import Decoder
from transpiler import Transpiler
from dispatcher import DispatcherGenerator
from lib_gen import LibGenerator

def main():
    parser = argparse.ArgumentParser(description="RV32 ELF to Minecraft Datapack Compile")
    parser.add_argument("input_file", help="Path to the binary file (.bin) or hex dump")
    parser.add_argument("output_dir", help="Output directory for the datapack")
    parser.add_argument("--namespace", default="rv32", help="Datapack namespace")
    args = parser.parse_args()
    
    print(f"Reading {args.input_file}...")
    with open(args.input_file, 'rb') as f:
        data = f.read()

    decoder = Decoder(data)
    instructions = decoder.decode_all()
    print(f"Decoded {len(instructions)} instructions.")

    if os.path.exists(args.output_dir):
        shutil.rmtree(args.output_dir)
    
    data_dir = os.path.join(args.output_dir, "data", args.namespace, "function")
    os.makedirs(data_dir, exist_ok=True)
    
    transpiler = Transpiler(instructions, args.namespace)
    for instr in instructions:
        lines = transpiler.convert_instruction(instr)
        fname = f"instr_{hex(instr.address)[2:]}.mcfunction"
        with open(os.path.join(data_dir, fname), 'w') as f:
            f.write("\n".join(lines))
            
    dispatch_dir = os.path.join(data_dir, "dispatch")
    os.makedirs(dispatch_dir, exist_ok=True)
    dispatcher = DispatcherGenerator(instructions, dispatch_dir, args.namespace)
    dispatcher.generate()

    lib_gen = LibGenerator(data_dir, args.namespace)
    lib_gen.generate()
    
    with open(os.path.join(args.output_dir, "pack.mcmeta"), 'w') as f:
        json.dump({"pack": {"pack_format": 48, "description": "MC-RVVM 1.21"}}, f, indent=4)

    padded_data = data + b'\x00' * ((4 - len(data) % 4) % 4)
    with open(os.path.join(data_dir, "mem", "load_prog.mcfunction"), 'w') as f:
        f.write("# Load binary image into RAM\n")
        for i in range(0, len(padded_data), 4):
            val = struct.unpack_from("<i", padded_data, i)[0]
            f.write(f"data modify storage {args.namespace}:ram data[{i//4}] set value {val}\n")

    with open(os.path.join(data_dir, "mem", "load_image_data.mcfunction"), 'w') as f:
        f.write("# Default empty image loader. Overwrite with img2mc.py output if needed.\n")

    with open(os.path.join(data_dir, "reset.mcfunction"), 'w') as f:
        for i in range(32): f.write(f"scoreboard players set x{i} rv_reg 0\n")
        f.write(f"scoreboard players set pc {args.namespace}_pc 0\n")
        f.write("scoreboard players set #halt rv_temp 0\n")
        f.write("scoreboard players set #halt_notified rv_temp 0\n")
        f.write(f"data modify storage {args.namespace}:uart buffer set value []\n")
        f.write(f"data merge storage {args.namespace}:io {{}}\n")
        f.write(f"function {args.namespace}:mem/load_image_data\n")
        f.write(f"function {args.namespace}:mem/load_prog\n")
        f.write("tellraw @a [{\"text\":\"[MC-RVVM] VM Reset.\",\"color\":\"yellow\"}]\n")
    
    with open(os.path.join(data_dir, "step.mcfunction"), 'w') as f:
        f.write(f"function {args.namespace}:dispatch/root\n")
        f.write(f"function {args.namespace}:debug/dump_inline\n")

    with open(os.path.join(data_dir, "tick.mcfunction"), 'w') as f:
        for _ in range(16000):
            f.write(f"execute unless score #halt rv_temp matches 1 run function {args.namespace}:dispatch/root\n")
        f.write(f"execute if score #halt rv_temp matches 1 unless score #halt_notified rv_temp matches 1 run tellraw @a [{{\"text\":\"[MC-RVVM] Execution Halted.\",\"color\":\"red\"}}]\n")
        f.write(f"execute if score #halt rv_temp matches 1 run scoreboard players set #halt_notified rv_temp 1\n")
        
    with open(os.path.join(data_dir, "load.mcfunction"), 'w') as f:
        f.write("scoreboard objectives add rv_reg dummy\n")
        f.write(f"scoreboard objectives add {args.namespace}_pc dummy\n")
        f.write("scoreboard objectives add rv_temp dummy\n")
        f.write("scoreboard objectives add rv_const dummy\n")
        f.write("scoreboard players set #four rv_const 4\n")
        f.write("scoreboard players set #two rv_const 2\n")
        f.write("scoreboard players set #thirty_two rv_const 32\n")
        f.write("scoreboard players set #zero rv_const 0\n")
        f.write("scoreboard players set #min_int rv_const -2147483647\n")
        f.write("scoreboard players remove #min_int rv_const 1\n")
        for i in range(31):
            f.write(f"scoreboard players set #p_{i} rv_const {1 << i}\n")
        f.write("scoreboard players operation #p_31 rv_const = #min_int rv_const\n")
        f.write(f"data merge storage {args.namespace}:io {{}}\n")
        f.write(f"function {args.namespace}:mem/init\n")
        f.write(f"function {args.namespace}:reset\n")
        f.write("tellraw @a [{\"text\":\"[MC-RVVM] Loaded.\",\"color\":\"green\"}]\n")

    for tag_path in ["function", "functions"]:
        tag_dir = os.path.join(args.output_dir, "data", "minecraft", "tags", tag_path)
        os.makedirs(tag_dir, exist_ok=True)
        with open(os.path.join(tag_dir, "tick.json"), 'w') as f:
            json.dump({"values": [f"{args.namespace}:tick"]}, f, indent=4)
        with open(os.path.join(tag_dir, "load.json"), 'w') as f:
            json.dump({"values": [f"{args.namespace}:load"]}, f, indent=4)

    print("Done! Datapack generated at:", args.output_dir)

if __name__ == "__main__":
    main()
