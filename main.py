#!/usr/bin/python3

import argparse

from lib.parser import Parser
from lib.analyser import Analyser
from lib.control_flow_graph import ControlFlowGraph
from lib.error import CompilerError
from lib.machine_code import MachineCode


def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file',
                        help='path file with code to compile')
    parser.add_argument('output_file',
                        help='path to file with machine code (default ./a.mr)',
                        default='a.mr')
    return parser.parse_args()

def main():
    args = arg_parser()

    parser = Parser()
    flow = ControlFlowGraph()
    analyser = Analyser()
    codegen = MachineCode()

    with open(args.input_file, 'r') as file_in:
        content = file_in.read()

    try:
        tree = parser.parse(content)
        symtab, commands = analyser.analyse(tree)
        g = flow.convert(commands, symtab)
        code = codegen.start(g, symtab)
    except CompilerError:
        exit(1)

    with open(args.output_file, 'w') as file_out:
        file_out.write(code)

    
if __name__ == '__main__':
    main()

