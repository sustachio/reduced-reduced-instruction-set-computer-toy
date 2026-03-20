from __future__ import annotations
from enum import Enum
from dataclasses import dataclass

def is_num(a):
    try:
        int(a)
        return True
    except ValueError:
        return False

class TokenType(Enum):
    KEYWORD = 0
    SYMBOL = 1
    IDENTIFIER = 2
    INT_CONSTANT = 3
    STRING_CONSTANT = 4

class Keyword(Enum):
    END = 0
    CLASS = 1
    DEF = 2
    STATICDEF = 3
    FIELD = 4
    STATIC = 5
    LOCAL = 6
    INT = 7
    CHAR = 8
    BOOL = 9
    VOID = 10
    TRUE = 11
    FALSE = 12
    NULL = 13
    SELF = 14
    LET = 15
    CALL = 16
    IF = 17
    THEN = 18
    ELSE = 19
    WHILE = 20
    RETURN = 21

symbols   = ['(', ')', ',', ';', '$', '.', '+', '-', '*', '/', '&', '|', '>', '<', '=', '~', '[', ']']
keywords = ['end', 'class', 'def', 'staticdef', 'field', 'static', 'local', 'int', 'char', 'bool', 'void', 'true', 'false', 'null', 'self', 'let', 'call', 'if', 'then', 'else', 'while', 'return']
class Tokenizer:
    def __init__(self, text_block):
        self.text_block = text_block

        self.token_type = TokenType.KEYWORD

        self.current_token = ""

        self.lines = 1

        self.keyword = Keyword.END
        self.symbol = ""
        self.identifier = ""
        self.int_value = 0
        self.string_value = ""

        # needed to allow for backtracking
        self.tokens = []
        self.current_token_i = -1


    def char(self):
        return self.text_block[0]

    def next_char(self):
        return self.text_block[1]

    def advance_char(self):
        self.text_block = self.text_block[1:]

    def has_more_tokens(self):
        i = 0

        while len(self.text_block) > i:
            # ignore comments
            if self.text_block[i] == "#":
                while self.text_block[i] != "\n":
                    i += 1

            if not self.text_block[i] in " \t\n": return True
            i += 1

        return False

    def back_track(self):
        self.current_token_i -= 1
        self.current_token = self.tokens[self.current_token_i]

    def advance(self):
        if len(self.tokens) > self.current_token_i+1:
            self.current_token_i += 1
            self.current_token = self.tokens[self.current_token_i]
            return

        # $ name (
        #   ^

        self.last_token = self.current_token

        build_word = ""

        while self.char() in "# \t\n":
            # skip whitespace
            while self.char() in " \t\n":
                if self.char() == "\n": self.lines += 1
                self.advance_char()
            # skip comments
            if self.char() == "#":
                while not self.char() in "\n":
                    self.advance_char()


        # parse string literal
        if self.char() == "\"":
            self.advance_char()
            while self.has_more_tokens() and self.char() != "\"":
                build_word += self.char()
                self.advance_char()

            self.advance_char() # final "

            self.token_type = TokenType.STRING_CONSTANT
            self.string_value = build_word
            self.current_token = build_word
            self.tokens.append(self.current_token)
            self.current_token_i += 1
            return

        # parse number
        if is_num(self.char()):
            while self.has_more_tokens() and is_num(self.char()):
                build_word += self.char()
                self.advance_char()

            self.token_type = TokenType.INT_CONSTANT
            self.int_value = int(build_word)
            self.current_token = build_word
            self.tokens.append(self.current_token)
            self.current_token_i += 1
            return

        # parse symbol
        if self.char() in symbols:
            self.token_type = TokenType.SYMBOL
            if len(self.text_block) > 1 and self.text_block[0:2] == "==":
                self.advance_char()
                self.advance_char()

                self.symbol = "=="
                self.current_token = "=="
                self.tokens.append(self.current_token)
                self.current_token_i += 1
                return


            self.symbol = self.char()
            self.current_token = self.char()
            self.tokens.append(self.current_token)
            self.current_token_i += 1
            self.advance_char()
            return

        # parse identifier/keyword
        while self.has_more_tokens() and not self.char() in symbols and not self.char() in " \t\n":
            build_word += self.char()
            self.advance_char()

        if build_word in keywords:
            self.token_type = TokenType.KEYWORD
            self.keyword = build_word
            self.current_token = build_word
            self.tokens.append(self.current_token)
            self.current_token_i += 1
            return

        # identifier
        self.token_type = TokenType.IDENTIFIER
        self.identifier = build_word
        self.current_token = build_word
        self.tokens.append(self.current_token)
        self.current_token_i += 1

