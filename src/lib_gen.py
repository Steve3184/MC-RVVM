import os

class LibGenerator:
    def __init__(self, output_dir, namespace="rv32"):
        self.output_dir = output_dir
        self.namespace = namespace
        self.lib_costs = {}

    def generate(self):
        for d in ["lib", "mem", "ecall", "debug"]:
            os.makedirs(os.path.join(self.output_dir, d), exist_ok=True)
        self.gen_bitwise()
        self.gen_shifts()
        self.gen_math()
        self.gen_mem()
        self.gen_load_batch()
        ascii_depth = self.gen_uart()
        self.gen_data_loader()
        self.gen_exec_cmd()
        self.gen_ecall()
        self.gen_debug()
        return ascii_depth, self.lib_costs

    def _register_cost(self, name, lines, deps=None):
        count = len(lines) if isinstance(lines, list) else lines
        dep_cost = 0
        if deps:
            for d in deps:
                if isinstance(d, tuple):
                    d_name, multiplier = d
                    dep_cost += self.lib_costs.get(d_name, 0) * multiplier
                else:
                    dep_cost += self.lib_costs.get(d, 0)
        self.lib_costs[name] = count + dep_cost

    def gen_exec_cmd(self):
        MAX_CMD_LEN = 256
        args_keys = [f'c{i}' for i in range(MAX_CMD_LEN)]
        args_json = "{" + ",".join([f'{k}:""' for k in args_keys]) + "}"
        
        macro_call = "$" + "".join([f'$(c{i})' for i in range(MAX_CMD_LEN)])
        
        lines = [
            f'data modify storage {self.namespace}:io args set value {args_json}',
            'scoreboard players set #idx rv_temp 0',
            'scoreboard players operation #addr rv_temp = x10 rv_reg',
            f'function {self.namespace}:ecall/exec_cmd_loop',
            f'function {self.namespace}:ecall/exec_cmd_run with storage {self.namespace}:io'
        ]
        with open(os.path.join(self.output_dir, "ecall", "exec_cmd.mcfunction"), 'w') as f:
            f.write("\n".join(lines) + "\n")
            
        lines_loop = [
            f'execute if score #idx rv_temp matches {MAX_CMD_LEN}.. run return 0',
            
            f'scoreboard players operation #addr_temp rv_temp = #addr rv_temp',
            f'scoreboard players operation #off rv_temp = #addr_temp rv_temp',
            f'scoreboard players operation #off rv_temp %= #four rv_const',
            f'scoreboard players operation #addr_temp rv_temp /= #four rv_const',
            f'execute store result storage {self.namespace}:io addr int 1 run scoreboard players get #addr_temp rv_temp',
            f'execute store result storage {self.namespace}:io off int 1 run scoreboard players get #off rv_temp',
            f'function {self.namespace}:mem/read_lb with storage {self.namespace}:io',
            
            'execute if score #res rv_temp matches 0 run return 0',
            
            'scoreboard players operation #char rv_temp = #res rv_temp',
            f'function {self.namespace}:lib/ascii/map',
            f'data modify storage {self.namespace}:io char set from storage {self.namespace}:uart char_esc',
            
            f'execute store result storage {self.namespace}:io temp_idx int 1 run scoreboard players get #idx rv_temp',
            f'function {self.namespace}:ecall/exec_cmd_append with storage {self.namespace}:io',
            
            'scoreboard players add #addr rv_temp 1',
            'scoreboard players add #idx rv_temp 1',
            f'function {self.namespace}:ecall/exec_cmd_loop'
        ]
        with open(os.path.join(self.output_dir, "ecall", "exec_cmd_loop.mcfunction"), 'w') as f:
            f.write("\n".join(lines_loop) + "\n")

        lines_append = [
             f'$data modify storage {self.namespace}:io args.c$(temp_idx) set value "$(char)"',
        ]
        with open(os.path.join(self.output_dir, "ecall", "exec_cmd_append.mcfunction"), 'w') as f:
            f.write("\n".join(lines_append) + "\n")

        lines_run = [
            f'function {self.namespace}:ecall/exec_cmd_run_macro with storage {self.namespace}:io args'
        ]
        with open(os.path.join(self.output_dir, "ecall", "exec_cmd_run.mcfunction"), 'w') as f:
            f.write("\n".join(lines_run) + "\n")

        lines_run_macro = [
            macro_call
        ]
        with open(os.path.join(self.output_dir, "ecall", "exec_cmd_run_macro.mcfunction"), 'w') as f:
             f.write("\n".join(lines_run_macro) + "\n")

    def gen_data_loader(self):
        lines_main = [
            f"$data modify storage {self.namespace}:temp CopyList set from storage $(path) $(nbt)",
            f"execute store result score #curr_idx rv_temp run data get storage {self.namespace}:io dest_idx",
            f"function {self.namespace}:mem/copy_loop"
        ]
        with open(os.path.join(self.output_dir, "mem", "copy_storage_to_ram.mcfunction"), 'w') as f:
            f.write("\n".join(lines_main) + "\n")
        self._register_cost("mem/copy_storage_to_ram", lines_main)
        with open(os.path.join(self.output_dir, "load_extra_data.mcfunction"), 'w') as f:
            f.write("# dummy file\n")
        
        lines_loop = [
            f"execute unless data storage {self.namespace}:temp CopyList[0] run return 0",
            f"execute store result storage {self.namespace}:io idx int 1 run scoreboard players get #curr_idx rv_temp",
            f"function {self.namespace}:mem/copy_step with storage {self.namespace}:io",
            f"data remove storage {self.namespace}:temp CopyList[0]",
            f"scoreboard players add #curr_idx rv_temp 1",
            f"function {self.namespace}:mem/copy_loop"
        ]
        with open(os.path.join(self.output_dir, "mem", "copy_loop.mcfunction"), 'w') as f:
             f.write("\n".join(lines_loop) + "\n")
        
        lines_step = [
            f"$data modify storage {self.namespace}:ram data[$(idx)] set from storage {self.namespace}:temp CopyList[0]"
        ]
        with open(os.path.join(self.output_dir, "mem", "copy_step.mcfunction"), 'w') as f:
             f.write("\n".join(lines_step) + "\n")

    def gen_load_batch(self):
        lines = [
            f"execute store result storage {self.namespace}:io idx int 1 run scoreboard players get #temp rv_temp",
            f"function {self.namespace}:mem/load_batch_step with storage {self.namespace}:io",
            f"data remove storage {self.namespace}:temp Batch[0]",
            f"scoreboard players add #temp rv_temp 1",
            f"execute if data storage {self.namespace}:temp Batch[0] run function {self.namespace}:mem/load_batch"
        ]
        with open(os.path.join(self.output_dir, "mem", "load_batch.mcfunction"), 'w') as f:
            f.write("\n".join(lines) + "\n")

        lines_step = [
            f"$data modify storage {self.namespace}:ram data[$(idx)] set from storage {self.namespace}:temp Batch[0]"
        ]
        with open(os.path.join(self.output_dir, "mem", "load_batch_step.mcfunction"), 'w') as f:
            f.write("\n".join(lines_step) + "\n")

    def gen_ascii_map(self):
        def generate_tree(chars, path):
            os.makedirs(os.path.join(self.output_dir, "lib", "ascii", os.path.dirname(path)), exist_ok=True)
            with open(os.path.join(self.output_dir, "lib", "ascii", f"{path}.mcfunction"), 'w') as f:
                if len(chars) == 1:
                    c, val = chars[0]
                    escaped = c.replace('\\', '\\\\').replace('"', '\\"')
                    f.write(f'data modify storage {self.namespace}:uart char set value "{escaped}"\n')
                    macro_escaped = c.replace('\\', '\\\\\\\\').replace('"', '\\\\\\"')
                    f.write(f'data modify storage {self.namespace}:uart char_esc set value "{macro_escaped}"\n')
                    
                    self._register_cost(f"lib/ascii/{path}", 2)
                    return 1
                mid = len(chars) // 2
                low, high = chars[:mid], chars[mid:]
                f.write(f"execute if score #char rv_temp matches {low[0][1]}..{low[-1][1]} run function {self.namespace}:lib/ascii/{path}_0\n")
                f.write(f"execute if score #char rv_temp matches {high[0][1]}..{high[-1][1]} run function {self.namespace}:lib/ascii/{path}_1\n")
                
                self._register_cost(f"lib/ascii/{path}", 2)
                
                d1 = generate_tree(low, f"{path}_0")
                d2 = generate_tree(high, f"{path}_1")
                return 1 + max(d1, d2)
        
        all_chars = [(chr(i), i) for i in range(32, 127)]
        all_chars.sort(key=lambda x: x[1])
        return generate_tree(all_chars, "map")

    def gen_uart(self):
        ascii_depth = self.gen_ascii_map()
        
        lines_flush = [
            f"execute if data storage {self.namespace}:uart buffer[0] run tellraw @a {{\"nbt\":\"buffer[]\",\"storage\":\"{self.namespace}:uart\",\"separator\":\"\"}}",
            f"data modify storage {self.namespace}:uart buffer set value []"
        ]
        with open(os.path.join(self.output_dir, "lib", "uart_flush.mcfunction"), 'w') as f:
            f.write("\n".join(lines_flush) + "\n")
        self._register_cost("lib/uart_flush", lines_flush)
        
        lines_putc = [
            "scoreboard players operation #char rv_temp = x10 rv_reg",
            f"execute if score #char rv_temp matches 10 run function {self.namespace}:lib/uart_flush",
            f"execute unless score #char rv_temp matches 10 run function {self.namespace}:lib/ascii/map",
            f"execute unless score #char rv_temp matches 10 run data modify storage {self.namespace}:uart buffer append from storage {self.namespace}:uart char"
        ]
        with open(os.path.join(self.output_dir, "lib", "uart_putc.mcfunction"), 'w') as f:
            f.write("\n".join(lines_putc) + "\n")
        self._register_cost("lib/uart_putc", lines_putc, deps=["lib/uart_flush"])
        self.lib_costs["lib/uart_putc"] += ascii_depth
        
        return ascii_depth

    def gen_math(self):
        mul_lines = []
        mul_lines.append("scoreboard players set #res rv_temp 0")
        mul_lines.append("scoreboard players operation #t1 rv_temp = #op1 rv_temp")
        mul_lines.append("scoreboard players operation #t2 rv_temp = #op2 rv_temp")
        for i in range(32):
            mul_lines.append(f"scoreboard players operation #bit rv_temp = #t2 rv_temp")
            mul_lines.append(f"scoreboard players operation #bit rv_temp %= #two rv_const")
            mul_lines.append(f"execute unless score #bit rv_temp matches 0 run scoreboard players operation #res rv_temp += #t1 rv_temp")
            mul_lines.append(f"scoreboard players operation #t1 rv_temp *= #two rv_const")
            mul_lines.append(f"scoreboard players operation #t2 rv_temp /= #two rv_const")
        
        with open(os.path.join(self.output_dir, "lib", "mul.mcfunction"), 'w') as f:
            f.write("\n".join(mul_lines) + "\n")
        self._register_cost("lib/mul", mul_lines)
        
        lines_add64 = [
            "scoreboard players operation #rh rv_temp += #u1h rv_temp",
            "scoreboard players operation #old_rl rv_temp = #rl rv_temp",
            "scoreboard players operation #rl rv_temp += #u1l rv_temp",
            "scoreboard players operation #c1 rv_temp = #rl rv_temp",
            "scoreboard players operation #c1 rv_temp -= #min_int rv_const",
            "scoreboard players operation #c2 rv_temp = #old_rl rv_temp",
            "scoreboard players operation #c2 rv_temp -= #min_int rv_const",
            "execute if score #c1 rv_temp < #c2 rv_temp run scoreboard players add #rh rv_temp 1"
        ]
        with open(os.path.join(self.output_dir, "lib", "add64_u1.mcfunction"), 'w') as f:
            f.write("\n".join(lines_add64) + "\n")
        self._register_cost("lib/add64_u1", lines_add64)

        lines_shl64 = [
            "scoreboard players operation #u1h rv_temp *= #two rv_const",
            "execute if score #u1l rv_temp matches ..-1 run scoreboard players add #u1h rv_temp 1",
            "scoreboard players operation #u1l rv_temp *= #two rv_const"
        ]
        with open(os.path.join(self.output_dir, "lib", "shl64_u1.mcfunction"), 'w') as f:
            f.write("\n".join(lines_shl64) + "\n")
        self._register_cost("lib/shl64_u1", lines_shl64)

        for op in ["mulh", "mulhu", "mulhsu"]:
            lines = []
            lines.append("scoreboard players set #rh rv_temp 0\nscoreboard players set #rl rv_temp 0")
            lines.append("scoreboard players operation #u1l rv_temp = #op1 rv_temp\nscoreboard players set #u1h rv_temp 0")
            lines.append("scoreboard players operation #u2l rv_temp = #op2 rv_temp\nscoreboard players set #u2h rv_temp 0")
            if op == "mulh":
                lines.append("execute if score #op1 rv_temp matches ..-1 run scoreboard players set #u1h rv_temp -1")
                lines.append("execute if score #op2 rv_temp matches ..-1 run scoreboard players set #u2h rv_temp -1")
            elif op == "mulhsu":
                lines.append("execute if score #op1 rv_temp matches ..-1 run scoreboard players set #u1h rv_temp -1")
            for i in range(32):
                lines.append(f"scoreboard players operation #bit rv_temp = #u2l rv_temp")
                lines.append(f"scoreboard players operation #bit rv_temp %= #two rv_const")
                lines.append(f"execute unless score #bit rv_temp matches 0 run function {self.namespace}:lib/add64_u1")
                lines.append(f"function {self.namespace}:lib/shl64_u1")
                lines.append(f"scoreboard players operation #op1 rv_temp = #u2l rv_temp")
                lines.append(f"scoreboard players set #op2 rv_temp 1")
                lines.append(f"function {self.namespace}:lib/srl")
                lines.append(f"scoreboard players operation #u2l rv_temp = #res rv_temp")
            lines.append("scoreboard players operation #res rv_temp = #rh rv_temp")
            
            with open(os.path.join(self.output_dir, "lib", f"{op}.mcfunction"), 'w') as f:
                f.write("\n".join(lines) + "\n")
            self._register_cost(f"lib/{op}", lines, deps=[("lib/add64_u1", 32), ("lib/shl64_u1", 32), ("lib/srl", 32)])

        divu_lines = []
        divu_lines.append("scoreboard players set #q rv_temp 0\nscoreboard players set #r rv_temp 0")
        divu_lines.append("execute if score #u2 rv_temp matches 0 run scoreboard players set #q rv_temp -1")
        divu_lines.append("execute if score #u2 rv_temp matches 0 run scoreboard players operation #r rv_temp = #u1 rv_temp")
        divu_lines.append("execute if score #u2 rv_temp matches 0 run return 0")
        divu_lines.append("scoreboard players operation #tu2 rv_temp = #u2 rv_temp")
        divu_lines.append("scoreboard players operation #tu2 rv_temp -= #min_int rv_const")
        for i in range(31, -1, -1):
            divu_lines.append(f"scoreboard players operation #r rv_temp *= #two rv_const")
            if i == 31:
                divu_lines.append("scoreboard players set #bit rv_temp 0")
                divu_lines.append("execute if score #u1 rv_temp matches ..-1 run scoreboard players set #bit rv_temp 1")
            else:
                divu_lines.append(f"scoreboard players operation #bit rv_temp = #u1 rv_temp")
                if i > 0: divu_lines.append(f"scoreboard players operation #bit rv_temp /= #p_{i} rv_const")
                divu_lines.append(f"scoreboard players operation #bit rv_temp %= #two rv_const")
                divu_lines.append(f"execute if score #bit rv_temp matches ..-1 run scoreboard players add #bit rv_temp 2")
            divu_lines.append(f"scoreboard players operation #r rv_temp += #bit rv_temp")
            divu_lines.append("scoreboard players operation #tr rv_temp = #r rv_temp")
            divu_lines.append("scoreboard players operation #tr rv_temp -= #min_int rv_const")
            divu_lines.append("execute if score #tr rv_temp >= #tu2 rv_temp run scoreboard players operation #r rv_temp -= #u2 rv_temp")
            if i > 0: divu_lines.append(f"execute if score #tr rv_temp >= #tu2 rv_temp run scoreboard players operation #q rv_temp += #p_{i} rv_const")
            else: divu_lines.append(f"execute if score #tr rv_temp >= #tu2 rv_temp run scoreboard players add #q rv_temp 1")
        
        with open(os.path.join(self.output_dir, "lib", "divu_logic.mcfunction"), 'w') as f:
            f.write("\n".join(divu_lines) + "\n")
        self._register_cost("lib/divu_logic", divu_lines)

        for op in ["divu", "remu", "div", "rem"]:
            lines = []
            if op == "divu":
                lines.append("scoreboard players operation #u1 rv_temp = #op1 rv_temp")
                lines.append("scoreboard players operation #u2 rv_temp = #op2 rv_temp")
                lines.append(f"function {self.namespace}:lib/divu_logic")
                lines.append("scoreboard players operation #res rv_temp = #q rv_temp")
            elif op == "remu":
                lines.append("scoreboard players operation #u1 rv_temp = #op1 rv_temp")
                lines.append("scoreboard players operation #u2 rv_temp = #op2 rv_temp")
                lines.append(f"function {self.namespace}:lib/divu_logic")
                lines.append("scoreboard players operation #res rv_temp = #r rv_temp")
            elif op in ["div", "rem"]:
                lines.append("scoreboard players set #s1 rv_temp 0\nscoreboard players set #s2 rv_temp 0")
                lines.append("execute if score #op1 rv_temp matches ..-1 run scoreboard players set #s1 rv_temp 1")
                lines.append("execute if score #op2 rv_temp matches ..-1 run scoreboard players set #s2 rv_temp 1")
                lines.append("scoreboard players operation #u1 rv_temp = #op1 rv_temp")
                lines.append("execute if score #s1 rv_temp matches 1 run scoreboard players set #zero rv_temp 0")
                lines.append("execute if score #s1 rv_temp matches 1 run scoreboard players operation #u1 rv_temp = #zero rv_temp")
                lines.append("execute if score #s1 rv_temp matches 1 run scoreboard players operation #u1 rv_temp -= #op1 rv_temp")
                lines.append("scoreboard players operation #u2 rv_temp = #op2 rv_temp")
                lines.append("execute if score #s2 rv_temp matches 1 run scoreboard players set #zero rv_temp 0")
                lines.append("execute if score #s2 rv_temp matches 1 run scoreboard players operation #u2 rv_temp = #zero rv_temp")
                lines.append("execute if score #s2 rv_temp matches 1 run scoreboard players operation #u2 rv_temp -= #op2 rv_temp")
                lines.append(f"function {self.namespace}:lib/divu_logic")
                if op == "div":
                    lines.append("scoreboard players operation #res rv_temp = #q rv_temp")
                    lines.append("execute unless score #s1 rv_temp = #s2 rv_temp if score #q rv_temp matches 1.. run scoreboard players set #zero rv_temp 0")
                    lines.append("execute unless score #s1 rv_temp = #s2 rv_temp if score #q rv_temp matches 1.. run scoreboard players operation #res rv_temp = #zero rv_temp")
                    lines.append("execute unless score #s1 rv_temp = #s2 rv_temp if score #q rv_temp matches 1.. run scoreboard players operation #res rv_temp -= #q rv_temp")
                else:
                    lines.append("scoreboard players operation #res rv_temp = #r rv_temp")
                    lines.append("execute if score #s1 rv_temp matches 1 if score #r rv_temp matches 1.. run scoreboard players set #zero rv_temp 0")
                    lines.append("execute if score #s1 rv_temp matches 1 if score #r rv_temp matches 1.. run scoreboard players operation #res rv_temp = #zero rv_temp")
                    lines.append("execute if score #s1 rv_temp matches 1 if score #r rv_temp matches 1.. run scoreboard players operation #res rv_temp -= #r rv_temp")
            
            with open(os.path.join(self.output_dir, "lib", f"{op}.mcfunction"), 'w') as f:
                f.write("\n".join(lines) + "\n")
            self._register_cost(f"lib/{op}", lines, deps=["lib/divu_logic"])

    def gen_bitwise(self):
        for op in ["and", "or", "xor"]:
            lines = ["scoreboard players set #res rv_temp 0", "scoreboard players operation #t1 rv_temp = #op1 rv_temp", "scoreboard players operation #t2 rv_temp = #op2 rv_temp", "execute if score #t1 rv_temp matches ..-1 run scoreboard players operation #t1 rv_temp -= #min_int rv_const", "execute if score #t2 rv_temp matches ..-1 run scoreboard players operation #t2 rv_temp -= #min_int rv_const"]
            for i in range(31):
                lines.append(f"scoreboard players operation #b1 rv_temp = #t1 rv_temp")
                lines.append("scoreboard players operation #b1 rv_temp %= #two rv_const")
                lines.append("execute if score #b1 rv_temp matches ..-1 run scoreboard players add #b1 rv_temp 2")
                lines.append("scoreboard players operation #b2 rv_temp = #t2 rv_temp")
                lines.append("scoreboard players operation #b2 rv_temp %= #two rv_const")
                lines.append("execute if score #b2 rv_temp matches ..-1 run scoreboard players add #b2 rv_temp 2")
                if op == "and": lines.append(f"execute if score #b1 rv_temp matches 1 if score #b2 rv_temp matches 1 run scoreboard players operation #res rv_temp += #p_{i} rv_const")
                elif op == "or":
                    lines.append(f"execute if score #b1 rv_temp matches 1 run scoreboard players operation #res rv_temp += #p_{i} rv_const")
                    lines.append(f"execute unless score #b1 rv_temp matches 1 if score #b2 rv_temp matches 1 run scoreboard players operation #res rv_temp += #p_{i} rv_const")
                elif op == "xor": lines.append(f"execute unless score #b1 rv_temp = #b2 rv_temp run scoreboard players operation #res rv_temp += #p_{i} rv_const")
                lines.append("scoreboard players operation #t1 rv_temp /= #two rv_const")
                lines.append("scoreboard players operation #t2 rv_temp /= #two rv_const")
            lines.extend(["scoreboard players set #s1 rv_temp 0", "scoreboard players set #s2 rv_temp 0", "execute if score #op1 rv_temp matches ..-1 run scoreboard players set #s1 rv_temp 1", "execute if score #op2 rv_temp matches ..-1 run scoreboard players set #s2 rv_temp 1"])
            if op == "and": lines.append("execute if score #s1 rv_temp matches 1 if score #s2 rv_temp matches 1 run scoreboard players operation #res rv_temp -= #min_int rv_const")
            elif op == "or":
                lines.append("execute if score #s1 rv_temp matches 1 run scoreboard players operation #res rv_temp -= #min_int rv_const")
                lines.append("execute unless score #s1 rv_temp matches 1 if score #s2 rv_temp matches 1 run scoreboard players operation #res rv_temp -= #min_int rv_const")
            elif op == "xor": lines.append("execute unless score #s1 rv_temp = #s2 rv_temp run scoreboard players operation #res rv_temp -= #min_int rv_const")
            with open(os.path.join(self.output_dir, "lib", f"{op}.mcfunction"), 'w') as f: f.write("\n".join(lines))

    def gen_shifts(self):
        for op in ["sll", "srl", "sra"]:
            lines = ["scoreboard players operation #res rv_temp = #op1 rv_temp", "scoreboard players operation #amt rv_temp = #op2 rv_temp", "scoreboard players operation #amt rv_temp %= #thirty_two rv_const"]
            for i in range(5):
                amt = 1 << i
                lines.append("scoreboard players operation #bit rv_temp = #amt rv_temp")
                lines.append("scoreboard players operation #bit rv_temp %= #two rv_const")
                if op == "sll": lines.append(f"execute if score #bit rv_temp matches 1 run scoreboard players operation #res rv_temp *= #p_{amt} rv_const")
                elif op == "srl":
                    lines.append(f"execute if score #bit rv_temp matches 1 if score #res rv_temp matches 0.. run scoreboard players operation #res rv_temp /= #p_{amt} rv_const")
                    lines.append(f"execute if score #bit rv_temp matches 1 if score #res rv_temp matches ..-1 run function {self.namespace}:lib/srl_{amt}_neg")
                elif op == "sra": lines.append(f"execute if score #bit rv_temp matches 1 run function {self.namespace}:lib/sra_{amt}")
                lines.append("scoreboard players operation #amt rv_temp /= #two rv_const")
            with open(os.path.join(self.output_dir, "lib", f"{op}.mcfunction"), 'w') as f: f.write("\n".join(lines))
            if op == "srl":
                for i in range(5):
                    amt = 1 << i
                    with open(os.path.join(self.output_dir, "lib", f"srl_{amt}_neg.mcfunction"), 'w') as f: f.write(f"scoreboard players operation #res rv_temp -= #min_int rv_const\nscoreboard players operation #res rv_temp /= #p_{amt} rv_const\nscoreboard players operation #res rv_temp += #p_{31-amt} rv_const\n")
            elif op == "sra":
                for i in range(5):
                    amt = 1 << i
                    with open(os.path.join(self.output_dir, "lib", f"sra_{amt}.mcfunction"), 'w') as f:
                        for _ in range(amt):
                            f.write("scoreboard players operation #old_res rv_temp = #res rv_temp\n")
                            f.write("scoreboard players operation #rem rv_temp = #res rv_temp\n")
                            f.write("scoreboard players operation #rem rv_temp %= #two rv_const\n")
                            f.write("scoreboard players operation #res rv_temp /= #two rv_const\n")
                            f.write("execute if score #old_res rv_temp matches ..-1 if score #rem rv_temp matches -1 run scoreboard players remove #res rv_temp 1\n")

    def gen_mem(self):
        with open(os.path.join(self.output_dir, "mem", "init.mcfunction"), 'w') as f:
            f.write(f"data modify storage {self.namespace}:ram data set value [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]\n")
            # 16 * 2^18 = 4,194,304 words (16MB)
            for _ in range(18):
                f.write(f"data modify storage {self.namespace}:ram data append from storage {self.namespace}:ram data[]\n")
            
            f.write(f"data modify storage {self.namespace}:safe_ram data set value [0,0,0,0,0,0,0,0]\n")
            for _ in range(16):
                f.write(f"data modify storage {self.namespace}:safe_ram data append from storage {self.namespace}:safe_ram data[]\n")
        
        def gen_u_div(f, n):
            f.write(f"execute if score #w rv_temp matches ..-1 run scoreboard players operation #w rv_temp -= #min_int rv_const\n")
            f.write(f"scoreboard players operation #w rv_temp /= #p_{n} rv_const\n")
            f.write(f"execute if score #w rv_temp matches ..-1 run scoreboard players operation #w rv_temp += #p_{31-n} rv_const\n")

        with open(os.path.join(self.output_dir, "mem", "read_lb.mcfunction"), 'w') as f:
            f.write(f"$execute store result score #w rv_temp run data get storage {self.namespace}:ram data[$(addr)]\n")
            f.write("scoreboard players set #shift rv_temp 0\n")
            f.write("execute if score #off rv_temp matches 1 run scoreboard players set #shift rv_temp 8\n")
            f.write("execute if score #off rv_temp matches 2 run scoreboard players set #shift rv_temp 16\n")
            f.write("execute if score #off rv_temp matches 3 run scoreboard players set #shift rv_temp 24\n")
            f.write("execute if score #off rv_temp matches -3 run scoreboard players set #shift rv_temp 8\n")
            f.write("execute if score #off rv_temp matches -2 run scoreboard players set #shift rv_temp 16\n")
            f.write("execute if score #off rv_temp matches -1 run scoreboard players set #shift rv_temp 24\n")
            
            f.write("execute unless score #off rv_temp matches 0 run function %s:mem/u_div\n" % self.namespace)
            f.write("scoreboard players operation #w rv_temp %= #p_8 rv_const\nexecute if score #w rv_temp matches ..-1 run scoreboard players operation #w rv_temp += #p_8 rv_const\nexecute if score #w rv_temp matches 128..255 run scoreboard players remove #w rv_temp 256\nscoreboard players operation #res rv_temp = #w rv_temp\n")
        
        with open(os.path.join(self.output_dir, "mem", "u_div.mcfunction"), 'w') as f:
            f.write("execute if score #w rv_temp matches ..-1 run scoreboard players set #is_neg rv_temp 1\n")
            f.write("execute unless score #w rv_temp matches ..-1 run scoreboard players set #is_neg rv_temp 0\n")
            f.write("execute if score #is_neg rv_temp matches 1 run scoreboard players operation #w rv_temp -= #min_int rv_const\n")
            
            f.write("execute if score #shift rv_temp matches 8 run scoreboard players operation #w rv_temp /= #p_8 rv_const\n")
            f.write("execute if score #shift rv_temp matches 16 run scoreboard players operation #w rv_temp /= #p_16 rv_const\n")
            f.write("execute if score #shift rv_temp matches 24 run scoreboard players operation #w rv_temp /= #p_24 rv_const\n")
            
            f.write("execute if score #is_neg rv_temp matches 1 if score #shift rv_temp matches 8 run scoreboard players operation #w rv_temp += #p_23 rv_const\n")
            f.write("execute if score #is_neg rv_temp matches 1 if score #shift rv_temp matches 16 run scoreboard players operation #w rv_temp += #p_15 rv_const\n")
            f.write("execute if score #is_neg rv_temp matches 1 if score #shift rv_temp matches 24 run scoreboard players operation #w rv_temp += #p_7 rv_const\n")

        with open(os.path.join(self.output_dir, "mem", "read_lbu.mcfunction"), 'w') as f:
            f.write(f"$execute store result score #w rv_temp run data get storage {self.namespace}:ram data[$(addr)]\n")
            f.write("scoreboard players set #shift rv_temp 0\n")
            f.write("execute if score #off rv_temp matches 1 run scoreboard players set #shift rv_temp 8\n")
            f.write("execute if score #off rv_temp matches 2 run scoreboard players set #shift rv_temp 16\n")
            f.write("execute if score #off rv_temp matches 3 run scoreboard players set #shift rv_temp 24\n")
            f.write("execute if score #off rv_temp matches -3 run scoreboard players set #shift rv_temp 8\n")
            f.write("execute if score #off rv_temp matches -2 run scoreboard players set #shift rv_temp 16\n")
            f.write("execute if score #off rv_temp matches -1 run scoreboard players set #shift rv_temp 24\n")
            f.write("execute unless score #off rv_temp matches 0 run function %s:mem/u_div\n" % self.namespace)
            f.write("scoreboard players operation #w rv_temp %= #p_8 rv_const\nexecute if score #w rv_temp matches ..-1 run scoreboard players operation #w rv_temp += #p_8 rv_const\nscoreboard players operation #res rv_temp = #w rv_temp\n")
        
        with open(os.path.join(self.output_dir, "mem", "read_lh.mcfunction"), 'w') as f:
            f.write(f"$execute store result score #w rv_temp run data get storage {self.namespace}:ram data[$(addr)]\n")
            f.write("scoreboard players set #shift rv_temp 0\n")
            f.write("execute if score #off rv_temp matches 2 run scoreboard players set #shift rv_temp 16\n")
            f.write("execute if score #off rv_temp matches -2 run scoreboard players set #shift rv_temp 16\n")
            f.write("execute unless score #off rv_temp matches 0 run function %s:mem/u_div\n" % self.namespace)
            f.write("scoreboard players operation #w rv_temp %= #p_16 rv_const\nexecute if score #w rv_temp matches ..-1 run scoreboard players operation #w rv_temp += #p_16 rv_const\nexecute if score #w rv_temp matches 32768..65535 run scoreboard players remove #w rv_temp 65536\nscoreboard players operation #res rv_temp = #w rv_temp\n")
        
        with open(os.path.join(self.output_dir, "mem", "read_lhu.mcfunction"), 'w') as f:
            f.write(f"$execute store result score #w rv_temp run data get storage {self.namespace}:ram data[$(addr)]\n")
            f.write("scoreboard players set #shift rv_temp 0\n")
            f.write("execute if score #off rv_temp matches 2 run scoreboard players set #shift rv_temp 16\n")
            f.write("execute if score #off rv_temp matches -2 run scoreboard players set #shift rv_temp 16\n")
            f.write("execute unless score #off rv_temp matches 0 run function %s:mem/u_div\n" % self.namespace)
            f.write("scoreboard players operation #w rv_temp %= #p_16 rv_const\nexecute if score #w rv_temp matches ..-1 run scoreboard players operation #w rv_temp += #p_16 rv_const\nscoreboard players operation #res rv_temp = #w rv_temp\n")
        with open(os.path.join(self.output_dir, "mem", "read_lw.mcfunction"), 'w') as f:
             f.write(f"$execute store result score #res rv_temp run data get storage {self.namespace}:ram data[$(addr)]\n")
        with open(os.path.join(self.output_dir, "mem", "write_sw.mcfunction"), 'w') as f: f.write(f"$data modify storage {self.namespace}:ram data[$(addr)] set from storage {self.namespace}:io val\n")
        with open(os.path.join(self.output_dir, "mem", "write_sb.mcfunction"), 'w') as f:
            f.write(f"$execute store result score #old rv_temp run data get storage {self.namespace}:ram data[$(addr)]\n")
            f.write("scoreboard players operation #w rv_temp = #old rv_temp\n")
            f.write("scoreboard players set #shift rv_temp 0\n")
            f.write("execute if score #off rv_temp matches 1 run scoreboard players set #shift rv_temp 8\n")
            f.write("execute if score #off rv_temp matches 2 run scoreboard players set #shift rv_temp 16\n")
            f.write("execute if score #off rv_temp matches 3 run scoreboard players set #shift rv_temp 24\n")
            f.write("execute if score #off rv_temp matches -3 run scoreboard players set #shift rv_temp 8\n")
            f.write("execute if score #off rv_temp matches -2 run scoreboard players set #shift rv_temp 16\n")
            f.write("execute if score #off rv_temp matches -1 run scoreboard players set #shift rv_temp 24\n")
            f.write("execute unless score #off rv_temp matches 0 run function %s:mem/u_div\n" % self.namespace)
            f.write("scoreboard players operation #byte rv_temp = #w rv_temp\n")
            f.write("scoreboard players operation #byte rv_temp %= #p_8 rv_const\nexecute if score #byte rv_temp matches ..-1 run scoreboard players operation #byte rv_temp += #p_8 rv_const\n")
            f.write("scoreboard players set #mul rv_const 1\nexecute if score #off rv_temp matches 1 run scoreboard players operation #mul rv_const = #p_8 rv_const\nexecute if score #off rv_temp matches 2 run scoreboard players operation #mul rv_const = #p_16 rv_const\nexecute if score #off rv_temp matches 3 run scoreboard players operation #mul rv_const = #p_24 rv_const\n")
            f.write("execute if score #off rv_temp matches -3 run scoreboard players operation #mul rv_const = #p_8 rv_const\nexecute if score #off rv_temp matches -2 run scoreboard players operation #mul rv_const = #p_16 rv_const\nexecute if score #off rv_temp matches -1 run scoreboard players operation #mul rv_const = #p_24 rv_const\n")
            f.write(f"scoreboard players operation #byte rv_temp *= #mul rv_const\nscoreboard players operation #old rv_temp -= #byte rv_temp\nexecute store result score #new rv_temp run data get storage {self.namespace}:io val\n")
            f.write("scoreboard players operation #new rv_temp %= #p_8 rv_const\nexecute if score #new rv_temp matches ..-1 run scoreboard players operation #new rv_temp += #p_8 rv_const\nscoreboard players operation #new rv_temp *= #mul rv_const\n")
            f.write(f"scoreboard players operation #old rv_temp += #new rv_temp\nexecute store result storage {self.namespace}:io val int 1 run scoreboard players get #old rv_temp\n$data modify storage {self.namespace}:ram data[$(addr)] set from storage {self.namespace}:io val\n")
        
        with open(os.path.join(self.output_dir, "mem", "write_sh.mcfunction"), 'w') as f:
            f.write(f"$execute store result score #old rv_temp run data get storage {self.namespace}:ram data[$(addr)]\n")
            f.write("scoreboard players operation #w rv_temp = #old rv_temp\n")
            f.write("scoreboard players set #shift rv_temp 0\n")
            f.write("execute if score #off rv_temp matches 2 run scoreboard players set #shift rv_temp 16\n")
            f.write("execute if score #off rv_temp matches -2 run scoreboard players set #shift rv_temp 16\n")
            f.write("execute unless score #off rv_temp matches 0 run function %s:mem/u_div\n" % self.namespace)
            f.write("scoreboard players operation #byte rv_temp = #w rv_temp\n")
            f.write("scoreboard players operation #byte rv_temp %= #p_16 rv_const\nexecute if score #byte rv_temp matches ..-1 run scoreboard players operation #byte rv_temp += #p_16 rv_const\n")
            f.write("scoreboard players set #mul rv_const 1\nexecute if score #off rv_temp matches 2 run scoreboard players operation #mul rv_const = #p_16 rv_const\n")
            f.write("execute if score #off rv_temp matches -2 run scoreboard players operation #mul rv_const = #p_16 rv_const\n")
            f.write(f"scoreboard players operation #byte rv_temp *= #mul rv_const\nscoreboard players operation #old rv_temp -= #byte rv_temp\nexecute store result score #new rv_temp run data get storage {self.namespace}:io val\n")
            f.write("scoreboard players operation #new rv_temp %= #p_16 rv_const\nexecute if score #new rv_temp matches ..-1 run scoreboard players operation #new rv_temp += #p_16 rv_const\nscoreboard players operation #new rv_temp *= #mul rv_const\n")
            f.write(f"scoreboard players operation #old rv_temp += #new rv_temp\nexecute store result storage {self.namespace}:io val int 1 run scoreboard players get #old rv_temp\n$data modify storage {self.namespace}:ram data[$(addr)] set from storage {self.namespace}:io val\n")

    def gen_ecall(self):
        with open(os.path.join(self.output_dir, "ecall", "dispatch.mcfunction"), 'w') as f:
            f.write(f"execute if score x17 rv_reg matches 1 run function {self.namespace}:ecall/print_int\n")
            f.write(f"execute if score x17 rv_reg matches 11 run function {self.namespace}:lib/uart_putc\n")
            f.write(f"execute if score x17 rv_reg matches 12 run function {self.namespace}:ecall/syscon\n")
            f.write(f"execute if score x17 rv_reg matches 13 run function {self.namespace}:ecall/load_data\n")
            f.write(f"execute if score x17 rv_reg matches 14 run function {self.namespace}:ecall/exec_cmd\n")
            f.write(f"execute if score x17 rv_reg matches 93 run function {self.namespace}:debug/dump_inline\n")
            f.write(f"execute if score x17 rv_reg matches 10 run scoreboard players set #halt rv_temp 1\n")
        
        with open(os.path.join(self.output_dir, "ecall", "load_data.mcfunction"), 'w') as f:
            f.write("scoreboard players operation #addr rv_temp = x10 rv_reg\n")
            f.write("scoreboard players operation #addr rv_temp /= #four rv_const\n")
            f.write(f"execute store result storage {self.namespace}:io dest_idx int 1 run scoreboard players get #addr rv_temp\n")
            f.write(f'data modify storage {self.namespace}:io path set value "{self.namespace}:data"\n')
            f.write(f'data modify storage {self.namespace}:io nbt set value "Data"\n')
            f.write(f"function {self.namespace}:mem/copy_storage_to_ram with storage {self.namespace}:io\n")

        with open(os.path.join(self.output_dir, "ecall", "syscon.mcfunction"), 'w') as f:
            f.write('execute if score x10 rv_reg matches 21845 run tellraw @a [{"text":"[MC-RVVM] Powering Off.","color":"red"}]\n')
            f.write("execute if score x10 rv_reg matches 21845 run scoreboard players set #halt rv_temp 1\n")
        with open(os.path.join(self.output_dir, "ecall", "print_int.mcfunction"), 'w') as f:
            f.write("tellraw @a [{\"score\":{\"name\":\"x10\",\"objective\":\"rv_reg\"},\"color\":\"green\"}]\n")

    def gen_debug(self):
        with open(os.path.join(self.output_dir, "debug", "dump_inline.mcfunction"), 'w') as f:
            f.write(f"tellraw @a [{{\"text\":\"PC:\",\"color\":\"gray\"}},{{\"score\":{{\"name\":\"pc\",\"objective\":\"{self.namespace}_pc\"}}}},{{\"text\":\" | \",\"color\":\"dark_gray\"}}")
            for i in [1, 2, 8, 10, 11, 12, 13, 14, 15, 17]:
                f.write(f",{{\"text\":\"x{i}:\",\"color\":\"aqua\"}},{{\"score\":{{\"name\":\"x{i}\",\"objective\":\"rv_reg\"}}}},{{\"text\":\" \",\"color\":\"white\"}}")
            f.write("]\n")