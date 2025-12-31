import os

class LibGenerator:
    def __init__(self, output_dir, namespace="rv32"):
        self.output_dir = output_dir
        self.namespace = namespace

    def generate(self):
        for d in ["lib", "mem", "ecall", "debug"]:
            os.makedirs(os.path.join(self.output_dir, d), exist_ok=True)
        self.gen_bitwise()
        self.gen_shifts()
        self.gen_math()
        self.gen_mem()
        self.gen_uart()
        self.gen_data_loader()
        self.gen_ecall()
        self.gen_debug()

    def gen_data_loader(self):
        with open(os.path.join(self.output_dir, "mem", "load_data.mcfunction"), 'w') as f:
            f.write("# a0: dest_addr, a1: storage_path_idx, a2: nbt_path_idx\n")
            f.write(f"$data modify storage {self.namespace}:ram data[$(dest_idx)] set from storage $(path) $(nbt)\n")


    def gen_ascii_map(self):
        def generate_tree(chars, path):
            os.makedirs(os.path.join(self.output_dir, "lib", "ascii", os.path.dirname(path)), exist_ok=True)
            with open(os.path.join(self.output_dir, "lib", "ascii", f"{path}.mcfunction"), 'w') as f:
                if len(chars) == 1:
                    c, val = chars[0]
                    escaped = c.replace('\\', '\\\\').replace('"', '\\"')
                    f.write(f'data modify storage {self.namespace}:uart char set value "{escaped}"\n')
                    return
                mid = len(chars) // 2
                low, high = chars[:mid], chars[mid:]
                f.write(f"execute if score #char rv_temp matches {low[0][1]}..{low[-1][1]} run function {self.namespace}:lib/ascii/{path}_0\n")
                f.write(f"execute if score #char rv_temp matches {high[0][1]}..{high[-1][1]} run function {self.namespace}:lib/ascii/{path}_1\n")
                generate_tree(low, f"{path}_0")
                generate_tree(high, f"{path}_1")
        all_chars = [(chr(i), i) for i in range(32, 127)]
        all_chars.insert(0, (" ", 10))
        all_chars.sort(key=lambda x: x[1])
        generate_tree(all_chars, "map")

    def gen_uart(self):
        self.gen_ascii_map()
        with open(os.path.join(self.output_dir, "lib", "uart_putc.mcfunction"), 'w') as f:
            f.write("scoreboard players operation #char rv_temp = x10 rv_reg\n")
            f.write(f"execute if score #char rv_temp matches 10 run function {self.namespace}:lib/uart_flush\n")
            f.write(f"execute unless score #char rv_temp matches 10 run function {self.namespace}:lib/ascii/map\n")
            f.write(f"execute unless score #char rv_temp matches 10 run data modify storage {self.namespace}:uart buffer append from storage {self.namespace}:uart char\n")
        
        with open(os.path.join(self.output_dir, "lib", "uart_flush.mcfunction"), 'w') as f:
            f.write(f"execute if data storage {self.namespace}:uart buffer[0] run function {self.namespace}:lib/uart_print with storage {self.namespace}:uart\n")
            f.write(f"data modify storage {self.namespace}:uart buffer set value []\n")

        with open(os.path.join(self.output_dir, "lib", "uart_print.mcfunction"), 'w') as f:
            f.write(f'$tellraw @a $(buffer)\n')

    def gen_math(self):
        with open(os.path.join(self.output_dir, "lib", "mul.mcfunction"), 'w') as f:
            f.write("scoreboard players set #res rv_temp 0\n")
            f.write("scoreboard players operation #t1 rv_temp = #op1 rv_temp\n")
            f.write("scoreboard players operation #t2 rv_temp = #op2 rv_temp\n")
            for i in range(32):
                f.write(f"scoreboard players operation #bit rv_temp = #t2 rv_temp\n")
                f.write(f"scoreboard players operation #bit rv_temp %= #two rv_const\n")
                f.write(f"execute unless score #bit rv_temp matches 0 run scoreboard players operation #res rv_temp += #t1 rv_temp\n")
                f.write(f"scoreboard players operation #t1 rv_temp *= #two rv_const\n")
                f.write(f"scoreboard players operation #t2 rv_temp /= #two rv_const\n")
        for op in ["mulh", "mulhu", "mulhsu"]:
            with open(os.path.join(self.output_dir, "lib", f"{op}.mcfunction"), 'w') as f:
                f.write("scoreboard players set #rh rv_temp 0\nscoreboard players set #rl rv_temp 0\n")
                f.write("scoreboard players operation #u1l rv_temp = #op1 rv_temp\nscoreboard players set #u1h rv_temp 0\n")
                f.write("scoreboard players operation #u2l rv_temp = #op2 rv_temp\nscoreboard players set #u2h rv_temp 0\n")
                if op == "mulh":
                    f.write("execute if score #op1 rv_temp matches ..-1 run scoreboard players set #u1h rv_temp -1\n")
                    f.write("execute if score #op2 rv_temp matches ..-1 run scoreboard players set #u2h rv_temp -1\n")
                elif op == "mulhsu":
                    f.write("execute if score #op1 rv_temp matches ..-1 run scoreboard players set #u1h rv_temp -1\n")
                for i in range(32):
                    f.write(f"scoreboard players operation #bit rv_temp = #u2l rv_temp\n")
                    f.write(f"scoreboard players operation #bit rv_temp %= #two rv_const\n")
                    f.write(f"execute unless score #bit rv_temp matches 0 run function {self.namespace}:lib/add64_u1\n")
                    f.write(f"function {self.namespace}:lib/shl64_u1\n")
                    f.write(f"scoreboard players operation #op1 rv_temp = #u2l rv_temp\n")
                    f.write(f"scoreboard players set #op2 rv_temp 1\n")
                    f.write(f"function {self.namespace}:lib/srl\n")
                    f.write(f"scoreboard players operation #u2l rv_temp = #res rv_temp\n")
                f.write("scoreboard players operation #res rv_temp = #rh rv_temp\n")
        with open(os.path.join(self.output_dir, "lib", "add64_u1.mcfunction"), 'w') as f:
            f.write("scoreboard players operation #rh rv_temp += #u1h rv_temp\n")
            f.write("scoreboard players operation #old_rl rv_temp = #rl rv_temp\n")
            f.write("scoreboard players operation #rl rv_temp += #u1l rv_temp\n")
            f.write("scoreboard players operation #c1 rv_temp = #rl rv_temp\n")
            f.write("scoreboard players operation #c1 rv_temp -= #min_int rv_const\n")
            f.write("scoreboard players operation #c2 rv_temp = #old_rl rv_temp\n")
            f.write("scoreboard players operation #c2 rv_temp -= #min_int rv_const\n")
            f.write("execute if score #c1 rv_temp < #c2 rv_temp run scoreboard players add #rh rv_temp 1\n")
        with open(os.path.join(self.output_dir, "lib", "shl64_u1.mcfunction"), 'w') as f:
            f.write("scoreboard players operation #u1h rv_temp *= #two rv_const\n")
            f.write("execute if score #u1l rv_temp matches ..-1 run scoreboard players add #u1h rv_temp 1\n")
            f.write("scoreboard players operation #u1l rv_temp *= #two rv_const\n")
        with open(os.path.join(self.output_dir, "lib", "divu_logic.mcfunction"), 'w') as f:
            f.write("scoreboard players set #q rv_temp 0\nscoreboard players set #r rv_temp 0\n")
            f.write("execute if score #u2 rv_temp matches 0 run scoreboard players set #q rv_temp -1\n")
            f.write("execute if score #u2 rv_temp matches 0 run scoreboard players operation #r rv_temp = #u1 rv_temp\n")
            f.write("execute if score #u2 rv_temp matches 0 run return 0\n")
            f.write("scoreboard players operation #tu2 rv_temp = #u2 rv_temp\n")
            f.write("scoreboard players operation #tu2 rv_temp -= #min_int rv_const\n")
            for i in range(31, -1, -1):
                f.write(f"scoreboard players operation #r rv_temp *= #two rv_const\n")
                if i == 31:
                    f.write("scoreboard players set #bit rv_temp 0\n")
                    f.write("execute if score #u1 rv_temp matches ..-1 run scoreboard players set #bit rv_temp 1\n")
                else:
                    f.write(f"scoreboard players operation #bit rv_temp = #u1 rv_temp\n")
                    if i > 0: f.write(f"scoreboard players operation #bit rv_temp /= #p_{i} rv_const\n")
                    f.write(f"scoreboard players operation #bit rv_temp %= #two rv_const\n")
                    f.write(f"execute if score #bit rv_temp matches ..-1 run scoreboard players add #bit rv_temp 2\n")
                f.write(f"scoreboard players operation #r rv_temp += #bit rv_temp\n")
                f.write("scoreboard players operation #tr rv_temp = #r rv_temp\n")
                f.write("scoreboard players operation #tr rv_temp -= #min_int rv_const\n")
                f.write("execute if score #tr rv_temp >= #tu2 rv_temp run scoreboard players operation #r rv_temp -= #u2 rv_temp\n")
                if i > 0: f.write(f"execute if score #tr rv_temp >= #tu2 rv_temp run scoreboard players operation #q rv_temp += #p_{i} rv_const\n")
                else: f.write(f"execute if score #tr rv_temp >= #tu2 rv_temp run scoreboard players add #q rv_temp 1\n")
        for op in ["divu", "remu", "div", "rem"]:
            with open(os.path.join(self.output_dir, "lib", f"{op}.mcfunction"), 'w') as f:
                if op == "divu":
                    f.write("scoreboard players operation #u1 rv_temp = #op1 rv_temp\n")
                    f.write("scoreboard players operation #u2 rv_temp = #op2 rv_temp\n")
                    f.write(f"function {self.namespace}:lib/divu_logic\n")
                    f.write("scoreboard players operation #res rv_temp = #q rv_temp\n")
                elif op == "remu":
                    f.write("scoreboard players operation #u1 rv_temp = #op1 rv_temp\n")
                    f.write("scoreboard players operation #u2 rv_temp = #op2 rv_temp\n")
                    f.write(f"function {self.namespace}:lib/divu_logic\n")
                    f.write("scoreboard players operation #res rv_temp = #r rv_temp\n")
                elif op in ["div", "rem"]:
                    f.write("scoreboard players set #s1 rv_temp 0\nscoreboard players set #s2 rv_temp 0\n")
                    f.write("execute if score #op1 rv_temp matches ..-1 run scoreboard players set #s1 rv_temp 1\n")
                    f.write("execute if score #op2 rv_temp matches ..-1 run scoreboard players set #s2 rv_temp 1\n")
                    f.write("scoreboard players operation #u1 rv_temp = #op1 rv_temp\n")
                    f.write("execute if score #s1 rv_temp matches 1 run scoreboard players set #zero rv_temp 0\n")
                    f.write("execute if score #s1 rv_temp matches 1 run scoreboard players operation #u1 rv_temp = #zero rv_temp\n")
                    f.write("execute if score #s1 rv_temp matches 1 run scoreboard players operation #u1 rv_temp -= #op1 rv_temp\n")
                    f.write("scoreboard players operation #u2 rv_temp = #op2 rv_temp\n")
                    f.write("execute if score #s2 rv_temp matches 1 run scoreboard players set #zero rv_temp 0\n")
                    f.write("execute if score #s2 rv_temp matches 1 run scoreboard players operation #u2 rv_temp = #zero rv_temp\n")
                    f.write("execute if score #s2 rv_temp matches 1 run scoreboard players operation #u2 rv_temp -= #op2 rv_temp\n")
                    f.write(f"function {self.namespace}:lib/divu_logic\n")
                    if op == "div":
                        f.write("scoreboard players operation #res rv_temp = #q rv_temp\n")
                        f.write("execute unless score #s1 rv_temp = #s2 rv_temp if score #q rv_temp matches 1.. run scoreboard players set #zero rv_temp 0\n")
                        f.write("execute unless score #s1 rv_temp = #s2 rv_temp if score #q rv_temp matches 1.. run scoreboard players operation #res rv_temp = #zero rv_temp\n")
                        f.write("execute unless score #s1 rv_temp = #s2 rv_temp if score #q rv_temp matches 1.. run scoreboard players operation #res rv_temp -= #q rv_temp\n")
                    else:
                        f.write("scoreboard players operation #res rv_temp = #r rv_temp\n")
                        f.write("execute if score #s1 rv_temp matches 1 if score #r rv_temp matches 1.. run scoreboard players set #zero rv_temp 0\n")
                        f.write("execute if score #s1 rv_temp matches 1 if score #r rv_temp matches 1.. run scoreboard players operation #res rv_temp = #zero rv_temp\n")
                        f.write("execute if score #s1 rv_temp matches 1 if score #r rv_temp matches 1.. run scoreboard players operation #res rv_temp -= #r rv_temp\n")

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
            f.write(f"data modify storage {self.namespace}:ram data set value [0]\n")
            for _ in range(18):
                f.write(f"data modify storage {self.namespace}:ram data append from storage {self.namespace}:ram data[]\n")
            
            f.write(f"data modify storage {self.namespace}:safe_ram data set value [0]\n")
            for _ in range(19):
                f.write(f"data modify storage {self.namespace}:safe_ram data append from storage {self.namespace}:safe_ram data[]\n")
        with open(os.path.join(self.output_dir, "mem", "read_lb.mcfunction"), 'w') as f:
            f.write(f"$execute store result score #w rv_temp run data get storage {self.namespace}:ram data[$(addr)]\n")
            f.write("execute if score #off rv_temp matches 1 run scoreboard players operation #w rv_temp /= #p_8 rv_const\nexecute if score #off rv_temp matches 2 run scoreboard players operation #w rv_temp /= #p_16 rv_const\nexecute if score #off rv_temp matches 3 run scoreboard players operation #w rv_temp /= #p_24 rv_const\n")
            f.write("scoreboard players operation #w rv_temp %= #p_8 rv_const\nexecute if score #w rv_temp matches ..-1 run scoreboard players operation #w rv_temp += #p_8 rv_const\nexecute if score #w rv_temp matches 128..255 run scoreboard players remove #w rv_temp 256\nscoreboard players operation #res rv_temp = #w rv_temp\n")
        with open(os.path.join(self.output_dir, "mem", "read_lbu.mcfunction"), 'w') as f:
            f.write(f"$execute store result score #w rv_temp run data get storage {self.namespace}:ram data[$(addr)]\n")
            f.write("execute if score #off rv_temp matches 1 run scoreboard players operation #w rv_temp /= #p_8 rv_const\nexecute if score #off rv_temp matches 2 run scoreboard players operation #w rv_temp /= #p_16 rv_const\nexecute if score #off rv_temp matches 3 run scoreboard players operation #w rv_temp /= #p_24 rv_const\n")
            f.write("scoreboard players operation #w rv_temp %= #p_8 rv_const\nexecute if score #w rv_temp matches ..-1 run scoreboard players operation #w rv_temp += #p_8 rv_const\nscoreboard players operation #res rv_temp = #w rv_temp\n")
        with open(os.path.join(self.output_dir, "mem", "read_lh.mcfunction"), 'w') as f:
            f.write(f"$execute store result score #w rv_temp run data get storage {self.namespace}:ram data[$(addr)]\n")
            f.write("execute if score #off rv_temp matches 2 run scoreboard players operation #w rv_temp /= #p_16 rv_const\n")
            f.write("scoreboard players operation #w rv_temp %= #p_16 rv_const\nexecute if score #w rv_temp matches ..-1 run scoreboard players operation #w rv_temp += #p_16 rv_const\nexecute if score #w rv_temp matches 32768..65535 run scoreboard players remove #w rv_temp 65536\nscoreboard players operation #res rv_temp = #w rv_temp\n")
        with open(os.path.join(self.output_dir, "mem", "read_lhu.mcfunction"), 'w') as f:
            f.write(f"$execute store result score #w rv_temp run data get storage {self.namespace}:ram data[$(addr)]\n")
            f.write("execute if score #off rv_temp matches 2 run scoreboard players operation #w rv_temp /= #p_16 rv_const\n")
            f.write("scoreboard players operation #w rv_temp %= #p_16 rv_const\nexecute if score #w rv_temp matches ..-1 run scoreboard players operation #w rv_temp += #p_16 rv_const\nscoreboard players operation #res rv_temp = #w rv_temp\n")
        with open(os.path.join(self.output_dir, "mem", "read_lw.mcfunction"), 'w') as f:
             f.write(f"$execute store result score #res rv_temp run data get storage {self.namespace}:ram data[$(addr)]\n")
        with open(os.path.join(self.output_dir, "mem", "write_sw.mcfunction"), 'w') as f: f.write(f"$data modify storage {self.namespace}:ram data[$(addr)] set from storage {self.namespace}:io val\n")
        with open(os.path.join(self.output_dir, "mem", "write_sb.mcfunction"), 'w') as f:
            f.write(f"$execute store result score #old rv_temp run data get storage {self.namespace}:ram data[$(addr)]\n")
            f.write("scoreboard players operation #temp rv_temp = #old rv_temp\nexecute if score #off rv_temp matches 1 run scoreboard players operation #temp rv_temp /= #p_8 rv_const\nexecute if score #off rv_temp matches 2 run scoreboard players operation #temp rv_temp /= #p_16 rv_const\nexecute if score #off rv_temp matches 3 run scoreboard players operation #temp rv_temp /= #p_24 rv_const\n")
            f.write("scoreboard players operation #byte rv_temp = #temp rv_temp\nscoreboard players operation #byte rv_temp %= #p_8 rv_const\nexecute if score #byte rv_temp matches ..-1 run scoreboard players operation #byte rv_temp += #p_8 rv_const\n")
            f.write("scoreboard players set #mul rv_const 1\nexecute if score #off rv_temp matches 1 run scoreboard players operation #mul rv_const = #p_8 rv_const\nexecute if score #off rv_temp matches 2 run scoreboard players operation #mul rv_const = #p_16 rv_const\nexecute if score #off rv_temp matches 3 run scoreboard players operation #mul rv_const = #p_24 rv_const\n")
            f.write(f"scoreboard players operation #byte rv_temp *= #mul rv_const\nscoreboard players operation #old rv_temp -= #byte rv_temp\nexecute store result score #new rv_temp run data get storage {self.namespace}:io val\n")
            f.write("scoreboard players operation #new rv_temp %= #p_8 rv_const\nexecute if score #new rv_temp matches ..-1 run scoreboard players operation #new rv_temp += #p_8 rv_const\nscoreboard players operation #new rv_temp *= #mul rv_const\n")
            f.write(f"scoreboard players operation #old rv_temp += #new rv_temp\nexecute store result storage {self.namespace}:io val int 1 run scoreboard players get #old rv_temp\n$data modify storage {self.namespace}:ram data[$(addr)] set from storage {self.namespace}:io val\n")
        with open(os.path.join(self.output_dir, "mem", "write_sh.mcfunction"), 'w') as f:
            f.write(f"$execute store result score #old rv_temp run data get storage {self.namespace}:ram data[$(addr)]\n")
            f.write("scoreboard players operation #temp rv_temp = #old rv_temp\nexecute if score #off rv_temp matches 2 run scoreboard players operation #temp rv_temp /= #p_16 rv_const\n")
            f.write("scoreboard players operation #byte rv_temp = #temp rv_temp\nscoreboard players operation #byte rv_temp %= #p_16 rv_const\nexecute if score #byte rv_temp matches ..-1 run scoreboard players operation #byte rv_temp += #p_16 rv_const\n")
            f.write("scoreboard players set #mul rv_const 1\nexecute if score #off rv_temp matches 2 run scoreboard players operation #mul rv_const = #p_16 rv_const\n")
            f.write(f"scoreboard players operation #byte rv_temp *= #mul rv_const\nscoreboard players operation #old rv_temp -= #byte rv_temp\nexecute store result score #new rv_temp run data get storage {self.namespace}:io val\n")
            f.write("scoreboard players operation #new rv_temp %= #p_16 rv_const\nexecute if score #new rv_temp matches ..-1 run scoreboard players operation #new rv_temp += #p_16 rv_const\nscoreboard players operation #new rv_temp *= #mul rv_const\n")
            f.write(f"scoreboard players operation #old rv_temp += #new rv_temp\nexecute store result storage {self.namespace}:io val int 1 run scoreboard players get #old rv_temp\n$data modify storage {self.namespace}:ram data[$(addr)] set from storage {self.namespace}:io val\n")
        with open(os.path.join(self.output_dir, "mem", "init.mcfunction"), 'w') as f:
            f.write(f"data modify storage {self.namespace}:ram data set value [0]\n")
            for _ in range(21):
                f.write(f"data modify storage {self.namespace}:ram data append from storage {self.namespace}:ram data[]\n")

    def gen_ecall(self):
        with open(os.path.join(self.output_dir, "ecall", "dispatch.mcfunction"), 'w') as f:
            f.write(f"execute if score x17 rv_reg matches 1 run function {self.namespace}:ecall/print_int\n")
            f.write(f"execute if score x17 rv_reg matches 11 run function {self.namespace}:lib/uart_putc\n")
            f.write(f"execute if score x17 rv_reg matches 12 run function {self.namespace}:ecall/syscon\n")
            f.write(f"execute if score x17 rv_reg matches 13 run function {self.namespace}:ecall/load_data\n")
            f.write(f"execute if score x17 rv_reg matches 93 run function {self.namespace}:debug/dump_inline\n")
            f.write(f"execute if score x17 rv_reg matches 10 run scoreboard players set #halt rv_temp 1\n")
        
        with open(os.path.join(self.output_dir, "ecall", "load_data.mcfunction"), 'w') as f:
            f.write("scoreboard players operation #addr rv_temp = x10 rv_reg\n")
            f.write("scoreboard players operation #addr rv_temp /= #four rv_const\n")
            f.write(f"execute store result storage {self.namespace}:io dest_idx int 1 run scoreboard players get #addr rv_temp\n")
            f.write(f'data modify storage {self.namespace}:io path set value "{self.namespace}:kernel"\n')
            f.write(f'data modify storage {self.namespace}:io nbt set value "Image"\n')
            f.write(f"function {self.namespace}:mem/load_data with storage {self.namespace}:io\n")
            f.write('tellraw @a [{"text":"[MC-RVVM] Data loaded into RAM.","color":"green"}]\n')

        with open(os.path.join(self.output_dir, "ecall", "syscon.mcfunction"), 'w') as f:
            f.write('execute if score x10 rv_reg matches 21845 run tellraw @a [{"text":"[SYSCON] Powering Off.","color":"red"}]\n')
            f.write("execute if score x10 rv_reg matches 21845 run scoreboard players set #halt rv_temp 1\n")
        with open(os.path.join(self.output_dir, "ecall", "print_int.mcfunction"), 'w') as f:
            f.write("tellraw @a [{\"score\":{\"name\":\"x10\",\"objective\":\"rv_reg\"},\"color\":\"green\"}]\n")

    def gen_debug(self):
        with open(os.path.join(self.output_dir, "debug", "dump_inline.mcfunction"), 'w') as f:
            f.write(f"tellraw @a [{{\"text\":\"PC:\",\"color\":\"gray\"}},{{\"score\":{{\"name\":\"pc\",\"objective\":\"{self.namespace}_pc\"}}}},{{\"text\":\" | \",\"color\":\"dark_gray\"}}")
            for i in [1, 2, 8, 10, 11, 12, 13, 14, 15, 17]:
                f.write(f",{{\"text\":\"x{i}:\",\"color\":\"aqua\"}},{{\"score\":{{\"name\":\"x{i}\",\"objective\":\"rv_reg\"}}}},{{\"text\":\" \",\"color\":\"white\"}}")
            f.write("]\n")