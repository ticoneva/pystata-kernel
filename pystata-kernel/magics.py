import sys
import re
import urllib
import pandas as pd
from textwrap import dedent
from bs4 import BeautifulSoup as bs
from argparse import ArgumentParser, SUPPRESS
from pkg_resources import resource_filename

import pystata
import random

def print_kernel(msg, kernel):
    msg = re.sub(r'$', r'\r\n', msg, flags=re.MULTILINE)
    msg = re.sub(r'[\r\n]{1,2}[\r\n]{1,2}', r'\r\n', msg, flags=re.MULTILINE)
    stream_content = {'text': msg, 'name': 'stdout'}
    kernel.send_response(kernel.iopub_socket, 'stream', stream_content)

def count():
    pystata.stata.run("count",quietly=True)
    r_dict = pystata.stata.get_return()
    return int(r_dict['r(N)'])

def genSelVar(condition):
    condition = condition.replace('if ','').strip()
    # TODO: create a tmp var class to keep track of things
    varname = "pystataTmp_" + str(random.randrange(1000,9999))
    
    # Gen selection var in Stata
    cmd = f"gen {varname} = cond({condition},1,0)"
    pystata.stata.run(cmd, quietly=True)

    return varname

class StataMagics():
    html_base = "https://www.stata.com"
    html_help = urllib.parse.urljoin(html_base, "help.cgi?{}")

    magic_regex = re.compile(
        r'\A(%|\*%)(?P<magic>.+?)(?P<code>\s+.*)?\Z', flags=re.DOTALL + re.MULTILINE)

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
            name, code = match.groupdict().values()
            code = '' if code is None else code.strip()
            if name in self.available_magics:
                if code.find('-h') >= 0:
                    print_kernel(self.available_magics[name].format(name), kernel)
                    code = ''
                else:
                    code = getattr(self, "magic_" + name)(code, kernel)
            else:
                print_kernel("Unknown magic %{0}.".format(name), kernel)
    
        return code        

    def magic_browse(self,code,kernel):
        N_max = 200
        vars = None
        sel_var = None

        if_start = code.find('if ')
        if if_start >= 0:
            # If statement
            sel_var = genSelVar(code[if_start:])
            code = code[:if_start]
            
        args = [c.strip() for c in code.split(' ') if c]

        if len(args) >= 1:
            if args[0].isnumeric():
                # 1st argument is obs count
                N_max = int(args[0])
                del args[0]    

        if len(args) >= 1:
            vars = args

        N = min(count(),N_max)

        try:
            df = pystata.stata.pdataframe_from_data(obs=range(0,N),
                                                    var=vars,
                                                    selectvar=sel_var)
            if sel_var != None:
                df = df.drop([sel_var],axis=1)
            html = df.to_html(na_rep='.', notebook=True)

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
            pystata.stata.run(f"capture drop {sel_var}", quietly=True)            

        return ''

    def magic_help(self,code,kernel):
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

