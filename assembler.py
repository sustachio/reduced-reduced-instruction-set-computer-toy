debug = False

ops = {
    "nop": 0b000000,
    "sw": 0b000010,
    "li": 0b000100,
    "mv": 0b000101,
    "addi": 0b000110,
    "add": 0b000111,
    "sub": 0b001000,
    "neg": 0b001001,
    "andi": 0b001010,
    "and": 0b001011,
    "ori": 0b001100,
    "or": 0b001101,
    "slli": 0b001110,
    "sll": 0b001111,
    "srli": 0b010000,
    "srl": 0b010001,
    "srai": 0b010010,
    "sra": 0b010011,
    "j": 0b010100,
    "beq": 0b010110,
    "bne": 0b010111,
    "blt": 0b011000,
    "bgt": 0b011001,
    "bge": 0b011010,
    "ble": 0b011011,
    "lw": 0b011100,
    "jr": 0b011101,
    "not": 0b011111
}

class Assembler:
    def __init__(self, assembly_list):
        self.assembly_list = assembly_list
        self.labels = {}
        self.pc = 0

    def parse_registers(self, rd, rs1, rs2):
        if rd == "":  rd  = "0"
        if rs1 == "": rs1 = "0"
        if rs2 == "": rs2 = "0"

        if not rd[0].isdigit():  rd  = rd[1:]
        if not rs1[0].isdigit(): rs1 = rs1[1:]
        if not rs2[0].isdigit(): rs2 = rs2[1:]

        rd  = int(rd)
        rs1 = int(rs1)
        rs2 = int(rs2)

        return (rd, rs1, rs2)

    # returns binary instruction
    def instruction(self, op, rd="", rs1="", rs2="", imm="0", immRD=False):
        rd, rs1, rs2 = self.parse_registers(rd, rs1, rs2)
        imm = int(imm)

        op  = ops[op]
        rd  = (rd  & 0b11111)<<16
        rs1 = (rs1 & 0b11111)<<11
        rs2 = (rs2 & 0b11111)<<6

        if immRD:
            imm = (imm & 0b1111_1111_1111_1111)<<16
            rd = 0
        else:
            imm = (imm & 0b111_1111_1111)<<21
        
        instruction = imm+rd+op+rs1+rs2
        return f"{instruction:08x}"

    def parse_and_split_line(self, line):
        line = line.strip()

        if (comment := line.find("#")) != -1:
            line = line[0:comment]

        line = line.strip()
        if line == "": return -1

        line = line.replace(" ", ",")
        
        return [token for token in line.split(",") if token != '']

    def alert_error(self, cond, string):
        if cond:
            raise ValueError(string)

    def find_labels(self, lines):
        self.pc = 0
        for line in lines:
            if not ((tokens := self.parse_and_split_line(line)) == -1):
                if tokens[0] == "L:":
                    self.labels[tokens[1]] = self.pc
                    if debug: print(f"\tDEBUG: label {tokens[1]} at {self.pc}")
                else:
                    self.pc += 1
        self.pc = 0

    # allows to find labels
    def parse_imm(self, imm):
        if imm.startswith("LA"): # label absolute
            if debug: print(f"\tDEBUG: parsed absolute label {imm}")
            return self.labels[imm[2:]]
        if imm.startswith("L"):
            if debug: print(f"\tDEBUG: parsed label {imm}")
            return self.labels[imm[1:]]-self.pc
        return imm

    def assemble_line(self, line):
        if debug: print(f"\t\tDEBUG PC {self.pc+1}: " + line)

        if (tokens := self.parse_and_split_line(line)) == -1: return -1

        # label
        if tokens[0] == "L:":
            return -1

        self.pc += 1

        if tokens[0] == "nop": return self.instruction("nop")

        # rs2, imm(rs1)
        elif tokens[0] == "sw":
            self.alert_error(tokens[2].find(")") == -1 or tokens[2].find("(") == -1, "sw must have format rs2,imm(rs1)")

            imm = tokens[2][0:tokens[2].find("(")]
            rs1 = tokens[2][tokens[2].find("(") + 1:tokens[2].find(")")]
            return self.instruction("sw", rs2=tokens[1], rs1=rs1, imm=imm) 

        # rd, imm(rs1)
        elif tokens[0] == "lw":
            self.alert_error(tokens[2].find(")") == -1 or tokens[2].find("(") == -1, "lw must have format rd,imm(rs1)")

            imm = tokens[2][0:tokens[2].find("(")]
            rs1 = tokens[2][tokens[2].find("(") + 1:tokens[2].find(")")]
            return self.instruction("lw", rd=tokens[1], rs1=rs1, imm=imm) 

        # rd, rs1, imm
        elif tokens[0] in ["addi", "andi", "ori", "slli", "srli", "srai"]:
            return self.instruction(tokens[0], rd=tokens[1], rs1=tokens[2], imm=self.parse_imm(tokens[3]))

        # rd, rs1, rs2
        elif tokens[0] in ["add", "sub", "and", "or", "sll", "srl", "sra"]:
            return self.instruction(tokens[0], rd=tokens[1], rs1=tokens[2], rs2=tokens[3])

        # rd, imm 
        elif tokens[0] == "li":   return self.instruction("li",   rd=tokens[1], imm=self.parse_imm(tokens[2]))

        # rd, rs1
        elif tokens[0] in ["mv", "not", "neg"]:
            return self.instruction(tokens[0], rd=tokens[1], rs1=tokens[2])

        # immRD
        elif tokens[0] == "j":
            return self.instruction("j", imm=self.parse_imm(tokens[1]), immRD=True)

        # rs1
        elif tokens[0] == "jr":
            return self.instruction("jr", rs1=tokens[1])

        # rs1, rs2, immRD
        elif tokens[0] in ["beq", "bne", "blt", "bgt", "bge", "ble"]:
            return self.instruction(tokens[0], rs1=tokens[1], rs2=tokens[2], imm=self.parse_imm(tokens[3]), immRD=True)

        print("could not find instruction " + tokens[0]) 
        self.pc -= 1

    def assemble(self):
        res = []
        self.find_labels(self.assembly_list)
        for line in self.assembly_list:
            if ((ins := self.assemble_line(line)) != -1):
                res.append(ins)

        return res


if __name__ == "__main__":
    with open("programs/fibandmove.asm") as f:
        lines = f.readlines()
        a = Assembler(lines)
        for line in a.assemble():
            print(line)



























