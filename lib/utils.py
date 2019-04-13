def is_number(pid):
    return isinstance(pid, int)

def is_variable(iden):
    if isinstance(iden, tuple):
        return iden[0] == 'long'
    
    return False

def is_arr(iden):
    if isinstance(iden, tuple):
        return iden[0] == 'arr'
    return False

def is_declared_var(iden, symtab=None):
    if symtab:
        for id in symtab:
            if id[1] == iden and id[0] == 'long':
                return True
    return False