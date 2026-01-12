import re

class BlockOptimizer:
    def __init__(self, instructions, map_file=None):
        self.instructions = sorted(instructions, key=lambda x: x.address)
        self.instr_map = {i.address: i for i in self.instructions}
        self.map_file = map_file
        self.leaders = set()
        self.blocks = []
        self.weights = {} # Address -> Weight

    def optimize(self):
        self._identify_leaders()
        self._build_blocks()
        self._calc_hotspots()
        return self.blocks, self.weights

    def _identify_leaders(self):
        if self.instructions:
            self.leaders.add(self.instructions[0].address)

        if self.map_file:
            with open(self.map_file, 'r') as f:
                for line in f:
                    match = re.search(r'^\s+(0x[0-9a-fA-F]+)\s+([a-zA-Z_][a-zA-Z0-9_]*)', line)
                    if match:
                        addr = int(match.group(1), 16)
                        if addr in self.instr_map:
                            self.leaders.add(addr)

        for i, instr in enumerate(self.instructions):
            is_branch = instr.name in ["beq", "bne", "blt", "bge", "bltu", "bgeu"]
            is_jump = instr.name in ["jal", "jalr"]
            is_ecall = instr.name in ["ecall", "ebreak"]
            
            if is_branch or instr.name == "jal":
                target_addr = (instr.address + instr.imm) & 0xFFFFFFFF
                
                if target_addr in self.instr_map:
                    self.leaders.add(target_addr)

            if (is_branch or is_jump or is_ecall) and i + 1 < len(self.instructions):
                self.leaders.add(self.instructions[i+1].address)

    def _build_blocks(self):
        current_block = []
        sorted_leaders = sorted(list(self.leaders))
        leader_set = self.leaders

        for instr in self.instructions:
            if instr.address in leader_set and current_block:
                self._finalize_block(current_block)
                current_block = []
            
            current_block.append(instr)
            
        if current_block:
            self._finalize_block(current_block)

    def _finalize_block(self, instrs):
        if not instrs: return
        start_addr = instrs[0].address
        self.blocks.append({
            "start": start_addr,
            "end": instrs[-1].address,
            "instrs": instrs,
            "length": len(instrs)
        })

    def _calc_hotspots(self):
        for instr in self.instructions:
            self.weights[instr.address] = 1

        for block in self.blocks:
            w = 1
            if self.map_file:
                pass

        map_funcs = set()
        if self.map_file:
             with open(self.map_file, 'r') as f:
                for line in f:
                    match = re.search(r'^\s+(0x[0-9a-fA-F]+)\s+([a-zA-Z_][a-zA-Z0-9_]*)', line)
                    if match:
                        map_funcs.add(int(match.group(1), 16))

        for block in self.blocks:
            addr = block["start"]
            w = 1
            if addr in map_funcs:
                w = 100
            elif addr in self.leaders:
                pass
            
            self.weights[addr] = w

        for instr in self.instructions:
            if instr.name in ["beq", "bne", "blt", "bge", "bltu", "bgeu", "jal"]:
                target = (instr.address + instr.imm) & 0xFFFFFFFF
                if target in self.weights and target <= instr.address:
                    self.weights[target] += 50
                elif target in self.weights:
                    self.weights[target] += 5
