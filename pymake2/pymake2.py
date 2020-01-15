#! /usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

__author__ = 'Saud Wasly'

import argparse
import re
from typing import Dict

try:
    pass
    import argcomplete
except ImportError:
    print('Warning: Autocomplete is not working\nYou need to install argcomplete package')

import os
import sys
import traceback

try:
    import utility as util
    import make
    from makefile_template import gccTemplate
except:
    from pymake2 import utility as util
    from pymake2 import make
    from pymake2.makefile_template import gccTemplate

debug = False
highlight_errors = False
highlight_warnings = False

fd_out = None  # used to bash auto complete only


class ArgsT:
    t = 'all'
    f = None
    j = 1


class TargetT(object):
    def __init__(self, func, args, makefile_m):
        self.Name = func
        self.func = getattr(makefile_m, func)
        args_str = [item.strip() for item in args.split(',')]
        args_var = [getattr(makefile_m, item) for item in args_str if item != '']
        self.args_str = args_str
        self.args_var = args_var
        self.MakefileM = makefile_m
        self.Dependencies = args_var

    def check_dependencies(self):
        if len(self.Dependencies) == 0:
            return True

        util.print_color('Dependency checking of Target "%s"' % self.Name, util.tty_colors_cmds.On_Cyan)
        for i, item in enumerate(self.Dependencies):
            if type(item) is list:
                for sub_item in item:  # assumed to be list of file names (paths)
                    if not os.path.isfile(sub_item):
                        util.write_color('Dependency Error @ Target "%s": ' % self.Name, util.tty_colors_cmds.BRed)
                        print('%s does not exist!' % sub_item)
                        return False
            elif type(item) is str:
                if not os.path.isfile(item):
                    util.write_color('Dependency Error @ Target "%s": ' % self.Name, util.tty_colors_cmds.BRed)
                    print('%s does not exist!' % item)
                    return False
            elif type(item) is TargetT:  # another target
                if not item.run():
                    util.write_color('Dependency Error @ Target "%s": ' % self.Name, util.tty_colors_cmds.BRed)
                    print('Target "%s" failed' % item.Name)
                    return False

        return True

    def run(self):
        if self.check_dependencies():
            util.print_color('Executing Target "%s"' % self.Name, util.tty_colors_cmds.On_Cyan)
            try:
                if len(self.args_var) == 0:
                    ret_v = self.func()
                else:
                    ret_v = self.func(*self.args_var)

                if not ret_v:
                    util.print_color('Target "%s" failed' % self.Name, util.tty_colors_cmds.BRed)
                return ret_v
            except:
                util.print_color('Internal error in the target function "%s"' % self.Name, util.tty_colors_cmds.BRed)
                if debug:
                    traceback.print_exc()

        else:
            return False


def decode_line(line: bytes):
    return line.decode('utf-8')


def encode_line(line: str):
    return line.encode('utf-8')


def parse_makefile(makefile_path, makefile_m):
    targets = {}  # type: dict[str, TargetT]
    if os.path.isfile(makefile_path):
        f = open(makefile_path, 'rb')
        makefile_str = f.read()
        f.close()
        makefile_lines = makefile_str.splitlines()

        for i, l in enumerate(map(decode_line, makefile_lines)):
            if l.startswith('@target'):
                next_makefile_lines = decode_line(makefile_lines[i + 1])
                target_func = re.findall(r'def\s+(\w+)\s*\(', next_makefile_lines)
                target_func = target_func[0]
                target_args = re.findall(r'def\s+\w+\s*\((.*)\)', next_makefile_lines)
                target_args = target_args[0]
                target_v = TargetT(target_func, target_args, makefile_m)
                targets[target_func] = target_v

        # Detect Dependencies
        for key in targets.keys():
            tar_item = targets[key]
            for i, item in enumerate(tar_item.Dependencies):
                if callable(item):
                    dep_target_str = tar_item.args_str[i]
                    dep_target = targets[dep_target_str]
                    tar_item.Dependencies[i] = dep_target

    return targets


def get_targets_for_bash_autocomplete(makefile_path=''):
    targets = []
    if makefile_path == '':
        makefile_path = './makefile.py'
    if os.path.isfile(makefile_path):
        f = open(makefile_path, 'rb')
        makefile_str = f.read()
        f.close()
        makefile_lines = makefile_str.splitlines()
        for i, l in enumerate(map(decode_line, makefile_lines)):
            if l.startswith('@target'):
                next_makefile_lines = decode_line(makefile_lines[i + 1])
                res_v = re.findall(r'def\s+(\w+)\s*\(', next_makefile_lines)
                targets.append(res_v[0])
    return targets


