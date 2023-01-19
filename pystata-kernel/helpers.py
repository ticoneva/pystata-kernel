# Helper functions that requires Stata running or works on Stata code
# but does not depend on the Jupyter kernel.

import pandas as pd
import numpy as np
import pystata
import sfi
import re
 
def count():
    """
    Count the number of observations
    """
    return sfi.Data.getObsTotal()

def resolve_macro(macro):
    macro = macro.strip()
    if macro.startswith("`") and macro.endswith("'"):
        macro = sfi.Macro.getLocal(macro[1:-1])
    elif macro.startswith("$_"):
        macro = sfi.Macro.getLocal(macro[2:])
    elif macro.startswith("$"):
        macro = sfi.Macro.getGlobal(macro[1:])
    return macro

def InVar(code):
    """
    Return in-statement range
    """    
    code = code.replace(' in ','').strip()
    slash_pos = code.find('/')
    if slash_pos == -1:
        return (None, None)
    start = code[:slash_pos]
    end = code[slash_pos+1:]
    if start.strip() == 'f': start = 1
    if end.strip() == 'l': end = count()
    return (int(start)-1, int(end))

class SelVar():
    """
    Class for generating selection var in Stata
    """
    def __init__(self,condition):
        condition = condition.replace('if ','',1).strip()
        if condition == '':
            self.varname = None
        else:
            cmd = f"tempvar __selectionVar\ngenerate `__selectionVar' = cond({condition},1,0)"
            pystata.stata.run(cmd, quietly=True)      
            self.varname = sfi.Macro.getLocal("__selectionVar")  

    def clear(self):
        if self.varname != None:
            pystata.stata.run(f"capture drop {self.varname}", quietly=True)     

# Regex for parse_code_if_in
code_regex = re.compile(
        r'\A(?P<code>(?!if\s)(?!\sif)(?!in\s)(?!\sin).+?)?(?P<if>\s*if\s+.+?)?(?P<in>\s*in\s.+?)?\Z', flags=re.DOTALL + re.MULTILINE)

def parse_code_if_in(code):
    """
    Parse code into code if in
    """
    match = code_regex.match(code.strip())
    if match:
        args = match.groupdict()
        for k in args:
                args[k] = args[k] if isinstance(args[k],str) else ''   
    else:
        args = {'code':code,
                'if':'',
                'in':''}    

    return args

### Regex's for clean_code() ###
# Detect delimiter. This would detect valid delimiters plus macros:
# delimit_regex = re.compile(r'#delimit( |\t)+(;|cr|`.+\'|\$_.+|\$.+)')
# but it's unnecessary, since Stata's #delimit x interprets any x other 
# than 'cr' as switching the delimiter to ';'.
delimit_regex = re.compile(r'#delimit(.*$)', flags=re.MULTILINE)
# Detect comments spanning multiple lines
comment_regex = re.compile(r'((\/\/\/)(.)*(\n|\r)|(\/\*)(.|\s)*?(\*\/))')
# Detect left Whitespace
left_regex = re.compile(r'\n +')
# Detect Multiple whitespace
multi_regex = re.compile(r' +')

def clean_code(code):
    """
    Remove comments spanning multiple lines and replace custom delimiters
    """

    def _replace_delimiter(code,delimiter=None):
        # Recursively replace custom delimiter with newline

        split = delimit_regex.split(code.strip(),maxsplit=1)

        if len(split) == 3:
            before = split[0]
            after = _replace_delimiter(split[2],split[1].strip())
        else:
            before = code
            after = ''

        if delimiter != 'cr' and delimiter != None:
            before = before.replace('\r', '').replace('\n', '')
            before = before.replace(';','\n')

        return before + after

    # Apply custom delimiter
    code = _replace_delimiter(code)

    # Delete comments spanning multiple lines
    code = comment_regex.sub(' ',code)

    # Delete whitespace at start of line
    code = left_regex.sub('\n',code)

    # Replace multiple whitespace with one
    code = multi_regex.sub(' ',code)

    return code


