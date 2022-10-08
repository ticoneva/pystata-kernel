import sys
import re
import urllib
import pandas as pd
from textwrap import dedent
from bs4 import BeautifulSoup as bs
from argparse import ArgumentParser, SUPPRESS
from pkg_resources import resource_filename
from .helpers import better_pdataframe_from_data
from .config import get_config

import pystata
import sfi
import random
import numpy as np

def print_kernel(msg, kernel):
    msg = re.sub(r'$', r'\r\n', msg, flags=re.MULTILINE)
    msg = re.sub(r'[\r\n]{1,2}[\r\n]{1,2}', r'\r\n', msg, flags=re.MULTILINE)
    stream_content = {'text': msg, 'name': 'stdout'}
    kernel.send_response(kernel.iopub_socket, 'stream', stream_content)

def count():
    #pystata.stata.run("count",quietly=True)
    #r_dict = pystata.stata.get_return()
    #return int(r_dict['r(N)'])
    return sfi.Data.getObsTotal()

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

class StataMagics():
    html_base = "https://www.stata.com"
    html_help = urllib.parse.urljoin(html_base, "help.cgi?{}")

    magic_regex = re.compile(
        r'\A(%|\*%)(?P<magic>.+?)(?P<code>\s+(?!if\s)(?!\sif)(?!in\s)(?!\sin).+?)?(?P<if>\s+if\s+.+?)?(?P<in>\s+in\s+.+?)?\Z', flags=re.DOTALL + re.MULTILINE)

    # Format: magic_name: help_content
    available_magics = {
        'browse': '{} [-h] [N] [varlist] [if]',
        'help': '{} [-h] command_or_topic_name'
    }
    
    csshelp_default = resource_filename(
        'pystata-kernel', 'css/_StataKernelHelpDefault.css')

    def magic(self, code, kernel):
        match = self.magic_regex.match(code.strip())
        if match:
            v = match.groupdict()
            for k in v:
                v[k] = v[k] if isinstance(v[k],str) else ''                

            name = v['magic']
            v['code'] = v['code'].strip()

            if name in self.available_magics:
                if v['code'].find('-h') >= 0:
                    print_kernel(self.available_magics[name].format(name), kernel)
                    code = ''
                else:
                    code = getattr(self, "magic_" + name)(v, kernel)
            else:
                print_kernel("Unknown magic %{0}.".format(name), kernel)
    
        return code        

    def magic_browse(self,args,kernel):
        env = get_config()
        N_max = 200
        
        # If and in statements
        sel_var = SelVar(args['if'])
        start,end = InVar(args['in'])
            
        vargs = [c.strip() for c in args['code'].split(' ') if c]

        if len(vargs) >= 1:
            if vargs[0].isnumeric():
                # 1st argument is obs count
                N_max = int(vargs[0])
                del vargs[0]    

        # Specified variables?
        vars = vargs if len(vargs) >= 1 else None

        # Obs range
        if start != None and end != None:
            obs_range = range(start,end)
        else:
            obs_range = range(0,min(count(),N_max))

        # Missing value display format
        missingval = np.NaN
        if env['missing'] is not None and env['missing'] != 'pandas':
            missingval = env['missing']  
        
        try:
            df = better_pdataframe_from_data(obs=obs_range,
                                                    var=vars,
                                                    selectvar=sel_var.varname,
                                                    missingval=missingval)
            if vars == None and sel_var.varname != None:
                df = df.drop([sel_var.varname],axis=1)
                
            html = df.to_html(notebook=True)

            content = {
                    'data': {
                        'text/html': html},
                    'metadata': {}}
            kernel.send_response(kernel.iopub_socket, 'display_data', content)
        except Exception as e:
            msg = "Failed to browse data.\r\n{0}"
            print_kernel(msg.format(e), kernel)

        if sel_var != None:
            # Drop selection var in Stata. We put this outside of try to ensure 
            # the temp variable gets deleted even when there is an error.
            sel_var.clear()

        return ''

    def magic_help(self,args,kernel):

        code = args['code']

        try:
            reply = urllib.request.urlopen(self.html_help.format(code))
            html = reply.read().decode("utf-8")
            soup = bs(html, 'html.parser')

            # Set root for links to https://ww.stata.com
            for a in soup.find_all('a', href=True):
                href = a.get('href')
                match = re.search(r'{}(.*?)#'.format(code), href)
                if match:
                    hrelative = href.find('#')
                    a['href'] = href[hrelative:]
                elif not href.startswith('http'):
                    link = a['href']
                    match = re.search(r'/help.cgi\?(.+)$', link)
                    # URL encode bad characters like %
                    if match:
                        link = '/help.cgi?'
                        link += urllib.parse.quote_plus(match.group(1))
                    a['href'] = urllib.parse.urljoin(self.html_base, link)
                    a['target'] = '_blank'

            # Remove header 'Stata 15 help for ...'
            soup.find('h2').decompose()

            # Remove Stata help menu
            soup.find('div', id='menu').decompose()

            # Remove Copyright notice
            tags = ['a', 'font']
            for tag in tags:
                copyright = soup.find(tag, text='Copyright')
                if copyright:
                    copyright.find_parent("table").decompose()
                    break

            # Remove last hrule
            soup.find_all('hr')[-1].decompose()

            # Set all the backgrounds to transparent
            for color in ['#ffffff', '#FFFFFF']:
                for bg in ['bgcolor', 'background', 'background-color']:
                    for tag in soup.find_all(attrs={bg: color}):
                        if tag.get(bg):
                            tag[bg] = 'transparent'

            # Set html
            css = soup.find('style', {'type': 'text/css'})
            with open(self.csshelp_default, 'r') as default:
                css.string = default.read()

            fallback = 'This front-end cannot display HTML help.'
            resp = {
                'data': {
                    'text/html': str(soup),
                    'text/plain': fallback},
                'metadata': {}}
            kernel.send_response(kernel.iopub_socket, 'display_data', resp)
        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            msg = "Failed to fetch HTML help.\r\n{0}"
            print_kernel(msg.format(e), kernel)

        return ''        

