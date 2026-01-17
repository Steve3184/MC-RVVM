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
from block_optimizer import BlockOptimizer

def main():
    parser = argparse.ArgumentParser(description="RV32 ELF to Minecraft Datapack Compile")
    parser.add_argument("input_file", help="Path to the binary file (.bin) or hex dump")
    parser.add_argument("output_dir", help="Output directory for the datapack")
    parser.add_argument("--namespace", default="rv32", help="Datapack namespace")
    parser.add_argument("--map_file", help="Path to linker map file (.map) for optimization")
    parser.add_argument("--optimize", "-O", action="store_true", help="Enable block optimization")
    parser.add_argument("--ipt", type=int, default=2500, help="Instructions per tick (max 4800)")
    args = parser.parse_args()
    
    ipt = min(args.ipt, 4800)
    print(f"Reading {args.input_file}...")
    with open(args.input_file, 'rb') as f:
        data = f.read()

    decoder = Decoder(data)
    instructions = decoder.decode_all()
    print(f"Decoded {len(instructions)} instructions.")

    blocks = []
    weights = {}
    block_starts = set()

    if args.optimize:
        print("Optimizing blocks...")
        optimizer = BlockOptimizer(instructions, args.map_file)
        blocks, weights = optimizer.optimize()
        block_starts = {b['start'] for b in blocks}
        print(f"Identified {len(blocks)} blocks.")
        sorted_weights = sorted(weights.items(), key=lambda x: x[1], reverse=True)
        print("Top 3 Hotspots:")
        for addr, w in sorted_weights[:3]:
            print(f"  {hex(addr)}: Weight {w}")

    if os.path.exists(args.output_dir):
        shutil.rmtree(args.output_dir)
    
    data_dir = os.path.join(args.output_dir, "data", args.namespace, "function")
    os.makedirs(data_dir, exist_ok=True)
    
    dispatch_dir = os.path.join(data_dir, "dispatch")
    os.makedirs(dispatch_dir, exist_ok=True)
    
    dispatcher = DispatcherGenerator(instructions, dispatch_dir, args.namespace)
    dispatch_depth = dispatcher.generate(weights if args.optimize else None, block_starts if args.optimize else None)
    if dispatch_depth is None: dispatch_depth = 0

    lib_gen = LibGenerator(data_dir, args.namespace)
    ascii_depth, lib_costs = lib_gen.generate()
    if ascii_depth is None: ascii_depth = 0
    if "ecall/dispatch" not in lib_costs: lib_costs["ecall/dispatch"] = 20 + ascii_depth
    
    transpiler = Transpiler(instructions, args.namespace)
    max_instr_cost = 0
    func_pattern = re.compile(f"function {args.namespace}:([a-zA-Z0-9_./]+)")
    
    instr_lines_map = {}
    for instr in instructions:
        lines = transpiler.convert_instruction(instr, include_pc_update=True)
        lines.append(f"scoreboard players remove #ipt_count {args.namespace}_temp 1")
        if instr.name in ["ecall", "ebreak"]:
            lines.append("return 0")
        instr_lines_map[instr.address] = lines
        
        cost = 0
        for line in lines:
            cost += 1
            match = func_pattern.search(line)
            if match:
                called_func = match.group(1)
                if called_func in lib_costs: cost += lib_costs[called_func]
                elif "ascii" in called_func: cost += ascii_depth
                else: cost += 50 
        if cost > max_instr_cost: max_instr_cost = cost

    if not args.optimize:
        for instr in instructions:
            fname = f"i_{hex(instr.address)[2:]}.mcfunction"
            with open(os.path.join(data_dir, fname), 'w') as f:
                f.write("\n".join(instr_lines_map[instr.address]))

    if args.optimize:
        for block in blocks:
            fname = f"b_{hex(block['start'])[2:]}.mcfunction"
            content = []
            
            content.append(f"scoreboard players remove #ipt_count {args.namespace}_temp {block['length']}")

            last_idx = len(block['instrs']) - 1
            for i, instr in enumerate(block['instrs']):
                is_last = (i == last_idx)
                is_jmp_type = instr.name in ["jal", "jalr", "beq", "bne", "blt", "bge", "bltu", "bgeu"]
                
                if is_last and is_jmp_type:
                    content.extend(transpiler.convert_instruction(instr, include_pc_update=True))
                else:
                    content.extend(transpiler.convert_instruction(instr, include_pc_update=False))
                
                if instr.name in ["ecall", "ebreak"]:
                    content.append("return 0")
            
            last_instr = block['instrs'][-1]
            next_addr = (last_instr.address + 4) & 0xFFFFFFFF
            
            is_uncond_jump = last_instr.name in ["jal", "jalr", "ecall", "ebreak"]
            is_branch = last_instr.name in ["beq", "bne", "blt", "bge", "bltu", "bgeu"]
            
            if not is_branch and not is_uncond_jump:
                 content.append(f"scoreboard players set pc {args.namespace}_pc {next_addr}")

            cond = f"execute if score #ipt_count {args.namespace}_temp matches 1.. if score #sleep_ticks {args.namespace}_temp matches ..0 unless score #halt {args.namespace}_temp matches 1 run"
            target_addr = None
            if is_branch or last_instr.name == "jal":
                 target_addr = (last_instr.address + last_instr.imm) & 0xFFFFFFFF
            
            if is_branch:
                if target_addr is not None and target_addr in block_starts:
                     content.append(f"{cond} execute if score pc {args.namespace}_pc matches {target_addr} run function {args.namespace}:b_{hex(target_addr)[2:]}")
                if next_addr in block_starts:
                     content.append(f"{cond} execute if score pc {args.namespace}_pc matches {next_addr} run function {args.namespace}:b_{hex(next_addr)[2:]}")
            elif last_instr.name == "jal":
                if target_addr is not None and target_addr in block_starts:
                    content.append(f"{cond} function {args.namespace}:b_{hex(target_addr)[2:]}")
            elif last_instr.name == "jalr":
                 content.append(f"{cond} function {args.namespace}:dispatch/root")
            elif last_instr.name in ["ecall", "ebreak"]:
                 if next_addr in block_starts:
                     content.append(f"{cond} function {args.namespace}:b_{hex(next_addr)[2:]}")
            else:
                 if next_addr in block_starts:
                     content.append(f"{cond} function {args.namespace}:b_{hex(next_addr)[2:]}")

            with open(os.path.join(data_dir, fname), 'w') as f:
                f.write("\n".join(content))

    total_chain = ipt * (max_instr_cost + dispatch_depth)
    print(f"Calculated Max Potential Chain: {total_chain} commands per tick (IPT={ipt})")
    
    with open(os.path.join(args.output_dir, "pack.mcmeta"), 'w') as f:
        json.dump({"pack": {"pack_format": 48, "description": "MC-RVVM 1.21"}}, f, indent=4)

    padded_data = data + b'\x00' * ((4 - len(data) % 4) % 4)
    with open(os.path.join(data_dir, "mem", "load_data.mcfunction"), 'w') as f:
        batch_size = 128
        words = [struct.unpack_from("<i", padded_data, i)[0] for i in range(0, len(padded_data), 4)]
        for i in range(0, len(words), batch_size):
            batch_str = ",".join(map(str, words[i:i+batch_size]))
            f.write(f"data modify storage {args.namespace}:temp Batch set value [{batch_str}]\n")
            f.write(f"execute store result storage {args.namespace}:io start_idx int 1 run scoreboard players set #temp {args.namespace}_temp {i}\n")
            f.write(f"function {args.namespace}:mem/load_batch with storage {args.namespace}:io\n")

    with open(os.path.join(data_dir, "reset.mcfunction"), 'w') as f:
        for i in range(32): f.write(f"scoreboard players set x{i} {args.namespace}_reg 0\n")
        f.write(f"scoreboard players set pc {args.namespace}_pc 0\n")
        f.write(f"scoreboard players set #halt {args.namespace}_temp 0\n")
        f.write(f"scoreboard players set #halt_notified {args.namespace}_temp 0\n")
        f.write(f"scoreboard players set #sleep_ticks {args.namespace}_temp 0\n")
        f.write(f"scoreboard players set #ipt_count {args.namespace}_temp 0\n")
        f.write(f"data modify storage {args.namespace}:uart buffer set value []\n")
        f.write(f"data modify storage {args.namespace}:uart rx_buf set value []\n")
        f.write(f"data merge storage {args.namespace}:io {{}}\n")
        f.write(f"function {args.namespace}:mem/load_data\n")
        f.write(f"function {args.namespace}:load_extra_data\n")
        f.write("tellraw @a [{\"text\":\"[MC-RVVM] VM Reset.\",\"color\":\"yellow\"}]\n")
    
    with open(os.path.join(data_dir, "tick.mcfunction"), 'w') as f:
        f.write(f"function {args.namespace}:input/tick\n")
        f.write(f"scoreboard players set #is_sleeping {args.namespace}_temp 0\n")
        f.write(f"execute if score #sleep_ticks {args.namespace}_temp matches 1.. run scoreboard players set #is_sleeping {args.namespace}_temp 1\n")
        f.write(f"execute if score #is_sleeping {args.namespace}_temp matches 1 run scoreboard players remove #sleep_ticks {args.namespace}_temp 1\n")
        f.write(f"execute if score #is_sleeping {args.namespace}_temp matches 1 run return 0\n")
        
        f.write(f"scoreboard players set #ipt_count {args.namespace}_temp {ipt}\n")
        loop_count = 10 if args.optimize else 300
        for _ in range(loop_count):
            f.write(f"execute if score #ipt_count {args.namespace}_temp matches 1.. if score #sleep_ticks {args.namespace}_temp matches ..0 unless score #halt {args.namespace}_temp matches 1 run function {args.namespace}:dispatch/root\n")
        
        f.write(f"execute if score #halt {args.namespace}_temp matches 1 unless score #halt_notified {args.namespace}_temp matches 1 run tellraw @a [{{\"text\":\"[MC-RVVM] Stopped.\",\"color\":\"red\"}}]\n")
        f.write(f"execute if score #halt {args.namespace}_temp matches 1 run scoreboard players set #halt_notified {args.namespace}_temp 1\n")

    with open(os.path.join(data_dir, "load.mcfunction"), 'w') as f:
        f.write("gamerule maxCommandChainLength 2147483646\n")
        f.write(f"scoreboard objectives add {args.namespace}_reg dummy\n")
        f.write(f"scoreboard objectives add {args.namespace}_pc dummy\n")
        f.write(f"scoreboard objectives add {args.namespace}_temp dummy\n")
        f.write(f"scoreboard objectives add {args.namespace}_const dummy\n")
        f.write(f"scoreboard players set #four {args.namespace}_const 4\n")
        f.write(f"scoreboard players set #two {args.namespace}_const 2\n")
        for i in range(31): f.write(f"scoreboard players set #p_{i} {args.namespace}_const {1 << i}\n")
        f.write(f"scoreboard players set #min_int {args.namespace}_const -2147483647\n")
        f.write(f"scoreboard players remove #min_int {args.namespace}_const 1\n")
        f.write(f"scoreboard players operation #p_31 {args.namespace}_const = #min_int {args.namespace}_const\n")
        f.write(f"data merge storage {args.namespace}:io {{}}\n")
        f.write(f"function {args.namespace}:mem/init\n")
        f.write(f"function {args.namespace}:reset\n")
        f.write("tellraw @a [{\"text\":\"[MC-RVVM] Loaded.\",\"color\":\"green\"}]\n")

    tag_dir = os.path.join(args.output_dir, "data", "minecraft", "tags", "function")
    os.makedirs(tag_dir, exist_ok=True)
    with open(os.path.join(tag_dir, "tick.json"), 'w') as f:
        json.dump({"values": [f"{args.namespace}:tick"]}, f, indent=4)
    with open(os.path.join(tag_dir, "load.json"), 'w') as f:
        json.dump({"values": [f"{args.namespace}:load"]}, f, indent=4)

    print("Done! Datapack generated at:", args.output_dir)

if __name__ == "__main__":
    main()