def noecho_run(code):
    """
    Split code into program and non-program blocks, running each block noecho
    """

    def _startswith_stata_abbrev(string, full_command, shortest_abbrev):
        for j in range(len(shortest_abbrev), len(full_command)+1):
            if string.startswith(full_command[0:j] + ' '):
                return True
        return False

    def _remove_prog_prefixes(cs):
        if (_startswith_stata_abbrev(cs, 'quietly', 'qui')
            or cs.startswith('capture ')
            or _startswith_stata_abbrev(cs, 'noisily', 'n')):
            return _remove_prog_prefixes(cs.split(None, maxsplit=1)[1])
        else:
            return cs

    def _is_start_of_program_block(clean_code_line_stripped):
        cs = _remove_prog_prefixes(clean_code_line_stripped)
        _starts_program = (_startswith_stata_abbrev(cs, 'program', 'pr')
                           and not (cs == 'program di'
                                    or cs == 'program dir'
                                    or cs.startswith('program drop ')
                                    or _startswith_stata_abbrev(cs, 'program list', 'program l')))
        return (_starts_program
                or (cs in ['mata', 'mata:'])
                or (cs in ['python', 'python:']))

    def _run_as_program(clean_non_prog_code):
        _program_name = "temp_pystata_kernel_program_name"
        _program_define_code = f"program {_program_name}\n{clean_non_prog_code}\nend\n"
        pystata.stata.run(_program_define_code, quietly=True)
        pystata.stata.run(_program_name, quietly=False, inline=True, echo=False)
        pystata.stata.run(f"program drop {_program_name}", quietly=True)

    def _run_lines_noecho(co):
        clean_non_prog_code = '\n'.join(co)
        if len(co) == 1:  # to avoid outputting extra blank lines
            pystata.stata.run(clean_non_prog_code, quietly=False, inline=True, echo=False)
        else:
            _run_as_program(clean_non_prog_code)

    cl = clean_code(code).splitlines()
    co = []
    for c in cl:
        cs = c.strip()

        # Are we starting a program definition?
        if _is_start_of_program_block(cs):
            if co:
                _run_lines_noecho(co)
                co = []

        co.append(c)

        # Are we ending a program definition?
        if cs == 'end':
            clean_prog_code = '\n'.join(co)
            if co[0] in ['mata', 'mata:']:  # b/c 'quietly' blocks all mata output
                pystata.stata.run(clean_prog_code, quietly=False, inline=True, echo=False)
            else:
                pystata.stata.run(clean_prog_code, quietly=True, inline=True, echo=False)
            co = []

    if co:
        _run_lines_noecho(co)


def better_pdataframe_from_data(var=None, obs=None, selectvar=None, valuelabel=False, missingval=np.NaN):
    pystata.config.check_initialized()

    return better_dataframe_from_stata(None, var, obs, selectvar, valuelabel, missingval)


def better_pdataframe_from_frame(stfr, var=None, obs=None, selectvar=None, valuelabel=False, missingval=np.NaN):
    pystata.config.check_initialized()

    return better_dataframe_from_stata(stfr, var, obs, selectvar, valuelabel, missingval)


def better_dataframe_from_stata(stfr, var, obs, selectvar, valuelabel, missingval):
    hdl = sfi.Data if stfr is None else sfi.Frame.connect(stfr)

    if hdl.getObsTotal() <= 0:
        return None

    pystata.stata.run("""tempvar indexvar
                         generate `indexvar' = _n""", quietly=True)
    idx_var = sfi.Macro.getLocal('indexvar')

    data = hdl.getAsDict(var, obs, selectvar, valuelabel, missingval)
    if idx_var in data:
        idx = data.pop(idx_var)
    else:
        idx = hdl.getAsDict(idx_var, obs, selectvar, valuelabel, missingval).pop(idx_var)

    idx = pd.array(idx, dtype='Int64')

    pystata.stata.run("drop `indexvar'")

    return pd.DataFrame(data=data, index=idx).convert_dtypes()


