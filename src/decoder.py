import struct
from instructions import Instruction, InstructionType

def sign_extend(value, bits):
    sign_bit = 1 << (bits - 1)
    return (value & (sign_bit - 1)) - (value & sign_bit)

class Decoder:
    def __init__(self, binary_data, start_address=0):
        self.data = binary_data
        self.current_address = start_address
        self.instructions = []

    def decode_all(self):
        offset = 0
        while offset < len(self.data):
            if offset + 4 > len(self.data):
                break
            
            instr_word = struct.unpack_from('<I', self.data, offset)[0]
            instr = self.decode_word(self.current_address + offset, instr_word)
            self.instructions.append(instr)
            offset += 4
        return self.instructions

    def decode_word(self, address, word):
        opcode = word & 0x7F
        rd = (word >> 7) & 0x1F
        funct3 = (word >> 12) & 0x07
        rs1 = (word >> 15) & 0x1F
        rs2 = (word >> 20) & 0x1F
        funct7 = (word >> 25) & 0x7F
        
        imm_i = sign_extend((word >> 20) & 0xFFF, 12)
        imm_s = sign_extend(((word >> 25) << 5) | ((word >> 7) & 0x1F), 12)
        imm_b = sign_extend(((word >> 31) << 12) | ((word & 0x7E000000) >> 20) | ((word & 0xF00) >> 7) | ((word & 0x80) << 4), 13)
        imm_u = word & 0xFFFFF000
        imm_j = sign_extend(((word >> 31) << 20) | (word & 0xFF000) | ((word & 0x100000) >> 9) | ((word & 0x7FE00000) >> 20), 21)

        name = "unknown"
        itype = None

        if opcode == 0x37:
            name = "lui"
            return Instruction(address, name, InstructionType.U_TYPE, rd=rd, imm=imm_u)
        
        if opcode == 0x17:
            name = "auipc"
            return Instruction(address, name, InstructionType.U_TYPE, rd=rd, imm=imm_u)
            
        if opcode == 0x6F:
            name = "jal"
            return Instruction(address, name, InstructionType.J_TYPE, rd=rd, imm=imm_j)

        if opcode == 0x67:
            name = "jalr"
            return Instruction(address, name, InstructionType.I_TYPE, rd=rd, rs1=rs1, imm=imm_i)
            
        if opcode == 0x63:
            itype = InstructionType.B_TYPE
            if funct3 == 0: name = "beq"
            elif funct3 == 1: name = "bne"
            elif funct3 == 4: name = "blt"
            elif funct3 == 5: name = "bge"
            elif funct3 == 6: name = "bltu"
            elif funct3 == 7: name = "bgeu"
            return Instruction(address, name, itype, rs1=rs1, rs2=rs2, imm=imm_b)

        if opcode == 0x03:
            itype = InstructionType.I_TYPE
            if funct3 == 0: name = "lb"
            elif funct3 == 1: name = "lh"
            elif funct3 == 2: name = "lw"
            elif funct3 == 4: name = "lbu"
            elif funct3 == 5: name = "lhu"
            return Instruction(address, name, itype, rd=rd, rs1=rs1, imm=imm_i)

        if opcode == 0x23:
            itype = InstructionType.S_TYPE
            if funct3 == 0: name = "sb"
            elif funct3 == 1: name = "sh"
            elif funct3 == 2: name = "sw"
            return Instruction(address, name, itype, rs1=rs1, rs2=rs2, imm=imm_s)

        if opcode == 0x13:
            itype = InstructionType.I_TYPE
            if funct3 == 0: name = "addi"
            elif funct3 == 2: name = "slti"
            elif funct3 == 3: name = "sltiu"
            elif funct3 == 4: name = "xori"
            elif funct3 == 6: name = "ori"
            elif funct3 == 7: name = "andi"
            elif funct3 == 1: 
                name = "slli"
                imm_i = rs2
            elif funct3 == 5:
                if (word >> 30) == 0: name = "srli"
                else: name = "srai"
                imm_i = rs2
            return Instruction(address, name, itype, rd=rd, rs1=rs1, imm=imm_i)

        if opcode == 0x33:
            itype = InstructionType.R_TYPE
            if funct7 == 0:
                if funct3 == 0: name = "add"
                elif funct3 == 1: name = "sll"
                elif funct3 == 2: name = "slt"
                elif funct3 == 3: name = "sltu"
                elif funct3 == 4: name = "xor"
                elif funct3 == 5: name = "srl"
                elif funct3 == 6: name = "or"
                elif funct3 == 7: name = "and"
            elif funct7 == 0x20:
                if funct3 == 0: name = "sub"
                elif funct3 == 5: name = "sra"
            elif funct7 == 0x01:
                if funct3 == 0: name = "mul"
                elif funct3 == 1: name = "mulh"
                elif funct3 == 2: name = "mulhsu"
                elif funct3 == 3: name = "mulhu"
                elif funct3 == 4: name = "div"
                elif funct3 == 5: name = "divu"
                elif funct3 == 6: name = "rem"
                elif funct3 == 7: name = "remu"
            return Instruction(address, name, itype, rd=rd, rs1=rs1, rs2=rs2)

        if opcode == 0x73:
            if word == 0x00000073: return Instruction(address, "ecall", InstructionType.I_TYPE, rd=0)
            if word == 0x00100073: return Instruction(address, "ebreak", InstructionType.I_TYPE, rd=0)

        if opcode == 0x2F:
            itype = InstructionType.R_TYPE
            funct5 = (word >> 27) & 0x1F
            if funct5 == 0x02: name = "lr.w"
            elif funct5 == 0x03: name = "sc.w"
            elif funct5 == 0x01: name = "amoswap.w"
            elif funct5 == 0x00: name = "amoadd.w"
            elif funct5 == 0x04: name = "amoxor.w"
            elif funct5 == 0x0C: name = "amoand.w"
            elif funct5 == 0x08: name = "amoor.w"
            elif funct5 == 0x10: name = "amomin.w"
            elif funct5 == 0x14: name = "amomax.w"
            elif funct5 == 0x18: name = "amominu.w"
            elif funct5 == 0x1C: name = "amomaxu.w"
            return Instruction(address, name, itype, rd=rd, rs1=rs1, rs2=rs2)

        return Instruction(address, "unknown", InstructionType.R_TYPE, rd=0, rs1=0, rs2=0, imm=0)
