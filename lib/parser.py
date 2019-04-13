import logging

import ply.yacc as yacc

from lib.lexer import Lexer
from lib.error import CompilerError


class Parser(object):
    def p_program(self, p):
        "program : DECLARE declarations IN commands END"
        p[0] = ("program", p[2], p[4])

    def p_declarations(self, p):
        "declarations : declarations PIDENTIFIER SEMICOLON"
        id = ("long", p[2], p.lineno(2))
        p[0] = p[1] if p[1] else []
        p[0].append( id )

    def p_declarations_tab(self, p):
        "declarations : declarations PIDENTIFIER LPAREN NUMBER COLON NUMBER RPAREN SEMICOLON"
        tab = ("arr", p[2], p[4], p[6], p.lineno(2))
        p[0] = p[1] if p[1] else []
        p[0].append( tab )
    def p_declarations_empty(self, p):
        "declarations : empty"
        p[0] = []

    def p_commands(self, p):
        "commands : commands command"
        p[1].append( p[2] )
        p[0] = p[1]

    def p_commands_single(slef, p):
        "commands : command"
        p[0] = [ p[1] ]

    def p_command_assign(self, p):
        "command : identifier ASSIGN expression SEMICOLON"
        p[0] = ("assign", p[1], p[3])

    def p_command_if_then_else(self, p):
        "command : IF condition THEN commands ELSE commands ENDIF"
        p[0] = ("if_then_else", p[2], p[4], p[6])

    def p_command_if_then(self, p):
        "command : IF condition THEN commands ENDIF"
        p[0] = ("if_then", p[2], p[4])

    def p_command_while(self, p):
        "command : WHILE condition DO commands ENDWHILE"
        p[0] = ("while", p[2], p[4])

    def p_command_do(self, p):
        "command : DO commands WHILE condition ENDDO"
        p[0] = ("do_while", p[2], p[4])

    def p_command_for(self, p):
        """command : FOR PIDENTIFIER FROM value TO value DO commands ENDFOR
                   | FOR PIDENTIFIER FROM value DOWNTO value DO commands ENDFOR
        """
        p[0] = ("for_"+p[5].lower(), p[2], p[4], p[6], p[8])

    def p_command_read(self, p):
        "command : READ identifier SEMICOLON"
        p[0] = ("read",  p[2])

    def p_command_write(self, p):
        "command : WRITE value SEMICOLON"
        p[0] = ("write", p[2] )

    def p_expression_simple(self, p):
        "expression : value"
        p[0] = ("expression", p[1])

    def p_expression(self, p):
        """expression : value PLUS value
                      | value MINUS value
                      | value ASTERISK value
                      | value SLASH value
                      | value PERCENT value
        """
        p[0] = ("expression", p[2], p[1], p[3])

    def p_condition(self, p):
        """condition : value EQUAL value
                     | value NEQUAL value
                     | value LESS value
                     | value MORE value
                     | value LESSEQ value
                     | value MOREEQ value
        """
        p[0] = ("condition", p[2], p[1], p[3])

    def p_value_num(slef, p):
        """value : NUMBER
                 | identifier
        """
        p[0] = p[1]

    def p_identifier(self, p):
        "identifier : PIDENTIFIER"
        p[0] = ("long", p[1], p.lineno(1))

    def p_identifier_tab(self, p):
        "identifier : PIDENTIFIER LPAREN PIDENTIFIER RPAREN"
        p[0] = ("arr", p[1], p[3], p.lineno(1))

    def p_identifier_tab_access(self, p):
        "identifier : PIDENTIFIER LPAREN NUMBER RPAREN"
        p[0] = ("arr", p[1], p[3], p.lineno(1))

    def p_error(self, p):
        logging.error(f"Syntax error '{p.value}' in line {p.lineno}")
        raise CompilerError()

    def p_empty(self, p):
        "empty :"
        p[0] = None

    def __init__(self):
        self.lexer = Lexer()
        self.tokens = self.lexer.tokens
        self.parser = yacc.yacc(module=self, write_tables=0, debug=False)

    def parse(self, data):
        if data:
            return self.parser.parse(data, self.lexer.lexer, 0, 0, None)
        else:
            logging.error("Input file is empty")
            raise CompilerError()


