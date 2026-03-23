from parser import *
from assembler import *
from tokenizer import *
from vmcompiler import *

class Compiler:
    def __init__(self, text_block):
        parser = Parser(text_block)
        self.ast = parser.parse_program()

        self.bytecode = ""

        # needed for generating labels
        self.if_count = 0
        self.while_count = 0

        self.static_var_table  = {} # "Class$var": (type, offset from static adresses base)
        self.func_table = {} # "Class$func": (type, arg_n)  OR  "Class.func": (type, arg_n)

        # overwritten for each class
        self.fields_table = {} # "var_name": (type, offset from PTR1)
        self.current_class_context = "" # class name

        # overwritten for each function
        self.arguments_table = {} # "var_name": (type, offset from ARG)
        self.locals_table    = {} # "var_name": (type, offset from LCL)

        self.build_tables()

    def add_bytecode(self, line):
        self.bytecode += line + "\n"

    # self.static_var_table, self.static_func_table, self.methods_table
    # function addresses must be set during compilation
    def build_tables(self):
        for astclass in self.ast.classes:
            # static vars
            for static in astclass.statics:
                token = astclass.name + "$" + static[1]

                if token in self.static_var_table:
                    raise NameError(f"NAME ERROR: cannot have two definitions of '{token}'")

                # type, offset
                self.static_var_table[token] = (static[0], len(self.static_var_table))
                if len(self.static_var_table) > 200:
                    print("WARNING: you've got a lot of statics (>200), ensure table is not full")

            # static funcs
            for aststatic_func in astclass.static_functions:
                token = astclass.name + "$" + aststatic_func.name

                if token in self.func_table:
                    raise NameError(f"NAME ERROR: cannot have two static function definitions of '{token}'")

                self.func_table[token] = (aststatic_func.return_type, len(aststatic_func.params))

            # methods
            for astfunc in astclass.functions:
                token = astclass.name + "." + astfunc.name

                if token in self.func_table:
                    raise NameError(f"NAME ERROR: cannot have two method definitions of '{token}'")

                self.func_table[token] = (astfunc.return_type, len(astfunc.params))
        

    def compile_program(self):
        # TODO: ADD BOOTSTRAP CODE

        self.add_bytecode("# BOOTSTRAP")
        self.add_bytecode("call System$Init 0")
        self.add_bytecode("pop result 0")

        self.add_bytecode("label finalloop")
        self.add_bytecode("goto finalloop")

        for c in self.ast.classes:
            self.compile_class(c)

        return self.bytecode
        

    def compile_class(self, a: ASTClass):
        self.current_class_context = a.name
        self.add_bytecode(f"\t# CLASS {a.name}")

        # build fields table
        self.fields_table = {}

        for type_, field in a.fields:
            self.fields_table[field] = (type_, len(self.fields_table))

        # compile static funcs
        for static_func in a.static_functions:
            self.compile_function_dec(static_func)

        # compile methods
        for method in a.functions:
            self.compile_function_dec(method)


    def compile_function_dec(self, a: ASTFunctionDec):
        func_name = self.current_class_context + ("$" if a.static else ".") + a.name

        # build locals table
        self.locals_table = {}
        for type_, name in a.local_vars:
            if name in self.locals_table:
                raise NameError(f"NAME ERROR: cannot have two method definitions of '{token}'")

            self.locals_table[name] = (type_, len(self.locals_table))

        # build arguments table
        # if not static then first argument should be pointer to self
        self.arguments_table = {}
        if not a.static:
            self.arguments_table["self"] = (self.current_class_context, 0)

        for type_, name in a.params:
            if name in self.locals_table:
                raise NameError(f"NAME ERROR: cannot have two method definitions of '{token}'")

            self.arguments_table[name] = (type_, len(self.arguments_table))


        self.add_bytecode(f"function {func_name} {len(self.locals_table)}")

        # set ptr1 to self if not static
        if not a.static:
            self.add_bytecode("push argument 0")
            self.add_bytecode("pop pointer 0")

        # compile body
        for aststatement in a.statements:
            self.compile_statement(aststatement)

        # all functions return 0 as a basecase and set result[1] to ffffff
        # TODO: proper error handling
        self.add_bytecode("\t# FUNCTION BASE CASE")
        self.add_bytecode("push constant -1")
        self.add_bytecode("pop result 1")
        self.add_bytecode("push constant 0")
        self.add_bytecode("return")
    
    def compile_statement(self, a: ASTStatement):
        if type(a) == ASTCallStatement:
            self.compile_call_statement(a)
        elif type(a) == ASTLetStatement:
            self.compile_let_statement(a)
        elif type(a) == ASTIfStatement:
            self.compile_if_statement(a)
        elif type(a) == ASTWhileStatement:
            self.compile_while_statement(a)
        elif type(a) == ASTReturnStatement:
            self.compile_return_statement(a)

    def compile_call_statement(self, a: ASTCallStatement):
        self.add_bytecode(f"\t# CALL STATEMENT")
        self.compile_function_call(a.call)
        self.add_bytecode("pop temp 0") # remove result

    def compile_term(self, a: ASTTerm):
        if type(a) == ASTFuncCall:
            self.compile_function_call(a)
        elif type(a) == ASTIntConstant:
            self.compile_int_constant(a)
        elif type(a) == ASTStringConstant:
            self.compile_string_constant(a)
        elif type(a) == ASTKeywordConstant:
            self.compile_keyword_constant(a)
        elif type(a) == ASTVarName:
            self.compile_var_name(a)
        elif type(a) == ASTArrayAccess:
            self.compile_array_access(a)
        elif type(a) == ASTExpression:
            self.compile_expression(a)
        else:
            raise Exception(f"COMPILER ERROR: compile_term called on non term '{str(a)}'")

    def compile_function_call(self, a: ASTFuncCall):
        obj_type = ""
        # .func / $func
        if a.obj.value == "self":
            obj_type = self.current_class_context
        # classname$func
        elif a.static:
            obj_type = a.obj.value
        # var.func
        # .var.func
        # $var.func
        else:
            if a.obj.scope == "static":
                obj_type = self.static_var_table[self.current_class_context + "$" + a.func_name][0]
            elif a.obj.scope == "field":
                obj_type = self.fields_table[a.obj.value][0]
            elif a.obj.scope == "local" and a.obj.value in self.arguments_table:
                obj_type = self.arguments_table[a.obj.value][0]
            elif a.obj.scope == "local":
                obj_type = self.locals_table[a.obj.value][0]
            else:
                raise Exception(f"COMPILER ERROR: failed to fetch type of calling class of function call '{str(a)}'")

        if obj_type == "":
            raise Exception(f"COMPILER ERROR: got empty caller object type for function call '{str(a)}'")

        print(str(a))
        func_name = obj_type + ("$" if a.static else ".") + a.func_name

        self.add_bytecode(f"\t# FUNCTION CALL " + func_name)

        n_args = self.func_table[func_name][1]

        # if not static the adress of the object must be pushed to arguments first
        if not a.static:
            n_args += 1

            if a.obj.value == "self":
                self.add_bytecode(f"push pointer 0")

            elif a.obj.scope == "static":
                self.add_bytecode(f"push static {self.static_var_table[self.current_class_context + '$' + a.obj.value][1]}")

            elif a.obj.scope == "field":
                self.add_bytecode(f"push ptr1 {self.fields_table[a.obj.value][1]}")

            elif a.obj.scope == "local" and a.obj.value in self.arguments_table:
                self.add_bytecode(f"push argument {self.arguments_table[a.obj.value][1]}")

            elif a.obj.scope == "local":
                self.add_bytecode(f"push local {self.locals_table[a.obj.value][1]}")

            else:
                raise Exception("COMPILER ERROR: failed to fetch address of calling object for funciton '{str(a)}'")

        for astexpression in a.params:
            self.compile_expression(astexpression)

        self.add_bytecode(f"call {func_name} {n_args}")

    def compile_expression(self, a: ASTExpression):
        self.add_bytecode(f"\t# EXPRESSION")
        if len(a.terms) == 0: return

        self.compile_term(a.terms[0])

        for i in range(a.op_count):
            self.compile_term(a.terms[i + 1])
            
            if a.ops[i] == "+":
                self.add_bytecode("add")
            elif a.ops[i] == "-":
                self.add_bytecode("sub")
            # TODO: implement multiplication and division
            elif a.ops[i] == "*":
                raise Exception(f"COMPILER ERROR: multiplication with symbol '*' in expressions has not yet been implemnted, found when compiling '{str(a)}'")
            elif a.ops[i] == "/":
                raise Exception(f"COMPILER ERROR: division with symbol '/' in expressions has not yet been implemnted, found when compiling '{str(a)}'")
            elif a.ops[i] == "&":
                self.add_bytecode("and")
            elif a.ops[i] == "|":
                self.add_bytecode("or")
            elif a.ops[i] == ">":
                self.add_bytecode("gt")
            elif a.ops[i] == "<":
                self.add_bytecode("lt")
            elif a.ops[i] == "==":
                self.add_bytecode("eq")
            elif a.ops[i] == "<<":
                self.add_bytecode("sll")
            elif a.ops[i] == ">>":
                self.add_bytecode("srl")
            elif a.ops[i] == ">>>":
                self.add_bytecode("sra")

    def compile_int_constant(self, a: ASTIntConstant):
        self.add_bytecode(f"push constant {a.value}")

    def compile_string_constant(self, a: ASTStringConstant):
        raise Exception(f"COMPILER ERROR: string constants not yet implemented, found when compiling '{str(a)}'")

    def compile_keyword_constant(self, a: ASTKeywordConstant):
        self.add_bytecode(f"\t# KEYWORD CONSTANT")
        if a.value == "true":
            self.add_bytecode("push constant -1")
        elif a.value == "false":
            self.add_bytecode("push constant 0")
        elif a.value == "self":
            self.add_bytecode("push pointer 0")
        elif a.value == "null":
            self.add_bytecode("push constant 0")
        else:
            raise Exception(f"COMPILER ERROR: unknown keyword '{str(a)}'")

    def compile_var_name(self, a: ASTVarName):
        self.add_bytecode(f"\t# VARNAME {a.scope} {a.value}")
        if a.value == "self":
            self.add_bytecode(f"push pointer 0")

        elif a.scope == "static":
            self.add_bytecode(f"push static {self.static_var_table[self.current_class_context + '$' + a.value][1]}")

        elif a.scope == "field":
            self.add_bytecode(f"push ptr1 {self.fields_table[a.value][1]}")

        elif a.scope == "local" and a.value in self.arguments_table:
            self.add_bytecode(f"push argument {self.arguments_table[a.value][1]}")

        elif a.scope == "local":
            self.add_bytecode(f"push local {self.locals_table[a.value][1]}")

        else:
            raise Exception(f"COMPILER ERROR: could not find kind (static/field/local) of variable '{str(a)}'")

    def compile_array_access(self, a: ASTArrayAccess):
        self.add_bytecode(f"\t# ARRAY ACCESS")

        self.compile_var_name(a.var)
        self.compile_expression(a.offset)

        self.add_bytecode("add")
        self.add_bytecode("pop pointer 1")
        self.add_bytecode("push ptr2 0")

    def compile_let_statement(self, a: ASTLetStatement):
        self.add_bytecode(f"\t# LET STATEMENT")

        self.compile_expression(a.right)

        if type(a.left) == ASTVarName:
            if a.left.scope == "static":
                self.add_bytecode(f"pop static {self.static_var_table[self.current_class_context + '$' + a.left.value][1]}")

            elif a.left.scope == "field":
                self.add_bytecode(f"pop ptr1 {self.fields_table[a.left.value][1]}")

            elif a.left.scope == "local" and a.left.value in self.arguments_table:
                self.add_bytecode(f"pop argument {self.arguments_table[a.left.value][1]}")

            elif a.left.scope == "local":
                self.add_bytecode(f"pop local {self.locals_table[a.left.value][1]}")

            else:
                raise Exception(f"COMPILER ERROR: can not set variable with kind (static/field/local) '{a.left.scope}' when compiling '{str(a)}'")

        elif type(a.left) == ASTArrayAccess:
            self.compile_var_name(a.left.var)
            self.compile_expression(a.left.offset)

            self.add_bytecode("add")
            self.add_bytecode("pop pointer 1")
            self.add_bytecode("pop ptr2 0")

    def compile_if_statement(self, a: ASTIfStatement):
        self.add_bytecode(f"\t# IF STATEMENT")
        if_number = self.if_count
        self.if_count += 1

        self.compile_expression(a.condition)

        self.add_bytecode(f"if-goto ifthen{if_number}")

        for aststatement in a.otherwise:
            self.compile_statement(aststatement)

        self.add_bytecode(f"goto ifend{if_number}")

        self.add_bytecode(f"label ifthen{if_number}")

        for aststatement in a.then:
            self.compile_statement(aststatement)

        self.add_bytecode(f"label ifend{if_number}")

    # NOTE: support for continue/break could be cool
    def compile_while_statement(self, a: ASTWhileStatement):
        self.add_bytecode(f"\t# WHILE STATEMENT")

        while_number = self.while_count
        self.while_count += 1

        self.add_bytecode(f"label while{while_number}")

        self.compile_expression(a.condition)

        self.add_bytecode("not")
        self.add_bytecode(f"if-goto whileend{while_number}")

        for aststatement in a.do:
            self.compile_statement(aststatement)

        self.add_bytecode(f"goto while{while_number}")
        self.add_bytecode(f"label whileend{while_number}")

    # NOTE: need to add support for void return statements
    def compile_return_statement(self, a: ASTReturnStatement):
        self.add_bytecode(f"\t# RETURN STATEMENT")

        self.compile_expression(a.value)
        self.add_bytecode(f"return")
        

    def compile_unary_op(self, a: ASTUnaryOp):
        self.add_bytecode(f"\t# UNARY OP")

        self.compile_term(a.value)

        if a.op == "-":
            self.add_bytecode("neg")
        elif a.op == "~":
            self.add_bytecode("not")

if __name__ == "__main__":
    with open("programs/os.rbl") as f:
        a = Compiler(f.read())
        print("VM code:")
        code = a.compile_program()
        print(ident(code))
        print("Assembly code:")
        b = VMTranslator(code)
        b.translate()
        b.print_output()

        with open("PROGRAM.txt", "w") as f:
            f.write(b.output())
