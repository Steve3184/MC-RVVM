class Transpiler:
    def __init__(self, instructions, namespace="rv32"):
        self.instructions = instructions
        self.namespace = namespace
        self.pc_obj = f"{namespace}_pc"

    def convert_instruction(self, instr):
        cmds = []
        reg_obj = "rv_reg"
        pc_obj = self.pc_obj
        temp_obj = "rv_temp"
        const_player = "#const"

        def s32(val):
            val &= 0xFFFFFFFF
            if val >= 0x80000000:
                return val - 0x100000000
            return val

        def target(reg_idx):
            if reg_idx == 0: return None
            return f"x{reg_idx}"

        def source(reg_idx):
            if reg_idx == 0: return "x0"
            return f"x{reg_idx}"

        def safe_add_literal(player, obj, value):
            if value == 0: return []
            s_val = s32(value)
            if s_val > 0:
                return [f"scoreboard players add {player} {obj} {s_val}"]
            else:
                if s_val == -2147483648:
                    return [f"scoreboard players operation {player} {obj} += #min_int rv_const"]
                else:
                    return [f"scoreboard players remove {player} {obj} {abs(s_val)}"]

        if instr.name in ["add", "sub", "addi", "xor", "or", "and", "xori", "ori", "andi", "mul", "mulh", "mulhsu", "mulhu", "div", "divu", "rem", "remu"]:
            rd = target(instr.rd)
            if rd:
                if instr.name == "add":
                    cmds.append(f"scoreboard players operation #op1 {temp_obj} = {source(instr.rs1)} {reg_obj}")
                    cmds.append(f"scoreboard players operation #op1 {temp_obj} += {source(instr.rs2)} {reg_obj}")
                    cmds.append(f"scoreboard players operation {rd} {reg_obj} = #op1 {temp_obj}")
                elif instr.name == "sub":
                    cmds.append(f"scoreboard players operation #op1 {temp_obj} = {source(instr.rs1)} {reg_obj}")
                    cmds.append(f"scoreboard players operation #op1 {temp_obj} -= {source(instr.rs2)} {reg_obj}")
                    cmds.append(f"scoreboard players operation {rd} {reg_obj} = #op1 {temp_obj}")
                elif instr.name == "addi":
                    cmds.append(f"scoreboard players operation {rd} {reg_obj} = {source(instr.rs1)} {reg_obj}")
                    cmds.extend(safe_add_literal(rd, reg_obj, instr.imm))
                elif instr.name in ["xor", "or", "and", "mul", "mulh", "mulhsu", "mulhu", "div", "divu", "rem", "remu"]:
                    cmds.append(f"scoreboard players operation #op1 {temp_obj} = {source(instr.rs1)} {reg_obj}")
                    cmds.append(f"scoreboard players operation #op2 {temp_obj} = {source(instr.rs2)} {reg_obj}")
                    cmds.append(f"function {self.namespace}:lib/{instr.name}")
                    cmds.append(f"scoreboard players operation {rd} {reg_obj} = #res {temp_obj}")
                elif instr.name in ["xori", "ori", "andi"]:
                    cmds.append(f"scoreboard players operation #op1 {temp_obj} = {source(instr.rs1)} {reg_obj}")
                    cmds.append(f"scoreboard players set #op2 {temp_obj} {instr.imm}")
                    cmds.append(f"function {self.namespace}:lib/{instr.name[:-1]}")
                    cmds.append(f"scoreboard players operation {rd} {reg_obj} = #res {temp_obj}")
            cmds.append(f"scoreboard players add pc {pc_obj} 4")

        elif instr.name in ["sll", "srl", "sra", "slli", "srli", "srai"]:
            rd = target(instr.rd)
            if rd:
                cmds.append(f"scoreboard players operation #op1 {temp_obj} = {source(instr.rs1)} {reg_obj}")
                if instr.name.endswith("i"):
                    cmds.append(f"scoreboard players set #op2 {temp_obj} {instr.imm}")
                    lib_name = instr.name[:-1]
                else:
                    cmds.append(f"scoreboard players operation #op2 {temp_obj} = {source(instr.rs2)} {reg_obj}")
                    lib_name = instr.name
                cmds.append(f"function {self.namespace}:lib/{lib_name}")
                cmds.append(f"scoreboard players operation {rd} {reg_obj} = #res {temp_obj}")
            cmds.append(f"scoreboard players add pc {pc_obj} 4")

        elif instr.name in ["slt", "sltu", "slti", "sltiu"]:
            rd = target(instr.rd)
            if rd:
                if instr.name in ["slt", "slti"]:
                    val2 = f"{source(instr.rs2)} {reg_obj}" if instr.name == "slt" else f"#imm {temp_obj}"
                    if instr.name == "slti": cmds.append(f"scoreboard players set #imm {temp_obj} {instr.imm}")
                    cmds.append(f"scoreboard players set #res {temp_obj} 0")
                    cmds.append(f"execute if score {source(instr.rs1)} {reg_obj} < {val2} run scoreboard players set #res {temp_obj} 1")
                    cmds.append(f"scoreboard players operation {rd} {reg_obj} = #res {temp_obj}")
                else:
                    cmds.append(f"scoreboard players operation #u1 {temp_obj} = {source(instr.rs1)} {reg_obj}")
                    cmds.append(f"scoreboard players operation #u1 {temp_obj} -= #min_int rv_const")
                    if instr.name == "sltu":
                        cmds.append(f"scoreboard players operation #u2 {temp_obj} = {source(instr.rs2)} {reg_obj}")
                        cmds.append(f"scoreboard players operation #u2 {temp_obj} -= #min_int rv_const")
                    else:
                        cmds.append(f"scoreboard players set #imm {temp_obj} {instr.imm}")
                        cmds.append(f"scoreboard players operation #u2 {temp_obj} = #imm {temp_obj}")
                        cmds.append(f"scoreboard players operation #u2 {temp_obj} -= #min_int rv_const")
                    cmds.append(f"scoreboard players set #res {temp_obj} 0")
                    cmds.append(f"execute if score #u1 {temp_obj} < #u2 {temp_obj} run scoreboard players set #res {temp_obj} 1")
                    cmds.append(f"scoreboard players operation {rd} {reg_obj} = #res {temp_obj}")
            cmds.append(f"scoreboard players add pc {pc_obj} 4")

        elif instr.name in ["beq", "bne", "blt", "bge", "bltu", "bgeu"]:
            target_addr = s32(instr.address + instr.imm)
            next_addr = s32(instr.address + 4)
            if instr.name in ["bltu", "bgeu"]:
                cmds.append(f"scoreboard players operation #u1 {temp_obj} = {source(instr.rs1)} {reg_obj}")
                cmds.append(f"scoreboard players operation #u1 {temp_obj} -= #min_int rv_const")
                cmds.append(f"scoreboard players operation #u2 {temp_obj} = {source(instr.rs2)} {reg_obj}")
                cmds.append(f"scoreboard players operation #u2 {temp_obj} -= #min_int rv_const")
                op = "<" if instr.name == "bltu" else ">="
                cmds.append(f"execute if score #u1 {temp_obj} {op} #u2 {temp_obj} run scoreboard players set pc {pc_obj} {target_addr}")
                cmds.append(f"execute unless score #u1 {temp_obj} {op} #u2 {temp_obj} run scoreboard players set pc {pc_obj} {next_addr}")
            else:
                op = {"beq":"=","bne":"=","blt":"<","bge":">="}[instr.name]
                exec_type = "unless" if instr.name == "bne" else "if"
                other_type = "if" if instr.name == "bne" else "unless"
                cmds.append(f"execute {exec_type} score {source(instr.rs1)} {reg_obj} {op} {source(instr.rs2)} {reg_obj} run scoreboard players set pc {pc_obj} {target_addr}")
                cmds.append(f"execute {other_type} score {source(instr.rs1)} {reg_obj} {op} {source(instr.rs2)} {reg_obj} run scoreboard players set pc {pc_obj} {next_addr}")

        elif instr.name == "jal":
            rd = target(instr.rd)
            if rd: cmds.append(f"scoreboard players set {rd} {reg_obj} {s32(instr.address + 4)}")
            cmds.append(f"scoreboard players set pc {pc_obj} {s32(instr.address + instr.imm)}")
        elif instr.name == "jalr":
            rd = target(instr.rd)
            if rd: cmds.append(f"scoreboard players set {rd} {reg_obj} {s32(instr.address + 4)}")
            cmds.append(f"scoreboard players operation pc {pc_obj} = {source(instr.rs1)} {reg_obj}")
            cmds.extend(safe_add_literal("pc", pc_obj, instr.imm))
            cmds.append(f"scoreboard players operation pc {pc_obj} /= #two rv_const")
            cmds.append(f"scoreboard players operation pc {pc_obj} *= #two rv_const")

        elif instr.name == "lui":
            rd = target(instr.rd)
            if rd: cmds.append(f"scoreboard players set {rd} {reg_obj} {s32(instr.imm)}")
            cmds.append(f"scoreboard players add pc {pc_obj} 4")
        elif instr.name == "auipc":
            rd = target(instr.rd)
            if rd:
                cmds.append(f"scoreboard players set {rd} {reg_obj} {s32(instr.address + instr.imm)}")
            cmds.append(f"scoreboard players add pc {pc_obj} 4")

        elif instr.name in ["lw", "lh", "lb", "lhu", "lbu", "sw", "sh", "sb"]:
            rd_or_rs2 = target(instr.rd) if instr.name[0] == 'l' else source(instr.rs2)
            cmds.append(f"scoreboard players operation #addr {temp_obj} = {source(instr.rs1)} {reg_obj}")
            cmds.extend(safe_add_literal("#addr", temp_obj, instr.imm))
            cmds.append(f"scoreboard players operation #off {temp_obj} = #addr {temp_obj}")
            cmds.append(f"scoreboard players operation #off {temp_obj} %= #four rv_const")
            cmds.append(f"scoreboard players operation #addr {temp_obj} /= #four rv_const")
            
            cmds.append(f"execute store result storage {self.namespace}:io addr int 1 run scoreboard players get #addr {temp_obj}")
            cmds.append(f"execute store result storage {self.namespace}:io off int 1 run scoreboard players get #off {temp_obj}")
            
            if instr.name[0] == 'l':
                cmds.append(f"function {self.namespace}:mem/read_{instr.name} with storage {self.namespace}:io")
                if rd_or_rs2: cmds.append(f"scoreboard players operation {rd_or_rs2} {reg_obj} = #res {temp_obj}")
            else:
                cmds.append(f"execute store result storage {self.namespace}:io val int 1 run scoreboard players get {rd_or_rs2} {reg_obj}")
                cmds.append(f"function {self.namespace}:mem/write_{instr.name} with storage {self.namespace}:io")
            
            cmds.append(f"scoreboard players add pc {pc_obj} 4")

        elif instr.name in ["lr.w", "sc.w", "amoswap.w", "amoadd.w", "amoxor.w", "amoand.w", "amoor.w", "amomin.w", "amomax.w", "amominu.w", "amomaxu.w"]:
            rd = target(instr.rd)
            rs1 = source(instr.rs1)
            rs2 = source(instr.rs2)
            
            cmds.append(f"scoreboard players operation #addr {temp_obj} = {rs1} {reg_obj}")
            cmds.append(f"scoreboard players operation #off {temp_obj} = #addr {temp_obj}")
            cmds.append(f"scoreboard players operation #off {temp_obj} %= #four rv_const")
            cmds.append(f"scoreboard players operation #addr {temp_obj} /= #four rv_const")
            cmds.append(f"execute store result storage {self.namespace}:io addr int 1 run scoreboard players get #addr {temp_obj}")
            
            if instr.name == "lr.w":
                cmds.append(f"function {self.namespace}:mem/read_lw with storage {self.namespace}:io")
                if rd: cmds.append(f"scoreboard players operation {rd} {reg_obj} = #res {temp_obj}")
            elif instr.name == "sc.w":
                cmds.append(f"execute store result storage {self.namespace}:io val int 1 run scoreboard players get {rs2} {reg_obj}")
                cmds.append(f"function {self.namespace}:mem/write_sw with storage {self.namespace}:io")
                if rd: cmds.append(f"scoreboard players set {rd} {reg_obj} 0")
            else:
                cmds.append(f"function {self.namespace}:mem/read_lw with storage {self.namespace}:io")
                cmds.append(f"scoreboard players operation #old {temp_obj} = #res {temp_obj}")
                if instr.name == "amoswap.w":
                    cmds.append(f"scoreboard players operation #new {temp_obj} = {rs2} {reg_obj}")
                elif instr.name == "amoadd.w":
                    cmds.append(f"scoreboard players operation #new {temp_obj} = #old {temp_obj}")
                    cmds.append(f"scoreboard players operation #new {temp_obj} += {rs2} {reg_obj}")
                elif instr.name in ["amoand.w", "amoor.w", "amoxor.w"]:
                    cmds.append(f"scoreboard players operation #op1 {temp_obj} = #old {temp_obj}")
                    cmds.append(f"scoreboard players operation #op2 {temp_obj} = {rs2} {reg_obj}")
                    lib_name = instr.name[3:-2]
                    cmds.append(f"function {self.namespace}:lib/{lib_name}")
                    cmds.append(f"scoreboard players operation #new {temp_obj} = #res {temp_obj}")
                elif instr.name in ["amomin.w", "amomax.w", "amominu.w", "amomaxu.w"]:
                    op = "<" if "min" in instr.name else ">"
                    is_unsigned = "u" in instr.name
                    if not is_unsigned:
                        cmds.append(f"scoreboard players operation #new {temp_obj} = #old {temp_obj}")
                        cmds.append(f"execute if score {rs2} {reg_obj} {op} #old {temp_obj} run scoreboard players operation #new {temp_obj} = {rs2} {reg_obj}")
                    else:
                        cmds.append(f"scoreboard players operation #u1 {temp_obj} = #old {temp_obj}")
                        cmds.append(f"scoreboard players operation #u1 {temp_obj} -= #min_int rv_const")
                        cmds.append(f"scoreboard players operation #u2 {temp_obj} = {rs2} {reg_obj}")
                        cmds.append(f"scoreboard players operation #u2 {temp_obj} -= #min_int rv_const")
                        cmds.append(f"scoreboard players operation #new {temp_obj} = #old {temp_obj}")
                        cmds.append(f"execute if score #u2 {temp_obj} {op} #u1 {temp_obj} run scoreboard players operation #new {temp_obj} = {rs2} {reg_obj}")
                
                cmds.append(f"execute store result storage {self.namespace}:io val int 1 run scoreboard players get #new {temp_obj}")
                cmds.append(f"function {self.namespace}:mem/write_sw with storage {self.namespace}:io")
                if rd: cmds.append(f"scoreboard players operation {rd} {reg_obj} = #old {temp_obj}")

            cmds.append(f"scoreboard players add pc {pc_obj} 4")

        elif instr.name == "ecall":
            cmds.append(f"function {self.namespace}:ecall/dispatch")
            cmds.append(f"scoreboard players add pc {pc_obj} 4")
        elif instr.name == "ebreak":
            cmds.append(f"function {self.namespace}:debug/dump_inline")
            cmds.append(f"scoreboard players add pc {pc_obj} 4")
        else:
            if instr.name not in ["jal", "jalr", "beq", "bne", "blt", "bge", "bltu", "bgeu"]:
                cmds.append(f"scoreboard players add pc {pc_obj} 4")
            
        return cmds