from lib.utils import is_variable, is_arr, is_number, is_declared_var


class MachineCode(object):
    def __init__(self):
        self.code = []
        self.memory = {}
        self.mem_id = 0
        self.regs = [None for _ in range(8)]
        self.regsnames = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']

        # next statement counter
        self.k = 0

        self.labels = {}
        self.symtab = []

    def start(self, cfg, symtab):
        self.symtab = symtab
        self.reserve_memory(symtab)

        self.generate(cfg)

        return self.parse_code()

    def parse_code(self):
        new = []
        linee = []
        for line in self.code:
            for s in line.split():
                if s in self.labels:
                    s = str(self.labels[s])
                linee.append(s)
            linee = ' '.join(linee)
            new.append(linee)
            linee = []

        return '\n'.join(new)

    def reserve_memory(self, symtab):
        for iden in symtab:
            if is_variable(iden):
                self.memory[iden[1]] = self.mem_id
                self.mem_id += 1

        for iden in symtab:
            if is_arr(iden):
                self.memory[iden[1]] = self.mem_id
                self.mem_id += iden[3] - iden[2] + 1

    def generate(self, cfg):
        for node in cfg:
            getattr(self, 'gen_' + node[0])(node)

        self.push('HALT')

    def gen_read(self, node):
        _, iden = node
        if is_variable(iden):
            self.read_variable(iden)
        elif is_arr(iden):
            self.read_array(iden)

    def read_variable(self, iden):
        self.push('GET  {}'.format(1))
        self.store_var(iden, 1)

    def read_array(self, iden):
        _, name, sub_iden, _ = iden
        if is_number(sub_iden):
            offset = sub_iden + self.arr_offset(iden)
            self.gen_number(offset)
            self.push('''
            GET     {}
            STORE   {}
            '''.format(1, 1))
        elif is_declared_var(sub_iden, self.symtab):
            offset = self.arr_offset(iden)
            self.gen_number(offset, 2)
            inner_reg = self.loaddd(sub_iden, 3)
            self.push('''
            SUB     0   0
            ADD     0   2
            ADD     0   3
            GET     1
            STORE   1
            ''')

    def arr_offset(self, arr):
        start = 0
        for iden in self.symtab:
            if iden[1] == arr[1]:
                start = iden[2]
                break

        return self.memory[arr[1]] - start

    def store_var(self, iden, src):
        pos_in_mem = self.memory[iden[1]]
        self.gen_number(pos_in_mem, 0)
        self.push('STORE {}'.format(src))
        self.regs[src] = None

    def gen_write(self, node):
        _, iden = node
        if is_variable(iden):
            self.write_variable(iden)
        elif is_number(iden):
            self.write_number(iden)
        elif is_arr(iden):
            self.write_arr(iden)

    def write_variable(self, iden):
        reg = self.loaddd(iden, 2)
        self.push('PUT {}'.format(reg))

    def write_number(self, iden):
        self.gen_number(iden, 0)
        self.push('PUT {}'.format(0))

    def write_arr(self, iden):
        _, name, inner, _ = iden
        if is_number(inner):
            offset = inner + self.arr_offset(iden)
            self.gen_number(offset)
            self.push('''
                    LOAD {}
                    PUT {}
                    '''.format(1, 1))
            return
        elif is_declared_var(inner, self.symtab):
            self.loaddd(inner, 2)
            offset = self.arr_offset(iden)
            self.gen_number(offset, 3)
            self.push('''
            SUB     0   0
            ADD     0   2
            ADD     0   3
            LOAD    1
            PUT     1
            ''')

    def gen_assign(self, node):
        _, iden, expr = node
        if len(expr) == 2:
            self.assign_simple_expr(iden, expr)
        else:
            _, op, left, right = expr
            func_map = {
                '+': self.assign_plus,
                '-': self.assign_minus,
                '*': self.assign_mul,
                '/': self.assign_div,
                '%': self.assign_mod,
            }
            func_map[op](iden, left, right)

    def assign_plus(self, trg_iden, left, right):
        if is_arr(trg_iden):
            l_reg = self.loaddd(left, 2)
            r_reg = self.loaddd(right, 3)
            self.push('''
            ADD     {l}  {r}
            '''.format(l=l_reg, r=r_reg))
            self.store_arr(trg_iden, l_reg)
            return

        l_reg = self.loaddd(left, 2)
        r_reg = self.loaddd(right, 3)
        self.push('''
        ADD     {l}  {r}
        '''.format(l=l_reg, r=r_reg))
        self.store_var(trg_iden, l_reg)

    def assign_simple_expr(self, trg_iden, expr):
        _, right = expr
        if is_arr(trg_iden):
            val_reg = self.loaddd(right, 3)
            self.loaddd(trg_iden[2], 2)
            self.gen_number(self.arr_offset(trg_iden))
            self.push('''
            ADD     {a}  {inner}
            STORE   {val}
            '''.format(a=0, inner=2, val=val_reg))
            return

        val_reg = self.loaddd(right, 1)
        self.store_var(trg_iden, 1)

    def assign_minus(self, trg_iden, left, right):
        l_reg = self.loaddd(left, 2)
        r_reg = self.loaddd(right, 3)

        self.push('''
        SUB     {l}     {r}
        '''.format(l=l_reg, r=r_reg))

        if is_arr(trg_iden):
            self.store_arr(trg_iden, l_reg)
        elif is_variable(trg_iden):
            self.store_var(trg_iden, l_reg)

    def assign_mul(self, trg_iden, left, right):
        res_reg = 4
        l_reg = self.loaddd(left, 2)
        r_reg = self.loaddd(right, 3)
        code = '''
        SUB     {res}   {res}
        JZERO   {r}     ${end}
        JODD	{l}	    ${add}
        JUMP	${half}
        ADD	    {res}	{r}
        HALF	{l}
        ADD     {r}     {r}
        JUMP	${jzero}
        '''.format(res=res_reg, r=r_reg, l=l_reg,
                   add=2, half=2,
                   end=7, jzero=(-6))
        self.push(code)

        if is_arr(trg_iden):
            self.store_arr(trg_iden, res_reg)
        elif is_variable(trg_iden):
            self.store_var(trg_iden, res_reg)

    def assign_div(self, trg_iden, left, right):
        l_reg = self.loaddd(left, 2)
        r_reg = self.loaddd(right, 3)
        res_reg = 4
        divide = '''
        JZERO   {r}   ${end}
        COPY    1       {r}
        COPY    {res}   1
        SUB     {res}   {l}
        JZERO   {res}   ${body}
        JUMP    ${out}
        ADD     1       1
        JUMP    ${loop}
        SUB     {res}   {res}
        COPY    0       1
        SUB     0       {l}
        JZERO   0       ${add}
        ADD     {res}   {res}
        HALF    1
        JUMP    ${check}
        ADD     {res}   {res}
        INC     {res}
        SUB     {l}     1
        HALF    1
        COPY    0       {r}
        SUB     0       1
        JZERO   0       ${loop2}
        JUMP    ${out2}
        SUB     {l}     {l}
        SUB     {res}   {res}
        '''.format(res=res_reg, l=l_reg, r=r_reg,
                   end=23, body=2, out=3, loop=-5,
                   add=4, check=5, loop2=-12, out2=3)

        self.push(divide)
        if is_arr(trg_iden):
            self.store_arr(trg_iden, res_reg)
        elif is_variable(trg_iden):
            self.store_var(trg_iden, res_reg)

    def assign_mod(self, trg_iden, left, right):
        l_reg = self.loaddd(left, 2)
        r_reg = self.loaddd(right, 3)
        res_reg = 4
        divide = '''
        COPY    {res}   {l}     
        JZERO   {r}     ${end}
        COPY    1       {r}
        COPY    {res}   1
        SUB     {res}   {l}
        JZERO   {res}   ${body}
        JUMP    ${out}
        ADD     1       1
        JUMP    ${loop}
        SUB     {res}   {res}
        COPY    0       1
        SUB     0       {l}
        JZERO   0       ${add}
        ADD     {res}   {res}
        HALF    1
        JUMP    ${check}
        ADD     {res}   {res}
        INC     {res}
        SUB     {l}     1
        HALF    1
        COPY    0       {r}
        SUB     0       1
        JZERO   0       ${loop2}
        JUMP    ${out2}
        SUB     {l}     {l}
        SUB     {res}   {res}
        '''.format(res=res_reg, l=l_reg, r=r_reg,
                   end=23, body=2, out=3, loop=-5,
                   add=4, check=5, loop2=-12, out2=3)
        self.push(divide)
        if is_arr(trg_iden):
            self.store_arr(trg_iden, l_reg)
        elif is_variable(trg_iden):
            self.store_var(trg_iden, l_reg)

    def gen_if_goto(self, node):
        _, cond, label = node
        _, op, left, right = cond
        _, lbl = label  # przekaza sam lbl
        func_map = {
            '=': self.eq,
            '!=': self.neq,
            '<': self.less,
            '>': self.more,
            '<=': self.less_eq,
            '>=': self.more_eq,
        }
        func_map[op](left, right, lbl)

    def eq(self, left, right, label):
        if is_number(left) and is_number(right):
            if left == right:
                self.push('JUMP     {}'.format(label))
            else:
                return

        l_reg = self.loaddd(left, 2)
        r_reg = self.loaddd(right, 3)

        self.push('''
        COPY    0   {l}
        COPY    1   {r}
        SUB     0   {r}
        JZERO   0   ${sub}
        JUMP    ${end}
        SUB     1   {l}
        JZERO   1   {lbl}
        '''.format(l=l_reg, r=r_reg, lbl=label,
                   end=3, sub=2))

    def neq(self, left, right, label):
        if is_number(left) and is_number(right):
            if left != right:
                self.push('JUMP     {}'.format(label))
            else:
                return

        l_reg = self.loaddd(left, 2)
        r_reg = self.loaddd(right, 3)

        self.push('''
        COPY    0   {l}
        COPY    1   {r}
        SUB     0   {r}
        JZERO   0   ${sub}
        JUMP    {lb}
        SUB     1   {l}
        JZERO   1   ${end}
        JUMP    {lb}
        '''.format(l=l_reg, r=r_reg, lb=label,
                   end=2, sub=2))

    def less(self, left, right, label):
        self.more(right, left, label)

    def more(self, left, right, label):
        l_reg = self.loaddd(left, 2)
        r_reg = self.loaddd(right, 3)

        code = '''
        SUB     {l}     {r}
        JZERO   {l}     ${body}
        JUMP    {lbl}
        '''.format(l=l_reg, r=r_reg, body=2,
                   lbl=label)
        self.push(code)

    def less_eq(self, left, right, label):
        if is_number(left) and is_number(right):
            if left <= right:
                self.push('JUMP lbl'.format(lbl=label))
                return

        l_reg = self.loaddd(left, 2)
        r_reg = self.loaddd(right, 3)

        self.push('SUB {l} {r}'.format(l=l_reg, r=r_reg))
        self.push('JZERO {l} {lb}'.format(l=l_reg, lb=label))

    def more_eq(self, left, right, label):
        # Just swithing operands
        self.less_eq(right, left, label)

    def gen_cond(self, node, label):
        _, op, left, right = node

    def gen_goto(self, node):
        _, label = node
        _, lbl = label
        self.push('JUMP {}'.format(lbl))

    def gen_label(self, node):
        _, label = node
        self.labels[label] = self.k

    def store_arr(self, iden_arr, val_reg):
        _, name, inner, _ = iden_arr
        if is_number(inner):
            offset = inner + self.arr_offset(iden_arr)
            self.gen_number(offset)
            self.push('STORE {}'
                      .format(val_reg))
            return
        elif is_declared_var(inner, self.symtab):
            inner_reg = self.check_in_regs(inner)
            if not inner_reg:
                inner_mem_id = self.memory[inner]
                self.gen_number(inner_mem_id, 0)
                self.push('''
                LOAD    1
                ''')
                offset = self.arr_offset(iden_arr)
                self.gen_number(offset, 0)
                self.push('''
                ADD     0   1
                STORE   {}
                '''.format(val_reg))
                return
            else:
                offset = self.arr_offset(iden_arr)
                self.gen_number(offset, 0)
                self.push('''
                        ADD     {}  {}
                        STORE   {}
                        '''.format(0, inner_reg, val_reg))
                return

    def loaddd(self, iden, trg_reg):
        if is_number(iden):
            self.gen_number(iden, trg_reg)
            return trg_reg
        elif is_variable(iden):
            iden_reg = self.check_in_regs(iden[1])
            if not iden_reg:
                iden_mem_id = self.memory[iden[1]]
                self.gen_number(iden_mem_id)
                self.push('LOAD {}'
                          .format(trg_reg))
            else:
                self.push('COPY {} {}'
                          .format(trg_reg, iden_reg))
            return trg_reg
        elif is_arr(iden):
            _, name, inner, _ = iden
            if is_number(inner):
                offset = inner + self.arr_offset(iden)
                self.gen_number(offset)
                self.push('LOAD {}'
                          .format(trg_reg))
                return trg_reg
            elif is_declared_var(inner, self.symtab):
                inner_reg = self.check_in_regs(inner)
                if not inner_reg:
                    inner_mem_id = self.memory[inner]
                    self.gen_number(inner_mem_id, 0)
                    self.push('''
                    LOAD    1
                    ''')
                    offset = self.arr_offset(iden)
                    self.gen_number(offset, 0)
                    self.push('''
                    ADD     0   1
                    LOAD    {}
                    '''.format(trg_reg))
                    return trg_reg
                else:
                    offset = self.arr_offset(iden)
                    self.gen_number(offset, 0)
                    self.push('''
                    ADD {} {}
                    LOAD {}
                    '''.format(0, inner_reg, trg_reg))
                    return trg_reg
        elif is_declared_var(iden, self.symtab):
            iden_reg = self.check_in_regs(iden)
            if not iden_reg:
                iden_mem_id = self.memory[iden]
                self.gen_number(iden_mem_id)
                self.push('LOAD {}'
                          .format(trg_reg))
            else:
                self.push('COPY {} {}'
                          .format(trg_reg, iden_reg))
            return trg_reg

            pass

    def loadd(self, var):
        if is_number(var):
            reg = self.get_free_reg()
            self.gen_number(var, reg)
            return reg
        elif is_variable(var):
            reg = self.check_in_regs(var[1])
            if not reg:
                reg = self.load(var)
            return reg

    def load(self, iden):
        if is_variable(iden):
            pos_in_mem = self.memory[iden[1]]
            self.gen_number(pos_in_mem)
            dst_reg = self.get_reg(iden[1])
            self.push('LOAD reg', reg=dst_reg)
            self.regs[dst_reg] = iden[1]
            return dst_reg
        else:
            pass

    def check_in_regs(self, varname):
        if isinstance(varname, tuple):
            varname = varname[1]

        if varname in self.regs:
            return self.regs.index(varname)
        return None

    def get_var(self, iden_node, reg):
        _, name, _ = iden_node
        if name in self.regs:
            return self.regs.index(name)

        mem_id = self.memory[name]
        self.gen_number(mem_id)
        self.push('LOAD {}'.format(reg))
        self.regs[reg] = name
        return reg

    def get_free_reg(self, iden):
        if None in self.regs[5:]:
            reg_id = self.regs[5:].index(None)
            self.regs[reg_id + 5] = iden[1]
            return reg_id + 5

    def get_reg(self, var):
        if isinstance(var, tuple):
            var = var[1]

        if var in self.regs:
            return self.regs.index(var)
        elif None in self.regs[4:]:
            reg_id = self.regs[4:].index(None)
            self.regs[reg_id + 4] = var
            return reg_id + 4
        else:
            self.store(self.regs[4], 4)
            self.regs[4] = var
            return 4

    def store(self, id_name, id_reg):
        print('STORE')
        pos_in_mem = self.memory[id_name]
        self.gen_number(pos_in_mem)
        self.push('''
        STORE   {}
        '''.format(id_reg))
        self.regs[id_reg] = None

    def push_code(self, code):
        if isinstance(code, list):
            self.code.extend(code)
        elif isinstance(code, str):
            self.code.append(code)

    def push(self, code, **kwargs):
        intmap = ['0', '1', '2', '3', '4', '5', '6', '7']
        code = code.strip()
        code = [c.strip() for c in code.split('\n') if c]
        linee = []
        for line in code:
            for s in line.split():
                if s in intmap:
                    s = self.regsnames[int(s)]
                elif s.startswith('$'):
                    s = str(int(s[1:]) + self.k)
                linee.append(s)
            self.code.append(' '.join(linee))
            linee.clear()
            self.k += 1

    def gen_number(self, number, reg=0):
        code = []
        code.append('SUB {} {}'.format(reg, reg))

        if number != 0:
            code.append('INC {}'.format(reg))
            number = bin(number)[3:]
            for digit in number:
                code.append('ADD {} {}'.format(reg, reg))
                if digit == '1':
                    code.append('INC {}'.format(reg))

        self.push('\n'.join(code))
