from collections import namedtuple

Identifier = namedtuple('Identifier', ['type', 'name', 'inner'])


class ControlFlowGraph(object):
    def __init__(self):
        self.cfg = []
        self.curr_label = 0
        self.symtab = []

    def next_label(self):
        self.curr_label += 1
        return ('label', '@' + str(self.curr_label))

    def convert(self, commands, symtab):
        self.symtab = symtab
        self.generate(commands)
        return self.cfg

    def generate(self, commands):
        for cmd in commands:
            getattr(self, 'cfg_' + cmd[0])(cmd)

    def to_namedtuple(self, iden):
        if len(iden) == 1:
            return iden
        elif len(iden) == 3:
            return Identifier(iden[0], iden[1], None)
        elif len(iden) == 4:
            return Identifier(iden[0], iden[1], iden[2])

    def cfg_read(self, cmd):
        self.cfg.append(cmd)

    def cfg_write(self, cmd):
        self.cfg.append(cmd)

    def cfg_if_then_else(self, cmd):
        _, cond, body_t, body_f = cmd
        l_end = self.next_label()
        l_false = self.next_label()

        neg_cond_check = self.goto_if(self.neg_cond(cond), l_false)
        self.cfg.append(neg_cond_check)
        self.generate(body_t)
        self.cfg.append(self.goto(l_end))
        self.cfg.append(l_false)
        self.generate(body_f)
        self.cfg.append(l_end)

    def cfg_do_while(self, cmd):
        _, body, cond = cmd
        l_start_loop = self.next_label()
        l_end_loop = self.next_label()

        self.cfg.append(l_start_loop)
        self.generate(body)

        cond_check = self.goto_if(self.neg_cond(cond), l_end_loop)
        self.cfg.append(cond_check)

        self.cfg.append(self.goto(l_start_loop))
        self.cfg.append(l_end_loop)

    def cfg_while(self, cmd):
        _, cond, body = cmd
        l_start_loop = self.next_label()
        l_end_loop = self.next_label()

        self.cfg.append(l_start_loop)

        cond_checking = self.goto_if(self.neg_cond(cond), l_end_loop)
        self.cfg.append(cond_checking)

        self.generate(body)

        self.cfg.append(self.goto(l_start_loop))
        self.cfg.append(l_end_loop)

    def cfg_for_to(self, cmd):
        _, it, start, end, body = cmd
        iterator = ('long', it, None)
        self.symtab.append(iterator[:-1])

        iterator_end = ('long', it + '_end', None)
        self.symtab.append(iterator_end[:-1])

        iter_assign = ('assign', iterator, ('expression', start))
        iter_inc = ('assign', iterator, ('expression', '+', iterator, 1))
        end_iter_assign = ('assign', iterator_end, ('expression', end))

        l_start = self.next_label()
        l_end = self.next_label()

        self.cfg_assign(iter_assign)
        self.cfg_assign(end_iter_assign)

        self.cfg.append(l_start)

        cond_check = ('condition', '>', iterator, iterator_end)
        self.cfg.append(self.goto_if(cond_check, l_end))

        self.generate(body)

        self.cfg_assign(iter_inc)
        self.cfg.append(self.goto(l_start))
        self.cfg.append(l_end)

    def cfg_for_downto(self, cmd):
        _, it, start, end, body = cmd
        iterator = ('long', it, None)
        self.symtab.append(iterator[:-1])

        iterator_end = ('long', it + '_end', None)
        self.symtab.append(iterator_end[:-1])

        iter_assign = ('assign', iterator, ('expression', start))
        iter_dec = ('assign', iterator, ('expression', '-', iterator, 1))
        end_iter_assign = ('assign', iterator_end, ('expression', end))

        l_start = self.next_label()
        l_end = self.next_label()

        self.cfg_assign(iter_assign)
        self.cfg_assign(end_iter_assign)

        cond_check = ('condition', '<', iterator, iterator_end)
        self.cfg.append(self.goto_if(cond_check, l_end))

        self.cfg.append(l_start)

        self.generate(body)

        zero_check = ('condition', '<=', iterator, iterator_end)
        self.cfg.append(self.goto_if(zero_check, l_end))

        self.cfg_assign(iter_dec)
        self.cfg.append(self.goto(l_start))

        self.cfg.append(l_end)

    def cfg_if_then(self, cmd):
        _, cond, body = cmd
        l_end = self.next_label()

        cond_check = self.goto_if(self.neg_cond(cond), l_end)
        self.cfg.append(cond_check)
        self.generate(body)
        self.cfg.append(l_end)

    def cfg_assign(self, node):
        self.cfg.append(node)

    def neg_cond(self, cmd):
        type, op, left, right = cmd
        neg_map = {
            '=': '!=',
            '!=': '=',
            '<': '>=',
            '>': '<=',
            '<=': '>',
            '>=': '<',
        }
        return (type, neg_map[op], left, right)

    def goto_if(self, cond, label):
        return ('if_goto', cond, label)

    def goto(self, label):
        return ('goto', label)
