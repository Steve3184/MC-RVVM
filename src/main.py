import argparse
import os
import shutil
import json
import struct
import re
from decoder import Decoder
from transpiler import Transpiler
from dispatcher import DispatcherGenerator
from lib_gen import LibGenerator

IPT = 2500

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
    
    dispatch_dir = os.path.join(data_dir, "dispatch")
    os.makedirs(dispatch_dir, exist_ok=True)
    dispatcher = DispatcherGenerator(instructions, dispatch_dir, args.namespace)
    dispatch_depth = dispatcher.generate()
    if dispatch_depth is None: dispatch_depth = 0

    lib_gen = LibGenerator(data_dir, args.namespace)
    ascii_depth, lib_costs = lib_gen.generate()
    if ascii_depth is None: ascii_depth = 0
    
    if "ecall/dispatch" not in lib_costs: lib_costs["ecall/dispatch"] = 20 + ascii_depth
    
    transpiler = Transpiler(instructions, args.namespace)
    max_instr_cost = 0
    
    func_pattern = re.compile(f"function {args.namespace}:([a-zA-Z0-9_./]+)")
    
    for instr in instructions:
        lines = transpiler.convert_instruction(instr)
        fname = f"instr_{hex(instr.address)[2:]}.mcfunction"
        
        cost = 0
        for line in lines:
            cost += 1
            match = func_pattern.search(line)
            if match:
                called_func = match.group(1)
                if called_func in lib_costs:
                    cost += lib_costs[called_func]
                elif "ascii" in called_func:
                    cost += ascii_depth
                else:
                    cost += 50 
        
        if cost > max_instr_cost:
            max_instr_cost = cost

        with open(os.path.join(data_dir, fname), 'w') as f:
            f.write("\n".join(lines))
            
    
    chain_per_step = dispatch_depth + max_instr_cost + 5
    total_chain = IPT * chain_per_step
    total_chain = int(total_chain * 1.1)
    if total_chain < 65536: total_chain = 65536
    
    print(f"Calculated Max Chain: Step={chain_per_step} (Dispatch={dispatch_depth}, MaxInstr={max_instr_cost}), Total={total_chain}")
    
    with open(os.path.join(args.output_dir, "pack.mcmeta"), 'w') as f:
        json.dump({"pack": {"pack_format": 48, "description": "MC-RVVM 1.21"}}, f, indent=4)

    padded_data = data + b'\x00' * ((4 - len(data) % 4) % 4)
    with open(os.path.join(data_dir, "mem", "load_data.mcfunction"), 'w') as f:
        batch_size = 128
        words = []
        for i in range(0, len(padded_data), 4):
            words.append(struct.unpack_from("<i", padded_data, i)[0])
        
        for i in range(0, len(words), batch_size):
            batch = words[i:i+batch_size]
            batch_str = ",".join(map(str, batch))
            f.write(f"data modify storage {args.namespace}:temp Batch set value [{batch_str}]\n")
            f.write(f"execute store result storage {args.namespace}:io start_idx int 1 run scoreboard players set #temp rv_temp {i}\n")
            f.write(f"function {args.namespace}:mem/load_batch with storage {args.namespace}:io\n")

    with open(os.path.join(data_dir, "reset.mcfunction"), 'w') as f:
        for i in range(32): f.write(f"scoreboard players set x{i} rv_reg 0\n")
        f.write(f"scoreboard players set pc {args.namespace}_pc 0\n")
        f.write("scoreboard players set #halt rv_temp 0\n")
        f.write("scoreboard players set #halt_notified rv_temp 0\n")
        f.write(f"data modify storage {args.namespace}:uart buffer set value []\n")
        f.write(f"data merge storage {args.namespace}:io {{}}\n")
        f.write(f"function {args.namespace}:mem/load_data\n")
        f.write(f"function {args.namespace}:load_extra_data\n")
        f.write("tellraw @a [{\"text\":\"[MC-RVVM] VM Reset.\",\"color\":\"yellow\"}]\n")
    
    with open(os.path.join(data_dir, "step.mcfunction"), 'w') as f:
        f.write(f"function {args.namespace}:dispatch/root\n")
        f.write(f"function {args.namespace}:debug/dump_inline\n")

    with open(os.path.join(data_dir, "tick.mcfunction"), 'w') as f:
        for _ in range(IPT):
            f.write(f"execute unless score #halt rv_temp matches 1 run function {args.namespace}:dispatch/root\n")
        f.write(f"execute if score #halt rv_temp matches 1 unless score #halt_notified rv_temp matches 1 run tellraw @a [{{\"text\":\"[MC-RVVM] Stopped.\",\"color\":\"red\"}}]\n")
        f.write(f"execute if score #halt rv_temp matches 1 run scoreboard players set #halt_notified rv_temp 1\n")
        
    with open(os.path.join(data_dir, "load.mcfunction"), 'w') as f:
        f.write(f"gamerule maxCommandChainLength 1145141919\n")#{total_chain + 50}\n")
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
