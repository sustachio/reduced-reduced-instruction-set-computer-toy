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
        self.current_file = "haiii"

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
            self.add_asm(f"{command} x2,x2,x3")
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
        elif segment == "static":
            self.add_asm("li x3,16")
            address = f"{index}(x3)"
        elif segment == "temp":
            self.add_asm("li x3,4")
            address = f"{index}(x3)"

        # frame fields
        elif segment == "local":
            address = f"{index}(x{LCL})"
        elif segment == "argument":
            address = f"{index}(x{ARG})"
        elif segment == "this":
            address = f"{index}(x{THIS})"
        elif segment == "that":
            address = f"{index}(x{THAT})"
        elif segment == "constant": pass
        elif segment == "pointer": pass
        else:
            print(f"weewooweewoo can't find adress to push/pop for segment {segment}")

        if command == "push":
            if segment == "pointer" and index == 0:
                self.add_asm(f"li x2,x{THIS}")
            elif segment == "pointer" and index == 1:
                self.add_asm(f"li x2,x{THAT}")
            elif segment == "constant":
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

    def WriteLabel(self, name):
        self.add_asm(f"# label {name}")
        self.add_asm(f"L: label_{self.current_file}_{name}")

    def WriteGoto(self, name):
        self.add_asm(f"# goto {name}")
        self.add_asm(f"j Llabel_{self.current_file}_{name}")
        self.add_asm("nop")
        self.add_asm("nop")
        self.add_asm("nop")

    def WriteIfGoto(self, name):
        self.add_asm(f"# goto {name}")
        self.add_asm(f"lw x2,-1({SP})")
        self.add_asm(f"addi {SP},{SP},-1")
        self.add_asm(f"li x3,-1")
        self.add_asm(f"beq x2,x3,Llabel_{self.current_file}_{name}")
        self.add_asm("nop")
        self.add_asm("nop")
        self.add_asm("nop")

    def WriteCall(self, name, n_args):
        self.add_asm(f"# call {name} args {n_args}")

        # save state to stack
        self.add_asm(f"addi x2,x{PC},17") ## breaks with speculative execution
        self.add_asm(f"sw x2,0(x{SP})") # return addr
        self.add_asm(f"addi x{SP},x{SP},1")
        self.add_asm(f"sw x{LCL},0(x{SP})") # LCL
        self.add_asm(f"addi x{SP},x{SP},1")
        self.add_asm(f"sw x{ARG},0(x{SP})") # ARG
        self.add_asm(f"addi x{SP},x{SP},1")
        self.add_asm(f"sw x{THIS},0(x{SP})") # THIS
        self.add_asm(f"addi x{SP},x{SP},1")
        self.add_asm(f"sw x{THAT},0(x{SP})") # THAT
        self.add_asm(f"addi x{SP},x{SP},1")

        # repostion args
        self.add_asm(f"addi x{ARG},x{SP},{-5-n_args}")
        self.add_asm(f"mv x{LCL},x{SP}")

        # jump to
        self.add_asm(f"j Lfunc_{self.current_file}_{name}")
        self.add_asm("nop")
        self.add_asm("nop")
        self.add_asm("nop")

    def WriteFunction(self, name, n_vars):
        self.add_asm(f"# function {name} vars {n_vars}")
        self.add_asm(f"L: func_{self.current_file}_{name}")

        # initialize locals, also move stack pointer past
        for i in range(n_vars):
            self.add_asm(f"sw x0,0(x{SP})")
            self.add_asm(f"addi x{SP},x{SP},1")

    def WriteReturn(self):
        self.add_asm("# return")

        self.add_asm(f"lw x3,-5(x{LCL})") # save return addr

        # write result and move stack back
        self.add_asm(f"lw x2,-1(x{SP})")
        self.add_asm(f"sw x2,0(x{ARG})")
        self.add_asm(f"addi x{SP},x{ARG},1")

        # restore segment pointers
        self.add_asm(f"lw x{THAT},-1(x{LCL})")
        self.add_asm(f"lw x{THIS},-2(x{LCL})")
        self.add_asm(f"lw x{ARG},-3(x{LCL})")
        self.add_asm(f"lw x{LCL},-4(x{LCL})")

        # return
        self.add_asm(f"jr x3")
        self.add_asm("nop")
        self.add_asm("nop")
        self.add_asm("nop")




class VMTranslator:
    def __init__(self, file):
        with open(file) as f:
            self.parser = Parser(f.readlines())
            self.codewriter = CodeWritter()

    def translate(self):
        while self.parser.has_more_lines():
            self.parser.advance()

            if (self.parser.command_type() == self.parser.C_MATH):
                self.codewriter.WriteMath(self.parser.arg1())

            elif (self.parser.command_type() == self.parser.C_PUSH):
                self.codewriter.WritePushPop("push", self.parser.arg1(), self.parser.arg2())

            elif (self.parser.command_type() == self.parser.C_POP):
                self.codewriter.WritePushPop("pop", self.parser.arg1(), self.parser.arg2())

            elif (self.parser.command_type() == self.parser.C_GOTO):
                self.codewriter.WriteGoto(self.parser.arg1())

            elif (self.parser.command_type() == self.parser.C_IF_GOTO):
                self.codewriter.WriteIfGoto(self.parser.arg1())

            elif (self.parser.command_type() == self.parser.C_LABEL):
                self.codewriter.WriteLabel(self.parser.arg1())

            elif (self.parser.command_type() == self.parser.C_CALL):
                self.codewriter.WriteCall(self.parser.arg1(), self.parser.arg2())

            elif (self.parser.command_type() == self.parser.C_FUNCTION):
                self.codewriter.WriteFunction(self.parser.arg1(), self.parser.arg2())

            elif (self.parser.command_type() == self.parser.C_RETURN):
                self.codewriter.WriteReturn()

            else:
                print(f"byte code instruction {self.parser.current_instruction} not found")


    def print_output(self):
        print("assembly:")
        pc = 0
        for i in self.codewriter.assembly_instructions:
            if not i.startswith("L:") and not i.startswith("#"):
                print(f"\t{pc:08X}: "+i)
                pc += 1
            else:
                print(f"\t"+i)

        print("machine:")
        a = Assembler(self.codewriter.assembly_instructions)
        for i in a.assemble():
            print(i,end=" ")

    def output(self):
        res = ""
        a = Assembler(self.codewriter.assembly_instructions)
        for i in a.assemble():
            res += i + " "

        return res

a = VMTranslator("programs/vmtesting.vm")
a.translate()
a.print_output()

with open("PROGRAM.txt", "w") as f:
    f.write(a.output())




















            
