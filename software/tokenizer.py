from enum import Enum

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

            if len(self.text_block) > 1 and self.text_block[0:2] == ">>":
                self.advance_char()
                self.advance_char()

                self.symbol = ">>"
                self.current_token = ">>"
                self.tokens.append(self.current_token)
                self.current_token_i += 1
                return

            if len(self.text_block) > 1 and self.text_block[0:2] == "<<":
                self.advance_char()
                self.advance_char()

                self.symbol = "<<"
                self.current_token = "<<"
                self.tokens.append(self.current_token)
                self.current_token_i += 1
                return

            if len(self.text_block) > 2 and self.text_block[0:2] == ">>>":
                self.advance_char()
                self.advance_char()
                self.advance_char()

                self.symbol = ">>>"
                self.current_token = ">>>"
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