def auto_target():
    if os.path.isfile('./makefile.py'):
        return True
    else:
        return False


def complete_targets(prefix, parsed_args, **kwargs):
    targets = []
    # argcomplete.warn(parsed_args)
    # argcomplete.warn(parsed_args.f)
    if parsed_args.f:
        targets = get_targets_for_bash_autocomplete(parsed_args.f)
    elif auto_target():
        targets = get_targets_for_bash_autocomplete('./makefile.py')
    else:
        targets = ["No_MakeFile"]

    return targets
    # return ['ali', 'saud', 'xxx']


def print_cmd2():
    argcomplete.warn('print_cmd2:')
    argcomplete.warn('_ARGCOMPLETE: ', os.environ['_ARGCOMPLETE'])
    argcomplete.warn('_ARGCOMPLETE_IFS: ', os.environ['_ARGCOMPLETE_IFS'])
    argcomplete.warn('COMP_LINE: ', os.environ['COMP_LINE'])
    argcomplete.warn('COMP_POINT: ', os.environ['COMP_POINT'])
    argcomplete.warn('_ARGCOMPLETE_COMP_WORDBREAKS: ', os.environ['_ARGCOMPLETE_COMP_WORDBREAKS'])
    argcomplete.warn('COMP_WORDBREAKS: ', os.environ['COMP_WORDBREAKS'])


def print2cmd(txt):
    fd_out.write(txt)


def print_cmd():
    f_out = os.fdopen(8, "wb")

    def _printl(l1, l2=''):
        f_out.write(('{},{}\n\n'.format(l1, l2)).encode('utf-8'))

    try:
        _printl('Environment')
        # printl('_ARGCOMPLETE: ', os.environ['_ARGCOMPLETE'])
        # printl('_ARGCOMPLETE_IFS: ', os.environ['_ARGCOMPLETE_IFS'])
        # printl('COMP_LINE: ', os.environ['COMP_LINE'])
        # printl('COMP_POINT: ', os.environ['COMP_POINT'])
        # printl('_ARGCOMPLETE_COMP_WORDBREAKS: ', os.environ['_ARGCOMPLETE_COMP_WORDBREAKS'])
        # printl('COMP_WORDBREAKS: ', os.environ['COMP_WORDBREAKS'])
    except:
        pass

    f_out.close()


def main():
    global debug, highlight_errors, highlight_warnings
    parser = argparse.ArgumentParser(description='pymake2 is a simple make system implemented in python')
    parser.add_argument('t', metavar='Target', help='the make target in the makefile').completer = complete_targets
    parser.add_argument('-f', metavar='MakefilePath', help='to pass a makefile, default = ./makefile.py')
    # parser.add_argument('-t', metavar='Target', help='the make target in the make file').completer = complete_targets
    parser.add_argument('-j', metavar='Jobs', type=int, help='number of jobs used in the make process')

    argcomplete.autocomplete(parser)
    if len(sys.argv) > 1:
        args = parser.parse_args()
    else:
        args = ArgsT()

    if args.f:
        makefile_path = args.f
    elif auto_target():
        makefile_path = './makefile.py'
    else:
        ret_v = input('No makefile exists!, do you want to creat one?(y/n): ')
        if ret_v.lower() == 'y':
            with open('makefile.py', 'wb') as io_makefile:
                io_makefile.write(gccTemplate)
        sys.exit()

    import imp
    pkg_dir = os.path.normpath(os.path.dirname(__file__) + '/../')
    sys.path.insert(0, pkg_dir)
    if os.path.exists('/opt/pymake2'):
        sys.path.insert(0, '/opt/')

    makefile_m = imp.load_source('makefileM', makefile_path)
    make.shell('rm -f *.pyc')
    debug = getattr(makefile_m, 'Debug', False)
    highlight_errors = getattr(makefile_m, 'HighlightErrors', False)
    highlight_warnings = getattr(makefile_m, 'HighlightWarnings', False)
    targets = parse_makefile(makefile_path, makefile_m)  # type: Dict[str, TargetT]

    if args.t:
        try:
            selected_target = targets[args.t.strip()]  # type: TargetT
            # func = getattr(makefileM, args.t)
        except:
            util.print_color('Error: target function "%s" does not exist!' % args.t, util.tty_colors_cmds.BRed)
            if debug:
                traceback.print_exc()
            sys.exit()

        ret_v = selected_target.run()
        return ret_v

        # attrs = dir(makefileM)
        # for attr in attrs:
        #   if attr==args.t:
        #     func = getattr(makefileM, args.t)

    else:
        print('No target to build, exiting...')
        sys.exit()

    # print 'Done !'


if __name__ == '__main__':
    main()
