__author__ = 'Saud Wasly'

import fnmatch
import inspect
import os
import re
import sys

import sarge

import pymake2.utility as util
from pymake2.utility import tty_colors as colors

# makefileM = None # to be assigned upon importing

_highlighting = False
_highlighting_dict = {}


def eval(txt):
    outer_frame = inspect.stack()[1][0]
    outer_frame_globals = outer_frame.f_globals

    vars = re.findall(r'\$\((\w+)\)', txt)
    new_txt = re.sub(r'\$\((\w+)\)', r'{\1}', txt)

    for v in vars:
        try:
            val = outer_frame_globals[v]
            if type(val) is list:
                val = ' '.join(val)
            new_txt = new_txt.replace('{%s}' % v, val)
        except:
            val = os.getenv(v)
            if val:
                new_txt = new_txt.replace('{%s}' % v, val)
            else:
                util.print_color('Error: cannot find variable %s' % v, util.tty_colors_cmds.Red)
                sys.exit()
    return new_txt


def print_color(txt, fg='', bg='', bold=False):
    msg = util.get_colored(txt, fg, bg, bold)
    print(msg)


def regx(pattern):
    return re.compile(pattern, flags=re.IGNORECASE)


def hl(regx_p, fg_color=colors.Yellow, bg_color=''):
    global _highlighting
    _highlighting = True
    _highlighting_dict[regx_p] = (fg_color, bg_color)


def _highlight_outputs(txt):
    outer_frame = inspect.stack()[1][0]
    outer_frame = outer_frame.f_back
    outer_frame_globals = outer_frame.f_globals

    ret_v = txt
    try:
        highlight_warnings = outer_frame_globals['HighlightWarnings']
        if highlight_warnings:
            ret_v = util.HighlightWarnings(ret_v)
    except:
        pass

    try:
        highlight_errors = outer_frame_globals['HighlightErrors']
        if highlight_errors:
            ret_v = util.HighlightErrors(ret_v)
    except:
        pass

    try:
        highlight_notes = outer_frame_globals['HighlightNotes']
        if highlight_notes:
            ret_v = util.HighlightNotes(ret_v)
    except:
        pass

    try:  # custom highlight

        if _highlighting:
            for key in _highlighting_dict.keys():
                color = _highlighting_dict[key]
                ret_v = util.Highlight_custom(ret_v, key, color)
    except Exception as e:
        print(e)
        pass

    return ret_v


def find(root='./', filter_pattern='*', recursive=False, absolute=False, dir_only=False):
    src_files = []
    root_dir = os.path.abspath(root) if absolute else os.path.normpath(root)
    if recursive:
        for cur_root, directory, files in os.walk(root_dir):
            if dir_only:
                src_files.extend([cur_root + '/' + e for e in directory])
            else:
                for srcfile in fnmatch.filter(files, filter_pattern):
                    src_files.append(cur_root + '/' + srcfile)
    else:
        for cur_root, directory, files in os.walk(root_dir):
            if dir_only:
                src_files.extend([cur_root + '/' + e for e in directory])
            else:
                for srcfile in fnmatch.filter(files, filter_pattern):
                    src_files.append(cur_root + '/' + srcfile)
            break

    if dir_only:
        # add the current root directory to the list
        root_dir = os.path.abspath(root) if absolute else os.path.normpath(root)
        src_files.append(root_dir)
    return src_files


def get_dir(path):
    if type(path) is str:
        dir_str = os.path.dirname(path)
        return dir_str
    elif type(path) is list:
        ret_paths = []
        for p in path:
            dir_str = os.path.dirname(p)
            ret_paths.append(dir_str)
        return ret_paths
    else:
        return None


def print_list(lst):
    if type(lst) is not list:
        lst = lst.split()
    for i in lst:
        print(i)
    return lst


def get_filename(path):
    if type(path) is str:
        dir_str = os.path.basename(path)
        return dir_str
    elif type(path) is list:
        ret_paths = []
        for p in path:
            dir_str = os.path.basename(p)
            ret_paths.append(dir_str)
        return ret_paths
    else:
        return None