"""
with open("langex.txt") as f:
    a = Tokenizer(f.read())

    while a.has_more_tokens():
        a.advance()
        if a.token_type == TokenType.KEYWORD:
            print("kw " + a.keyword)
        if a.token_type == TokenType.IDENTIFIER:
            print("id " + a.identifier)
        if a.token_type == TokenType.SYMBOL:
            print("mb " + a.symbol)
        if a.token_type == TokenType.STRING_CONSTANT:
            print("st " + a.string_value)
        if a.token_type == TokenType.INT_CONSTANT:
            print("nt " + str(a.int_value))
    """

def ident(lines):
    build = ""
    if lines == None:
        return "\tNONETYPE"

    for line in lines.split("\n"):
        build += "\n\t" + line

    return build

# parser generates an AST
@dataclass
class ASTProgram:
    classes: list[ASTClass]

    def __str__(self):
        build = "ASTProgram\n"
        for c in self.classes:
            build += ident(str(c))

        return build

@dataclass
class ASTClass:
    name: str
    fields: list  # [(type, name), ... ]
    statics: list # [(type, name), ...]
    functions: list[ASTFunctionDec]
    static_functions: list[ASTFunctionDec]

    def __str__(self):
        build = f"ASTClass {self.name}\n" 

        build += f"\tfields:\n" 
        for f in self.fields:
            build += "\t\t" + f[0] + " " + f[1] + "\n"

        build += f"\tstatics:\n" 
        for s in self.statics:
            build += "\t\t" + s[0] + " " + s[1] + "\n"

        build += f"\tfunctions:\n" 
        for f in self.functions:
            build += ident(ident(str(f))) + "\n"

        build += f"\tstatic functions:\n" 
        for s in self.static_functions:
            build += ident(ident(str(s))) + "\n"

        return build

@dataclass
class ASTFunctionDec:
    static: bool

    return_type: str
    name: str
    local_vars: list # [(type, name), ...]
    params: list     # [(type, name), ...]

    statements: list[ASTStatement]

    def __str__(self):
        build = "ASTFunctionDec staticdef " if self.static else "def "
        build += self.return_type + " "
        build += self.name + "("

        for param in self.params:
           build += param[0] + " " + param[1] + ", "

        build += ")\n"
        build += "\tlocals:\n"
        for local in self.local_vars:
           build += "\t\t" + local[0] + " " + local[1] + "\n"

        build += "\tstatements:"
        for s in self.statements:
            build += ident(ident(str(s)))

        return build

@dataclass
class ASTStatement: # call, let, return, if, while
    pass

@dataclass
class ASTCallStatement(ASTStatement):
    call: ASTFuncCall

    def __str__(self):
        return "ASTCallStatement\n" + ident(str(self.call))


@dataclass
class ASTTerm:
    pass

@dataclass
class ASTFuncCall(ASTTerm):
    static: bool

    obj: ASTVarName # value='self' or another object, scope must be 'local' if self or static function
    func_name: str
    params: list[ASTExpression]

    def __str__(self):
        build = "ASTFuncCall function "
        build += "$" if self.static else "."
        build += self.func_name
        build += " on object:\n"
        build += ident(str(self.obj))
        build += "\n\tparams:\n"
        for p in self.params:
            build += ident(ident(str(p)))

        return build

@dataclass
class ASTExpression:
    # a + b - c
    #   op_count 2
    #   terms: a, b, c
    #   ops:   +,-
    terms: list[ASTTerm]
    ops: list[str]
    op_count: int = 0

    def __str__(self):
        build = "ASTExpression\n"
        if len(self.terms) == 0:
            build += "\tno terms"
            return build

        for i in range(self.op_count):
            build += ident(str(self.terms[i])) + "\n"
            build += "\tOp: " + self.ops[i]

        build += ident(str(self.terms[-1]))

        return build
            

@dataclass
class ASTIntConstant(ASTTerm):
    value: int

    def __str__(self):
        return "ASTIntConstant " +  str(self.value)

