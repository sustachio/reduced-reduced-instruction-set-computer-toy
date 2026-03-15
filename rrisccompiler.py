from rriscassempler import line2instruction, line2tokens, find_labels

def isnum(a):
    try:
        int(a)
        return True
    except ValueError:
        return False

ZERO_REG = 0
ONE_REG  = 1
FRAME_REG= 30

class Compiler:
    def __init__(self):
        self.instructions = []
        self.variables = {}
        self.frame_size = 0

        self.regs_waiting_on_result = [-1,-1,-1] # TODO shift reg for adding nops

        self.used_while_labels = []
        self.while_stack = []
        self.next_free_label = 0

        with open("rrisclangtest.txt") as f:
            self.compilelines(f.readlines())
            self.output()

    def add_ins(self, ins):
        self.instructions.append(ins)

    def output(self):
        print("assembly:")
        for ins in self.instructions:
            print("\t"+ins)
        print("machine code:")
        find_labels(self.instructions)
        for ins in self.instructions:
            if ((ins := line2instruction(ins)) != -1):
                print(ins + " ", end="")


    def compilelines(self, lines):
        for line in lines:
            if ((line := line2tokens(line)) == -1): continue

            if line[0] == "INIT":
                self.variables[line[1]] = self.frame_size
                self.frame_size += 1
                continue

            if line[0] == "LET":
                val = line[3]
                if isnum(val):
                    self.add_ins(f"li 2,{int(val)}")
                    self.add_ins("nop")
                    self.add_ins("nop")
                    self.add_ins("nop")
                    self.add_ins(f"sw 2,{self.variables[line[1]]}({FRAME_REG})")
                    self.add_ins("nop")
                    self.add_ins("nop")
                    self.add_ins("nop")
                else: # must fetch other variable
                    self.add_ins(f"lw 2,{self.variables[val]}({FRAME_REG})")
                    self.add_ins("nop")
                    self.add_ins("nop")
                    self.add_ins("nop")
                    self.add_ins(f"sw 2,{self.variables[line[1]]}({FRAME_REG})")
                    self.add_ins("nop")
                    self.add_ins("nop")
                    self.add_ins("nop")
                continue

            if line[0] == "MATH":
                res  = line[1]
                op   = line[3]
                val1 = line[4]
                val2 = 0

                two_operands = len(line)>5

                if two_operands:
                    val2 = line[5]

                self.add_ins(f"lw 2,{self.variables[val1]}({FRAME_REG})")
                if two_operands and not isnum(val2):
                    self.add_ins(f"lw 3,{self.variables[val2]}({FRAME_REG})")
                self.add_ins("nop")
                self.add_ins("nop")
                self.add_ins("nop")

                if op == "ADD" and isnum(val2):
                    self.add_ins(f"addi 2,2,{val2}")
                elif op == "ADD":
                    self.add_ins("add 2,2,3")
                elif op == "SUB":
                    # no subi instruction
                    if isnum(val2):
                        self.add_ins(f"li 3,{val2}")
                        self.add_ins("nop")
                        self.add_ins("nop")
                        self.add_ins("nop")
                    self.add_ins("sub 2,2,3")
                elif op == "NEG":
                    self.add_ins("neg 2,2")
                elif op == "AND" and isnum(val2):
                    self.add_ins(f"andi 2,2,{val2}")
                elif op == "AND":
                    self.add_ins("and 2,2,3")
                elif op == "OR" and isnum(val2):
                    self.add_ins(f"ori 2,2,{val2}")
                elif op == "OR":
                    self.add_ins("or 2,2,3")
                elif op == "SLL" and isnum(val2):
                    self.add_ins(f"slli 2,2,{val2}")
                elif op == "SLL":
                    self.add_ins("sll 2,2,3")
                elif op == "SRL" and isnum(val2):
                    self.add_ins(f"srli 2,2,{val2}")
                elif op == "SRL":
                    self.add_ins("srl 2,2,3")
                elif op == "SRA" and isnum(val2):
                    self.add_ins(f"srai 2,2,{val2}")
                elif op == "SRA":
                    self.add_ins("sra 2,2,3")

                self.add_ins("nop")
                self.add_ins("nop")
                self.add_ins("nop")


                self.add_ins(f"sw 2,{self.variables[res]}({FRAME_REG})")
                self.add_ins("nop")
                self.add_ins("nop")
                self.add_ins("nop")
                continue

            if line[0] == "WHILE":
                l = "loopstart" + str(self.next_free_label)
                self.next_free_label += 1
                self.used_while_labels.append(l)

                self.add_ins("L: " + l)

                self.while_stack.append(line)
                continue

            if line[0] == "WEND":
                l = self.used_while_labels.pop()
                line = self.while_stack.pop()

                if isnum(line[1]):
                    self.add_ins(f"li 2,{line[1]}")
                else:
                    self.add_ins(f"lw 2,{self.variables[line[1]]}({FRAME_REG})")

                if isnum(line[3]):
                    self.add_ins(f"li 3,{line[3]}")
                else:
                    self.add_ins(f"lw 3,{self.variables[line[3]]}({FRAME_REG})")

                self.add_ins("nop")
                self.add_ins("nop")
                self.add_ins("nop")

                if   line[2] == "==": self.add_ins("beq 2,3,L" + l)
                elif line[2] == "!=": self.add_ins("bne 2,3,L" + l)
                elif line[2] == "<":  self.add_ins("blt 2,3,L" + l)
                elif line[2] == ">":  self.add_ins("bgt 2,3,L" + l)
                elif line[2] == "<=": self.add_ins("ble 2,3,L" + l)
                elif line[2] == ">=": self.add_ins("bge 2,3,L" + l)


                self.add_ins("nop")
                self.add_ins("nop")
                self.add_ins("nop")











c=Compiler()
