import logging

from lib.error import CompilerError
from lib.utils import is_number


class Analyser(object):
    def __init__(self):
        self.declared = []
        self.initialized = {}
        self.tmp_vars = []
        self.symtab = []

    def analyse(self, parse_tree):
        declarations = parse_tree[1]
        commands = parse_tree[2]

        self.declared = self.check_declarations(declarations)
        self.check_commands(commands)

        return self.symtab, commands

    def check_declarations(self, declarations):
        """Checks for multiple declarations of the same pids
        and range of arrays.
        If no errors then return list with declared pids
        """
        # Checking for multiple declarations
        declared = []
        doubled = []
        for pid in declarations:
            if pid[1] not in declared:
                declared.append(pid[1])
                self.symtab.append(pid[:-1])
            else:
                doubled.append(pid)

        if doubled:
            for pid in doubled:
                logging.error('Double declaration "{}" in line {}'
                              .format(pid[1], pid[-1]))
            raise CompilerError()

        # Checkig arrays ranges
        for pid in declarations:
            if pid[0] == 'arr':
                if pid[2] > pid[3]:
                    logging.error('Array "{}" in line {} has wrong ranges'
                                  .format(pid[1], pid[-1]))
                    raise CompilerError()

        return declared

    def check_pid(self, pid):
        if is_number(pid):
            return
        if pid[1] in self.tmp_vars:
            return

        if pid[1] not in self.declared:
            logging.error('Variable "{}" not declared, line {}'
                          .format(pid[1], pid[-1]))
            raise CompilerError()

        if pid[0] == 'arr':
            if is_number(pid[2]):
                return
            if pid[2] in self.tmp_vars:
                return
            if pid[2] not in self.declared:
                logging.error('Variable "{}" not declared, line {}'
                              .format(pid[2], pid[-1]))
                raise CompilerError()

        for iden in self.symtab:
            if iden[1] == pid[1]:
                if iden[0] != pid[0]:
                    logging.error('Wrong "{}" has another type, line {}'
                                  .format(pid[1], pid[-1]))
                    raise CompilerError()

    def check_commands(self, commands):
        for cmd in commands:
            getattr(self, 'check_' + cmd[0])(cmd)

    def check_read(self, node):
        _, pid = node
        if is_number(pid):
            return

        self.check_pid(pid)
        self.initialized[pid[1]] = True

    def check_write(self, node):
        _, pid = node
        if is_number(pid):
            return

        self.check_pid(pid)
        self.check_initialization(pid)

    def check_initialization(self, pid):
        if is_number(pid):
            return
        if pid[1] in self.tmp_vars:
            return

        if pid[1] not in self.initialized:
            logging.error('Using uninitialized variable "{}" in line {}'
                          .format(pid[1], pid[-1]))
            raise CompilerError()

    def check_while(self, node):
        _, cond, body = node
        self.check_condition(cond)
        self.check_commands(body)

    def check_do_while(self, node):
        _, body, cond = node
        self.check_while((_, cond, body))

    def check_condition(self, node):
        _, _, left, right = node

        self.check_pid(left)
        self.check_pid(right)
        self.check_initialization(left)
        self.check_initialization(right)

    def check_if_then_else(self, node):
        _, cond, true_b, false_b = node

        self.check_condition(cond)
        self.check_commands(true_b)
        self.check_commands(false_b)

    def check_if_then(self, node):
        _, cond, body = node

        self.check_condition(cond)
        self.check_commands(body)

    def check_assign(self, node):
        _, iden, exp = node

        self.check_pid(iden)
        self.check_expression(exp)
        self.initialized[iden[1]] = True

    def check_expression(self, node):
        if len(node) == 4:
            _, _, left, right = node
            self.check_pid(left)
            self.check_pid(right)
            self.check_initialization(left)
            self.check_initialization(right)
        else:
            _, value = node
            self.check_pid(value)
            self.check_initialization(value)

    def check_for_to(self, node):
        _, iterator, start, end, body = node
        self.tmp_vars.append(iterator)

        self.check_pid(start)
        self.check_pid(end)
        self.check_initialization(start)
        self.check_initialization(end)

        self.check_commands(body)

        self.tmp_vars.remove(iterator)

    def check_for_downto(self, node):
        self.check_for_to(node)