@dataclass
class ASTStringConstant(ASTTerm):
    value: str

    def __str__(self):
        return "ASTStringConstant '" + self.value + "'"

@dataclass
class ASTKeywordConstant(ASTTerm):
    value: str

    def __str__(self):
        return "ASTKeywordConstant '" + self.value + "'"

@dataclass
class ASTVarName(ASTTerm):
    value: str
    scope: str # static, local, field

    def __str__(self):
        return "ASTVarName '" + self.value + "' with scope '" + self.scope + "'"

@dataclass
class ASTArrayAccess(ASTTerm):
    var: ASTVarName
    offset: ASTExpression

    def __str__(self):
        build = "ASTArrayAccess\n"
        build += "\tname:\n"
        build += ident(ident(str(self.var))) + "\n"
        build += "\toffset:\n"
        build += ident(ident(str(self.offset)))

        return build

@dataclass
class ASTLetStatement(ASTStatement):
    left: ASTVarName | ASTArrayAccess
    right: ASTExpression

    def __str__(self):
        build = "ASTLetStatement\n"
        build += "\tleft:"  + ident(ident(str(self.left))) + "\n"
        build += "\tright:" + ident(ident(str(self.right)))

        return build


@dataclass
class ASTIfStatement(ASTStatement):
    condition: ASTExpression
    then: list[ASTStatement]
    otherwise: list[ASTStatement]

    def __str__(self):
        build = "ASTIfStatement\n"
        build += "\tcondition:\n" + ident(ident(str(self.condition))) + "\n"
        build += "\tthen:\n"
        for s in self.then:
            build += ident(ident(str(s))) + "\n"
        build += "\telse:\n"
        for s in self.otherwise:
            build += ident(ident(str(s)))

        return build

@dataclass
class ASTWhileStatement(ASTStatement):
    condition: ASTExpression
    do: list[ASTStatement]

    def __str__(self):
        build = "ASTWhileStatement\n"
        build += "\tcondition:\n" + ident(ident(str(self.condition))) + "\n"
        build += "\tdo:\n"
        for s in self.do:
            build += ident(ident(str(s))) + "\n"

        return build

@dataclass
class ASTReturnStatement(ASTStatement):
    value: ASTExpression

    def __str__(self):
        build = "ASTReturnStatement\n"
        build += ident(str(self.value))

        return build

@dataclass
class ASTUnaryOp(ASTTerm):
    op: str
    value: ASTTerm

    def __str__(self):
        build = "ASTUnaryOp op='" + self.op + "'\n"
        build += ident(str(self.value))

        return build