def compile(compiler, flags, sources, objects):
    # utl.print_color('Compiling ...', utl.tty_colors.On_Cyan)
    highlight_no = True if util.is_Highlight_ON() else False

    if type(sources) is list:
        srcs = sources
    else:  # in the case of str
        srcs = sources.split()

    if type(objects) is list:
        objs = objects
    else:  # in the case of str
        objs = objects.split()

    if len(srcs) != len(objs):
        util.write_color('Error: ', util.tty_colors_cmds.Red)
        print('the length of the source files list does not match with objects files list')
        return

    for i, item in enumerate(srcs):
        cmd = '{CC} {flags} -c {src} -o {obj}'.format(CC=compiler, flags=flags, src=item, obj=objs[i])

        src_file = os.path.basename(item)
        obj_file = os.path.basename(objs[i])
        src_file = src_file.split('.')[0]
        obj_file = obj_file.split('.')[0]
        if src_file != obj_file:
            util.write_color('Compiling Error: ', util.tty_colors_cmds.BRed)
            print('source file %s and object file %s do not match. Make sure that the source and the object files lists are correspondent' % (item, objs[i]))
            return False
        if os.path.isfile(objs[i]):  # if the object file already exists
            src_m_time = os.path.getmtime(item)
            obj_mtime = os.path.getmtime(objs[i])
            if src_m_time <= obj_mtime:
                continue
        else:  # no obj file exists
            obj_dir = os.path.dirname(objs[i])
            obj_dir = os.path.normpath(obj_dir)
            if not os.path.exists(obj_dir):
                os.makedirs(obj_dir)

        util.print_color('Compiling: %s' % item, util.tty_colors_cmds.On_Cyan)
        success, outputs = sh(cmd, True, highlight_no)
        if highlight_no:
            print(_highlight_outputs(outputs))

        if not success:
            # if not run(cmd, show_cmd=True):
            util.write_color('Error: ', util.tty_colors_cmds.BRed)
            print('failed to compile, \n  %s' % cmd)
            return False

    return True


def link(linker, flags, objects, executable):
    if type(objects) is list:
        objs = ' '.join(objects)
    else:
        objs = objects.strip().strip('\n')

    objects_list = objs.split()

    link_flag = True
    if os.path.isfile(executable):
        link_flag = False
        exe_m_time = os.path.getmtime(executable)
        for obj in objects_list:
            obj_mtime = os.path.getmtime(obj)
            if obj_mtime > exe_m_time:
                link_flag = True
                break

    if link_flag:
        util.print_color('Linking ...', util.tty_colors_cmds.On_Blue)
        cmd = '{linker} {flags} {objs} -o {executable}'.format(linker=linker, flags=flags, objs=objs, executable=executable)
        hl = util.is_Highlight_ON()
        success, outputs = sh(cmd, True, hl)
        if hl:
            print(_highlight_outputs(outputs))

        if not success:
            util.print_color("Failed to link object files to assemble '%s'" % executable, util.tty_colors_cmds.BRed)
            return False
        else:
            return True
    else:
        return True


def archive(archiver, flags, objects, library):
    if type(objects) is list:
        objs = ' '.join(objects)
    else:
        objs = objects

    objects_list = objs.split()

    satisfaction_flag = False
    if os.path.isfile(library):
        satisfaction_flag = True
        output_m_time = os.path.getmtime(library)
        for obj in objects_list:
            obj_mtime = os.path.getmtime(obj)
            if obj_mtime > output_m_time:
                satisfaction_flag = False
                break

    if not satisfaction_flag:
        util.print_color('Archiving...', util.tty_colors_cmds.On_Blue)
        cmd = '{AR} {flags} {output} {objs}'.format(AR=archiver, flags=flags, objs=objs, output=library)
        hl = util.is_Highlight_ON()
        success, outputs = sh(cmd, True, hl)
        if hl:
            print(_highlight_outputs(outputs))

        if not success:
            util.print_color("Failed to archive object files to assemble '%s'" % library, util.tty_colors_cmds.BRed)
            return False
        else:
            return True
    else:
        return True


def norm_paths(paths):
    if type(paths) is str:
        dir_str = os.path.normpath(paths)
        return dir_str
    elif type(paths) is list:
        ret_paths = []
        for p in paths:
            dir_str = os.path.normpath(p)
            ret_paths.append(dir_str)
        return ret_paths
    else:
        return None


