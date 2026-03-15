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

def parse_registers(rd, rs1, rs2):
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
def instruction(op, rd="", rs1="", rs2="", imm="0", immRD=False):
    rd, rs1, rs2 = parse_registers(rd, rs1, rs2)
    imm = int(imm)

    if debug:
        print(f"\trd {rd}")
        print(f"\trs2 {rs2}")
        print(f"\trs1 {rs1}")
        print(f"\timm {imm}")

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

def line2tokens(line):
    line = line.strip()

    if (comment := line.find("#")) != -1:
        line = line[0:comment]

    line = line.strip()
    if line == "": return -1

    line = line.replace(" ", ",")
    
    return [token for token in line.split(",") if token != '']

def alert_error(cond, string):
    if cond:
        raise ValueError(string)

labels = {}

def find_labels(lines):
    pc = 0
    for line in lines:
        if not ((tokens := line2tokens(line)) == -1):
            if tokens[0] == "L:":
                labels[tokens[1]] = pc
        pc += 1


pc = 0
def line2instruction(line):
    global labels, pc

    if debug: print(line)

    if (tokens := line2tokens(line)) == -1: return -1

    pc += 1

    # label
    if tokens[0] == "L:":
        return -1

    if tokens[0] == "nop": return instruction("nop")

    # rs2, imm(rs1)
    elif tokens[0] == "sw":
        alert_error(tokens[2].find(")") == -1 or tokens[2].find("(") == -1, "sw must have format rs2,imm(rs1)")

        imm = tokens[2][0:tokens[2].find("(")]
        rs1 = tokens[2][tokens[2].find("(") + 1:tokens[2].find(")")]
        return instruction("sw", rs2=tokens[1], rs1=rs1, imm=imm) 

    # rd, imm(rs1)
    elif tokens[0] == "lw":
        alert_error(tokens[2].find(")") == -1 or tokens[2].find("(") == -1, "lw must have format rd,imm(rs1)")

        imm = tokens[2][0:tokens[2].find("(")]
        rs1 = tokens[2][tokens[2].find("(") + 1:tokens[2].find(")")]
        return instruction("lw", rd=tokens[1], rs1=rs1, imm=imm) 

    # rd, rs1, imm
    elif tokens[0] in ["addi", "andi", "ori", "slli", "srli", "srai"]:
        return instruction(tokens[0], rd=tokens[1], rs1=tokens[2], imm=tokens[3])

    # rd, rs1, rs2
    elif tokens[0] in ["add", "sub", "and", "or", "sll", "srl", "sra"]:
        return instruction(tokens[0], rd=tokens[1], rs1=tokens[2], rs2=tokens[3])

    # rd, imm 
    elif tokens[0] == "li":   return instruction("li",   rd=tokens[1], imm=tokens[2])

    # rd, rs1
    elif tokens[0] in ["mv", "not", "neg"]:
        return instruction(tokens[0], rd=tokens[1], rs1=tokens[2])

    # immRD
    elif tokens[0] == "j":
        if tokens[1].startswith("L"):
            return instruction("j", imm=labels[tokens[1][1:]]-pc+1, immRD=True)
        return instruction("j", imm=tokens[1], immRD=True)

    # rs1
    elif tokens[0] == "jr":
        return instruction("j", rs1=tokens[1])

    # rs1, rs2, immRD
    elif tokens[0] in ["beq", "bne", "blt", "bgt", "bge", "ble"]:
        if tokens[3].startswith("L"):
            return instruction(tokens[0], rs1=tokens[1], rs2=tokens[2], imm=labels[tokens[3][1:]]-pc+1, immRD=True)
        return instruction(tokens[0], rs1=tokens[1], rs2=tokens[2], imm=tokens[3], immRD=True)

    print("could not find instruction " + tokens[0]) 
    pc -= 1

if __name__ == "__main__":
    with open("rriscfibandmove.txt") as f:
        lines = f.readlines()
        find_labels(lines)
        for line in lines:
            if ((ins := line2instruction(line)) != -1):
                print(ins)



























