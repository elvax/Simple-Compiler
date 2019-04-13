import logging

import ply.lex as lex

from lib.error import CompilerError


class Lexer(object):
    tokens = (
        'NUMBER',
        'PIDENTIFIER',
        'PLUS',
        'MINUS',
        'ASTERISK',
        'SLASH',
        'PERCENT',
        'EQUAL',
        'NEQUAL',
        'LESS',
        'MORE',
        'LESSEQ',
        'MOREEQ',
        'READ',
        'WRITE',
        'ASSIGN',
        'SEMICOLON',
        'COLON',
        'DECLARE',
        'IN',
        'END',
        'IF',
        'THEN',
        'ELSE',
        'ENDIF',
        'FOR',
        'FROM',
        'TO',
        'DOWNTO',
        'ENDFOR',
        'WHILE',
        'DO',
        'ENDWHILE',
        'ENDDO',
        'LPAREN',
        'RPAREN',
    )

    t_PIDENTIFIER = r'[_a-z]+'
    t_PLUS = r'\+'         
    t_MINUS = r'\-'         
    t_ASTERISK = r'\*'         
    t_SLASH = r'/'         
    t_PERCENT = r'%'         
    t_EQUAL = r'='         
    t_NEQUAL = r'!='        
    t_LESS = r'<'         
    t_MORE = r'>'         
    t_LESSEQ = r'<='        
    t_MOREEQ = r'>='        
    t_READ = r'READ'      
    t_WRITE = r'WRITE'     
    t_ASSIGN = r':='        
    t_SEMICOLON = r';'  
    t_COLON = r':'       
    t_DECLARE = r'DECLARE'   
    t_IN = r'IN'        
    t_END = r'END'       
    t_IF = r'IF'        
    t_THEN = r'THEN'      
    t_ELSE = r'ELSE'      
    t_ENDIF = r'ENDIF'     
    t_FOR = r'FOR'       
    t_FROM = r'FROM'      
    t_TO = r'TO'        
    t_DOWNTO = r'DOWNTO'    
    t_ENDFOR = r'ENDFOR'    
    t_WHILE = r'WHILE'     
    t_DO = r'DO'        
    t_ENDWHILE = r'ENDWHILE'  
    t_ENDDO = r'ENDDO'  
    t_LPAREN = r'\('
    t_RPAREN = r'\)'   
    t_ignore  = ' \t'

    def t_NUMBER(self, t):
        r'[0-9]+'
        t.value = int(t.value)
        return t

    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)

    def t_comment(self, t):
        r'\[[^\]]*\]'
        pass

    def t_error(self, t):
        logging.error(f'Illegal character {t.value[0]} in line {t.lineno}')
        raise CompilerError()

    def __init__(self, **kwargs):
        self.lexer = lex.lex(module=self, **kwargs)
        
    def tokenize(self, data):
        self.lexer.input(data)
        while True:
            tok = self.lexer.token()
            if not tok:
                break
            else:
                yield tok

    def test(self, data):
        self.lexer.input(data)
        while True:
            tok = self.lexer.token()
            if not tok:
                break
            else:
                logging.error('Lexer error')
                raise CompilerError()