def join(*args):
    try:
        ret_v = ' '.join(args)  # this works if all args are str type
        return ret_v
    except:  # deal with different types
        ret_v = ''
        for arg in args:
            if type(arg) is list:
                arg_items = ' '.join(arg)
                ret_v += arg_items + ' '

            else:  # assume str
                ret_v += arg + ' '
        return ret_v


def replace(src_list, term, rep_with):
    if type(src_list) is list:
        ret_v = []
        for item in src_list:
            x = item.replace(term, rep_with)
            ret_v.append(x)

        return ret_v
    else:
        ret_v = src_list.replace(term, rep_with)
        return ret_v


def retarget(src_list, target_p, omit=''):
    if target_p.endswith('/'):
        target_p = target_p[:-1]

    if type(src_list) is list:
        ret_v = []
        for item in src_list:
            x = item.replace(omit, '')
            x = target_p + '/' + x
            x = os.path.normpath(x)
            ret_v.append(x)

        return ret_v
    else:
        x = src_list.replace(omit, '')
        x = target_p + '/' + x
        x = os.path.normpath(x)
        ret_v = x
        return ret_v


def exclude(original, ignores):
    ret_v = []
    for item in original:
        if item not in ignores:
            ret_v.append(item)
    return ret_v


def shell(cmd):
    p = sarge.run(cmd, shell=True, stdout=sarge.Capture())
    return p.stdout.text


def sh(cmd, show_cmd=False, capture_output=False, timeout=-1):
    if show_cmd:
        print(cmd)
    try:
        if capture_output:
            if timeout > -1:
                p = sarge.run(cmd, shell=True, stdout=sarge.Capture(), stderr=sarge.Capture(), async_=True)
                # sleep(3)
                try:
                    cmd = p.commands[0]  # type: sarge.Command # FIXME: This line generates index exception sometime
                    timed_out = util.wait_process(timeout, cmd)
                    if timed_out:
                        util.print_color('The command "%s" is timed out!' % cmd, util.tty_colors_cmds.On_Red)
                    util.kill_alive_process(cmd)
                except:
                    pass
            else:
                p = sarge.run(cmd, shell=True, stdout=sarge.Capture(), stderr=sarge.Capture())
        else:
            if timeout > -1:
                p = sarge.run(cmd, shell=True, async_=True)
                # sleep(3)
                try:
                    cmd = p.commands[0]  # type: sarge.Command # FIXME: This line generates index exception sometime
                    timed_out = util.wait_process(timeout, cmd)
                    if timed_out:
                        util.print_color('The command "%s" is timed out!' % cmd, util.tty_colors_cmds.On_Red)
                    util.kill_alive_process(cmd)
                except:
                    pass
            else:
                p = sarge.run(cmd, shell=True)

        outputs = ''

        if p.stdout and len(p.stdout.text) > 0:
            outputs = p.stdout.text
        if p.stderr and len(p.stderr.text) > 0:
            if outputs == '':
                outputs = p.stderr.text
            else:
                outputs += '\n' + p.stderr.text
        return p.returncode == 0, outputs
    except:
        if util.get_makefile_var('Debug'):
            util.Print_Debuging_messages()

        return False, ''


def run(cmd, show_cmd=False, highlight=False, timeout=10):
    """
    :param cmd: (str) the shell command
    :param show_cmd: (bool) print the command before executing it
    :param highlight: (bool) apply color highlights for the outputs
    :param timeout: (float) any positive number in seconds
    :return:
    """
    if highlight:
        success, outputs = sh(cmd, show_cmd, True, timeout)
        hl_out = _highlight_outputs(outputs)
        print(hl_out)
    else:
        success, outputs = sh(cmd, show_cmd, False, timeout)

    return success


def target(func):
    """
      This is a decorator function
    :param func:
    :return:
    """

    def target_func(*original_args, **original_kwargs):
        # print 'before the func'
        # print original_kwargs
        ret_v = func(*original_args, **original_kwargs)
        if ret_v is None or not ret_v:
            return False
        else:
            return True
        # print 'after the func'

    return target_func


if __name__ == '__main__':
    print('testing find()')
    f_list = find(dir_only=True, absolute=False)
    print_list(f_list)
    print('File List has %d items' % len(f_list))
