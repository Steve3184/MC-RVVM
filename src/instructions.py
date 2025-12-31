from enum import Enum, auto

class InstructionType(Enum):
    R_TYPE = auto()
    I_TYPE = auto()
    S_TYPE = auto()
    B_TYPE = auto()
    U_TYPE = auto()
    J_TYPE = auto()

class Instruction:
    def __init__(self, address, name, type, rd=0, rs1=0, rs2=0, imm=0):
        self.address = address
        self.name = name
        self.type = type
        self.rd = rd
        self.rs1 = rs1
        self.rs2 = rs2
        self.imm = imm

    def __repr__(self):
        return f"{hex(self.address)}: {self.name} rd={self.rd} rs1={self.rs1} rs2={self.rs2} imm={self.imm}"