class Parser:
    def __init__(self, text_block):
        self.tokenizer = Tokenizer(text_block)

        self.active_class = ""

    def process(self, string):
        if not self.tokenizer.current_token == string:
            raise Exception(f"UNCAUGHT SYNTAX ERROR (line {self.tokenizer.lines}): got '{self.tokenizer.current_token}' expected '{string}'")
        if self.tokenizer.has_more_tokens():
            self.tokenizer.advance()

    def next_token(self):
        current = self.tokenizer.current_token
        self.tokenizer.advance()
        return current

    def parse_program(self) -> ASTProgram:
        program = ASTProgram([])

        self.tokenizer.advance()
        while self.tokenizer.has_more_tokens():
            program.classes.append(self.parse_class_dec())

        return program

    def parse_class_dec(self) -> ASTClass:
        c = ASTClass("", [], [], [], [])

        self.process("class")

        class_name = self.next_token()
        self.active_class = class_name
        c.name = class_name

        # parse class statics/fields
        while self.tokenizer.current_token in ["static", "field"]:
            if self.tokenizer.current_token == "static":
                c.statics.extend(self.parse_class_var_dec())
            elif self.tokenizer.current_token == "field":
                c.fields.extend(self.parse_class_var_dec())

        # expect def staticdef end
        if not self.tokenizer.current_token in ["def", "staticdef", "end"]:
            raise Exception(f"SYNTAX ERROR (line {self.tokenizer.lines}): classes must first define fields and statics then functions, instead got '{self.tokenizer.current_token}' in between the two")

        # parse functions
        while self.tokenizer.current_token in ["def", "staticdef"]:
            f = self.parse_class_func_dec()
            if f.static:
                c.static_functions.append(f)
            else:
                c.functions.append(f)

        # expect end
        if self.tokenizer.current_token != "end":
            raise Exception(f"SYNTAX ERROR (line {self.tokenizer.lines}): class must end in an 'end' after function definitions, instead got '{self.tokenizer.current_token}'")

        self.process("end")

        return c

    def parse_class_var_dec(self) -> list: # [(type, name), ... ]
        # static vs. field has been processed in Class
        # expect static field
        if not self.tokenizer.current_token in ["static", "field"]:
            raise Exception(f"SYNTAX ERROR (line {self.tokenizer.lines}): class variable definition expected 'static' or 'field' got '{self.tokenizer.current_token}'")

        self.next_token()

        # parse type, name -> [(type, name)]
        type_ = self.next_token() # int char bool or class_name (identifier)
        defs = [(type_, self.next_token())]

        # parse names
        # pasrse list (, name)* or expect ;
        if not self.tokenizer.current_token in [";", ","]:
            quote = "'"
            quotecomma = "', '"
            raise Exception(f"SYNTAX ERROR (line {self.tokenizer.lines}): each class variable definition must have format 'type' 'name' (',' 'name')* ';' instead got '{type_}' {quote if len(names)>0 else ''}{quotecomma.join(names)}{quote if len(names)>0 else ''} '{self.tokenizer.current_token}'")

        while self.tokenizer.current_token == ",":
            self.next_token()
            defs.append((type_, self.next_token()))

        # expect ;
        if not self.tokenizer.current_token == ";":
            quote = "'"
            quotecomma = "', '"
            raise Exception(f"SYNTAX ERROR (line {self.tokenizer.lines}): each class variable definition must have format 'type' 'name' (',' 'name')* ';' instead got '{type_}' {quote if len(names)>0 else ''}{quotecomma.join(names)}{quote if len(names)>0 else ''} '{self.tokenizer.current_token}'")

        self.process(";")

        return defs

    def parse_class_func_dec(self) -> ASTFunctionDec:
        # expect staticdef def
        # parse static or not
        static = False
        if self.tokenizer.current_token == "staticdef":
            static = True
        elif self.tokenizer.current_token != "def":
            raise Exception(f"SYNTAX ERROR (line {self.tokenizer.lines}): expected 'def' or 'staticdef' got {self.tokenizer.current_token}")

        # parse type, name
        self.next_token()
        type_ = self.next_token()
        name = self.next_token()

        # parse params
        # expect (
        if self.tokenizer.current_token != "(":
            raise Exception(f"SYNTAX ERROR (line {self.tokenizer.lines}): expected '(' after function declaration '{'static' if static else 'def'} {type_} {name}' instead got {self.tokenizer.current_token}")
        self.process("(")

        f = ASTFunctionDec(static, type_, name, [], [], []) 

        while self.tokenizer.current_token != ")":
            f.params.append((self.next_token(), self.next_token()))

            if not self.tokenizer.current_token in [")", ","]:
                quote = "'"
                quotecomma = "', '"
                raise Exception(f"SYNTAX ERROR (line {self.tokenizer.lines}): function parameter declarations must have format '(' 'type' 'name' (',' 'name')* ')' instead got '{quotecomma.join([i[0] + ' ' + i[1] for i in f.params])}' '{self.current_token}'")

            if self.tokenizer.current_token == ",":
                self.next_token()

        self.next_token()

        # parse local_vars
        while self.tokenizer.current_token == "local":
            f.local_vars.extend(self.parse_local_dec())

        while self.tokenizer.current_token != "end":
            f.statements.append(self.parse_statement())

        self.process("end")

        return f

    def parse_local_dec(self) -> list: # [(type, name), ...]
        self.process("local")
        
        type_ = self.next_token()
        decs = [(type_, self.next_token())]

        if not self.tokenizer.current_token in [";", ","]:
            quotecomma = "','"
            raise Exception(f"SYNTAX ERROR (line {self.tokenizer.lines}): each local variable definition must have format 'type' 'name' (',' 'name')* ';' instead got '{type_}' '{quotecomma.join(names)}' '{self.current_token}'")

        while self.tokenizer.current_token == ",":
            self.next_token()
            decs.append((type_, self.next_token()))

        # expect ;
        if not self.tokenizer.current_token == ";":
            quotecomma = "', '"
            raise Exception(f"SYNTAX ERROR (line {self.tokenizer.lines}): each local variable definition must have format 'type' 'name' (',' 'name')* ';' instead got '{self.tokenizer.current_token}' at end)")

        self.process(";")

        return decs

    def parse_statement(self) -> ASTStatement:
        if self.tokenizer.current_token == "call":
            return self.parse_call_statement()
        elif self.tokenizer.current_token == "let":
            return self.parse_let_statement()
        elif self.tokenizer.current_token == "if":
            return self.parse_if_statement()
        elif self.tokenizer.current_token == "while":
            return self.parse_while_statement()
        elif self.tokenizer.current_token == "return":
            return self.parse_return_statement()
        else:
            raise Exception(f"SYNTAX ERROR (line {self.tokenizer.lines}): statments must start with call, let, if, while, or return, instead got '{self.tokenizer.current_token}'")

    def parse_call_statement(self) -> ASTCallStatement:
        self.process("call")

        c = ASTCallStatement(self.parse_func_call())

        if self.tokenizer.current_token != ";":
            raise Exception(f"SYNTAX ERROR (line {self.tokenizer.lines}): call statements must end in a ; instead got '{self.tokenizer.current_token}'")
        self.process(";")

        return c

    # .first()
    # $first()
    # first.second()
    # first$second()
    # .first.second()
    # $first.second()
    def parse_func_call(self):
        func_name = ""
        obj = ""
        static_first = False # is the first thing static from self
        field_first = False
        static_second = False
        self_func = False # .first() | $first()

        # process obj and func_name
        # .func / .class_name
        if self.tokenizer.current_token == ".":
            field_first = True
            self.tokenizer.advance()
        # $staticfunc / $class_name
        elif self.tokenizer.current_token == "$":
            static_first = True
            self.tokenizer.advance()

        # check if this is a function of self
        # func() (invalid) / $func() / .func()
        func_name = self.next_token()
        if self.tokenizer.current_token == "(":
            # func()
            if not (field_first or static_static):
                raise Exception(f"SYNTAX ERROR (line {self.tokenizer.lines}): function calls must specify a callee with ('.' | '$') 'func_name' for self functions or 'class_name' ('.' | '$') 'func_name' for other class's functions")

            self_func = True

        # class$staticfunc
        # class.func
        # .class.func
        # $class.func
        else:
            obj = func_name

            if not self.tokenizer.current_token in ["$", "."]:
                raise Exception(f"SYNTAX ERROR (line {self.tokenizer.lines}): function calls specifing an ojbect must be in format 'obj' ('.' | '$') 'func_name' instead got format obj='{obj}' accessor='{self.tokenizer.current_token}'")

            static_second = self.next_token() == "$"
            func_name = self.next_token()

        obj_scope = "local"
        if field_first:
            obj_scope = "field"
        elif static_first:
            obj_scope = "static"

        if (field_first or static_first) and static_second:
            raise Exception(f"SYNTAX ERROR (line {self.tokenizer.lines}): static function calls can not be on field or static variables and should instead use the name of the class you are calling")
        f_call = ASTFuncCall(static_second, ASTVarName("self" if self_func else obj, obj_scope), func_name, [])

        # parse params
        if not self.tokenizer.current_token == "(":
            raise Exception(f"SYNTAX ERROR (line {self.tokenizer.lines}): function 'obj' ('.' | '$') 'func_name' '(' instead got format '{obj}' '{'$' if static_first else '.'}' '{func_name}' '{self.tokenizer.current_token}'")
        self.process("(")

        while self.tokenizer.current_token != ")":
            f_call.params.append(self.parse_expression())

            if not self.tokenizer.current_token in [")", ","]:
                raise Exception(f"SYNTAX ERROR (line {self.tokenizer.lines}): function call parameters must have format '(' 'expression' (',' 'expression')* ')' instead got (coder note: this would be really hard to write but it got some expression and then the following) '{self.current_token}'")

            if self.tokenizer.current_token == ",":
                self.next_token()

        self.process(")")

        return f_call

    def parse_expression(self) -> ASTExpression:
        e = ASTExpression([self.parse_term()], [], 0)

        while self.tokenizer.current_token in ['+', '-', '/', '*', '&', '|', '<', '>', '==']:
            op = self.next_token()
            e.ops.append(op)
            e.terms.append(self.parse_term())
            e.op_count += 1

        return e


    def parse_term(self) -> ASTTerm:
        # parse (...)
        if self.tokenizer.current_token == "(":
            self.next_token()
            e = self.parse_expression()

            # expect )
            if self.tokenizer.current_token != ")":
                raise Exception(f"SYNTAX ERROR (line {self.tokenizer.lines}): terms starting with '(' must end with ')', instead got {self.tokenizer.current_token}")
            self.process(")")

            return e

        # parse int_contant
        if self.tokenizer.token_type == TokenType.INT_CONSTANT:
            e = ASTIntConstant(self.tokenizer.int_value)
            self.next_token()

            return e

        # parse string contant
        elif self.tokenizer.token_type == TokenType.STRING_CONSTANT:
            return ASTStringConstant(self.next_token())

        # parse true, false, null
        elif self.tokenizer.current_token in ["true", "false", "null"]: # not self, can be handeld elsewhere
            return ASTKeywordConstant(self.next_token())

        # pares unary
        elif self.tokenizer.current_token in ["-", "~"]:
            return ASTUnaryOp(self.next_token(), self.parse_term())

        # assume var_name, must peak to see if next is [ or (
        scope = "local"
        if self.tokenizer.current_token == ".":
            scope = "field"
            self.tokenizer.advance()
        elif self.tokenizer.current_token == "$":
            scope = "static"
            self.tokenizer.advance()

        name = self.next_token()

        # cases from here:
        # abc
        # abc() # must have been !local (.abc())
        # abc.func()
        # abc[]

        # parse array access 'name[expression]'
        if self.tokenizer.current_token == "[":
            self.process("[")
            offset = self.parse_expression()

            # expect ]
            if self.tokenizer.current_token != "]":
                raise Exception(f"SYNTAX ERROR (line {self.tokenizer.lines}): array access terms must end in ']' instead got '{self.tokenizer.current_token}'")
            self.process("]")

            return ASTArrayAccess(ASTVarName(name, scope), offset)

        # parse self function call
        # .func() / $func()
        elif self.tokenizer.current_token == "(":
            if scope == "local":
                raise Exception(f"SYNTAX ERROR (line {self.tokenizer.lines}): function calls must be prefixed with 'object' ('.' | '$') or just simply ('.' | '$') if the function is of the current class")
            self.tokenizer.back_track()
            self.tokenizer.back_track() # go back to first . / $

            return self.parse_func_call()

        # parse other obj function call
        # myobj$func()
        # myobj.func()
        # .myobj.func()
        # $myobj.func()
        elif self.tokenizer.current_token == "." or self.tokenizer.current_token == "$":
            self.tokenizer.back_track()
            if scope != "local":
                self.tokenizer.back_track() # back to first . or $

            return self.parse_func_call()

        # simple var_name
        else: 
            return ASTVarName(name, scope)

    def parse_let_statement(self):
        self.process("let")

        scope = "local"
        if self.tokenizer.current_token == ".":
            scope = "field"
            self.tokenizer.advance()
        elif self.tokenizer.current_token == "$":
            scope = "static"
            self.tokenizer.advance()

        name = self.next_token()
        left = ASTVarName(name, scope)
        if self.tokenizer.current_token == "[":
            self.process("[")
            left = ASTArrayAccess(ASTVarName(name, scope), self.parse_expression())
            self.process("]")

        self.process("=")
        right = self.parse_expression()
        self.process(";")

        return ASTLetStatement(left, right)

    def parse_if_statement(self):
        self.process("if")
        self.process("(")
        condition = self.parse_expression()
        self.process(")")
        self.process("then")

        if_ = ASTIfStatement(condition, [], [])

        while not self.tokenizer.current_token in ["end", "else"]:
            if_.then.append(self.parse_statement())

        if self.tokenizer.current_token == "else":
            self.next_token()
            while self.tokenizer.current_token != "end":
                if_.otherwise.append(self.parse_statement())

        self.process("end")

        return if_

    def parse_while_statement(self):
        self.process("while")
        self.process("(")
        condition = self.parse_expression()
        self.process(")")
        self.process("do")

        while_ = ASTWhileStatement(condition, [])

        while self.tokenizer.current_token != "end":
            while_.do.append(self.parse_statement())

        self.process("end")

        return while_

    def parse_return_statement(self):
        self.process("return")
        val = self.parse_expression()
        self.process(";")

        return ASTReturnStatement(val)

with open("programs/langexample.rbl") as f:
    a = Parser(f.read())
    print(a.parse_program())




        

        











































