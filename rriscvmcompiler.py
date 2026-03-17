from rriscassempler import Assembler

def isnum(a):
    try:
        int(a)
        return True
    except ValueError:
        return False

ZERO_REG = 0
ONE_REG  = 1
PC = 31
SP = 30
LCL = 29
ARG = 28
THIS = 27
THAT = 26
  
class Parser():
    C_MATH     = 0
    C_PUSH     = 1
    C_POP      = 2
    C_LABEL    = 3
    C_GOTO     = 4
    C_IF_GOTO  = 5
    C_FUNCTION = 6
    C_CALL     = 7
    C_RETURN   = 8

    def __init__(self, instructions):
        self.instructions = instructions
        self.current_instruction = ""

        # remove any starting blank lines/comments
        while (self.has_more_lines() and \
               self._parse_and_split_line(self.instructions[0]) == -1):
            self.instructions.pop(0)

    def has_more_lines(self):
        return len(self.instructions) > 0

    def _parse_and_split_line(self, line):
        line = line.strip()

        if (comment := line.find("#")) != -1:
            line = line[0:comment]

        line = line.strip()
        if line == "":
            return -1

        return [token.lower() for token in line.split(" ") if token != '']


    # read in next line and remove empty ones before and after
    def advance(self):
        line = self.instructions.pop(0)

        self.current_instruction = self._parse_and_split_line(line)

        while (self.has_more_lines() and \
               self._parse_and_split_line(self.instructions[0]) == -1):
            self.instructions.pop(0)

    def command_type(self):
        if self.current_instruction[0] in ["add", "sub", "neg", "eq", "gt", "lt", "and", "or", "not"]:
            return self.C_MATH
        if self.current_instruction[0] == "push":
            return self.C_PUSH
        if self.current_instruction[0] == "pop":
            return self.C_POP
        if self.current_instruction[0] == "label":
            return self.C_LABEL
        if self.current_instruction[0] == "goto":
            return self.C_GOTO
        if self.current_instruction[0] == "if-goto":
            return self.C_IF_GOTO
        if self.current_instruction[0] == "function":
            return self.C_FUNCTION
        if self.current_instruction[0] == "call":
            return self.C_CALL
        if self.current_instruction[0] == "return":
            return self.C_RETURN

    def arg1(self):
        if self.command_type() == self.C_MATH:
            return self.current_instruction[0]
        return self.current_instruction[1]

    def arg2(self):
        return int(self.current_instruction[2])

class CodeWritter:
    def __init__(self):
        self.assembly_instructions = []
        self.pc = 0

        self.WriteBootstrap()

    def WriteBootstrap(self):
        self.add_asm("# bootstrap")
        self.add_asm(f"li x{SP},256")
        self.add_asm(f"li x{LCL},500")
        self.add_asm(f"li x{ARG},600")
        self.add_asm(f"li x{THIS},700")
        self.add_asm(f"li x{THAT},800")

    def add_asm(self, text):
        self.assembly_instructions.append(text)
        self.pc += 1

    def WriteMath(self, command):
        self.add_asm(f"# {command}")
        if command in ["add", "sub", "or", "and"]:
            self.add_asm(f"lw  x2,-2(x{SP})")
            self.add_asm(f"lw  x3,-1(x{SP})")
            self.add_asm(f"{command} x2,x3,x2")
            self.add_asm(f"sw  x2,-2(x{SP})")
            self.add_asm(f"addi x{SP},x{SP},-1")
        if command in ["not", "neg"]:
            self.add_asm(f"lw  x2,-1(x{SP})")
            self.add_asm(f"{command} x2,x2")
            self.add_asm(f"sw  x2,-1(x{SP})")
        if command in ["gt", "eq", "lt"]:
            self.add_asm(f"li  x2,-1") # -1 for true, all ones
            self.add_asm(f"lw  x3,-2(x{SP})")
            self.add_asm(f"lw  x4,-1(x{SP})")
            self.add_asm(f"b{command} x3,x4,4")       # BREAKS WITH SPECULATIVE
            self.add_asm(f"nop")
            self.add_asm(f"nop")
            self.add_asm(f"nop")
            self.add_asm(f"li  x2,0")
            self.add_asm(f"sw  x2,-2(x{SP})")
            self.add_asm(f"addi x{SP},x{SP},-1")

    def WritePushPop(self, command, segment, index):
        self.add_asm(f"# {command} {segment} {index}")
        address = ""

        # fixed fields
        if segment == "result":
            address = f"{index}(x0)"
        if segment == "static":
            self.add_asm("li x3,16")
            address = f"{index}(x3)"
        if segment == "temp":
            self.add_asm("li x3,5")
            address = f"{index}(x3)"
        if segment == "pointer":
            self.add_asm("li x3,3")
            address = f"{index}(x3)"

        # frame fields
        if segment == "local":
            address = f"{index}(x{LCL})"
        if segment == "argument":
            address = f"{index}(x{ARG})"
        if segment == "this":
            address = f"{index}(x{THIS})"
        if segment == "that":
            address = f"{index}(x{THAT})"

        if command == "push":
            if segment == "constant":
                self.add_asm(f"li x2,{index}")
            else:
                self.add_asm(f"lw x2,{address}")

            self.add_asm(f"sw x2,0(x{SP})")
            self.add_asm(f"addi x{SP},x{SP},1")

        elif command == "pop":
            if segment == "constant":
                raise ValueError("cant pop to a constant")

            self.add_asm(f"lw x2,-1(x{SP})")
            self.add_asm(f"sw x2,{address}")

            self.add_asm(f"addi x{SP},x{SP},-1")

class VMTranslator:
    def __init__(self, file):
        with open(file) as f:
            self.parser = Parser(f.readlines())
            self.codewriter = CodeWritter()

    def translate_and_print(self):
        while self.parser.has_more_lines():
            self.parser.advance()

            if (self.parser.command_type() == self.parser.C_MATH):
                self.codewriter.WriteMath(self.parser.arg1())
            if (self.parser.command_type() == self.parser.C_PUSH):
                self.codewriter.WritePushPop("push", self.parser.arg1(), self.parser.arg2())
            if (self.parser.command_type() == self.parser.C_POP):
                self.codewriter.WritePushPop("pop", self.parser.arg1(), self.parser.arg2())

        print("assembly:")
        for i in self.codewriter.assembly_instructions:
            print("\t"+i)

        print("machine:")
        a = Assembler(self.codewriter.assembly_instructions)
        for i in a.assemble():
            print(i,end=" ")

    def translate(self):
        res = ""
        a = Assembler(self.codewriter.assembly_instructions)
        for i in a.assemble():
            res += i + " "

        return res

a = VMTranslator("rrisclangtest.txt")
a.translate_and_print()

with open("PROGRAM.txt", "w") as f:
    f.write(a.translate())




















            
