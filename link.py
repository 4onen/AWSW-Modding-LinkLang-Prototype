import renpy.parser
import renpy.ast as ast

import modloader.modgame
from modloader import modast
from modloader.modgame import base as ml

import re
import sys
import os.path as path

arg_regex = re.compile(r'\"[^\"]+\"|\'[^\']+\'|\w+')

class Linker:
    def __init__(self, linkfile):
        self.filename = linkfile
        self.lineno = -1
        self.context = {'here':None}
        self.statement = ''

    def warn(self,msg):
        if self.statement:
            modloader.modgame.sprnt("Linker warning:%r:%d: while parsing statement %r, %s" % (self.filename,self.lineno,self.statement,msg))
        else:
            modloader.modgame.sprnt("Linker warning:%r:%d: %s" % (self.filename,self.lineno,msg))
    
    def error(self,msg):
        raise renpy.parser.ParseError(self.filename,self.lineno,msg,self.statement)
    
    
    def var(self,name):
        if name in self.context:
            return self.context[name]
        else:
            self.error("I don't know what node %r is because that name hasn't been set! I don't support using a label here."%name)
    
    def var_or_label(self,name):
        if name in self.context:
            return self.context[name]
        else:
            l = modast.find_label(name)
            if l is not None:
                return l
            else:
                self.error("I don't know what node %r is because that name hasn't been set! It's also not a label on the Ren'Py tree."%name)

    def parse_args(self,line_remainder,keywords=[]):
        arg = None
        kwargs = {}
        chunks = arg_regex.finditer(line_remainder)
        for match in chunks:
            chunk = match.group(0)
            if chunk[0] in '\"\'' or chunk not in keywords:
                if arg is None:
                    if chunk[0] in '\"\'':
                        arg = chunk[1:-1]
                    else:
                        arg = chunk
                else:
                    self.warn("Found excess non-keyword argument to one command: %r! Attempting to continue with just the first..." % chunk)
            elif chunk in keywords:
                kw = chunk
                content = next(chunks,None)
                if content:
                    content = content.group(0)
                    content = content if content[0] not in '\"\'' else content[1:-1]
                    if keywords[kw] is not str:
                        try:
                            content = keywords[kw](content)
                        except:
                            self.error("keyword %r expected argument of type %r, but I couldn't convert actual argument %r!" % (kw,keywords[kw],content))
                    kwargs[kw] = content
                else:
                    self.warn("keyword %r expecting argument following. Attempting to continue..."%chunk[0])
            else:
                self.warn("unexpected word %r. Attempting to continue..."%chunk)
        
        if 'from' in kwargs:
            kwargs['source'] = kwargs['from']
            del kwargs['from']

        if 'source' in kwargs and kwargs['source'] not in self.context:
            self.error("I don't know where node variable %r is defined! Remember, I read the link file from top to bottom. I can't refer to future nodes!"%kwargs['source'])
        
        if 'as' in kwargs:
            kwargs['storeto']=kwargs['as']
            del kwargs['as']
        
        if 'for' in kwargs:
            kwargs['depth'] = kwargs['for']
            del kwargs['for']
        
        if 'return' in kwargs:
            kwargs['returnto'] = kwargs['return']
            del kwargs['return']

        return arg,kwargs

    def parse_link_statements(self, stmts, statement_kinds):
        if len(stmts) == 0:
            return

        for (filename,lineno,stmt,substmts) in stmts:
            self.filename,self.lineno,self.statement = filename,lineno,stmt
            if substmts:
                return_here = self.context['here']
                if stmt[-1] != ':':
                    self.warn("I found block following it! I expected it to end with a ':', but it did not. Attempting to continue...")
                else:
                    stmt=stmt[:-1]
            
            for (r,keywords,func) in statement_kinds:
                match = r.match(stmt)
                if match:
                    arg,kwargs = self.parse_args(stmt[match.end(0):].strip(),keywords)
                    func(self,match,arg,**kwargs)
                    # modloader.modgame.sprnt("Successfully parsed %r"%stmt)
                    break
            else:
                self.error("I couldn't recognize the statement. Are you sure it's on the list of supported commands?")
            
            if substmts:
                self.parse_link_statements(substmts,statement_kinds)
                self.context['here'] = return_here

    def stmt_find(self,match,arg,storeto='here'):
        subcommand = match.group(1)
        if arg is None:
            self.error("I expected an argument to the '%s' statement!"%match.group(0))
        
        fn = {'label':modast.find_label
             ,'jump':modast.find_jump_target
             ,'menu':modast.find_menu
             ,'say':modast.find_say
             ,'python':modast.find_python_statement
             }.get(subcommand,lambda _:self.error("Unrecognized 'find' target: %r"%subcommand))

        self.context[storeto] = fn(arg)
        if self.context[storeto] is None:
            self.error("I couldn't find any %r with content %r in the Ren'Py tree!"%(subcommand,arg))

    def stmt_search(self,match,arg,source='here',storeto='here',depth=200):
        subcommand = match.group(1)
        fromnode = self.var(source)
        if arg is None:
            type = \
                {'say':ast.Say
                ,'if':ast.If
                ,'menu':ast.Menu
                ,'show':ast.Show
                ,'hide':ast.Hide
                ,'call':ast.Call
                ,'scene':ast.Scene
                ,'label':ast.Label
                }.get(subcommand,None)
            if type is None:
                self.error("Unrecognized 'search' target: %r"%subcommand)
            self.context[storeto] = modast.search_for_node_type(fromnode,type,max_depth=depth)
            if self.context[storeto] == None:
                self.error("I couldn't find a node of type %r starting from %r:%r"%(type,source,fromnode))
        else:
            criteria = \
                {'say':lambda x: isinstance(x,ast.Say) and x.what==arg
                ,'if':lambda x: isinstance(x,ast.If) and any((e[0]==arg for e in x.entries))
                ,'menu':lambda x: isinstance(x,ast.Menu) and any((e[0]==arg for e in x.items))
                ,'show':lambda x: isinstance(x,ast.Show) and ''.join(x.imspec[0])==arg
                ,'hide':lambda x: isinstance(x,ast.Hide) and ''.join(x.imspec[0])==arg
                ,'call':lambda x: isinstance(x,ast.Call) and x.label==arg
                ,'scene':lambda x: isinstance(x,ast.Scene) and x.imspec is not None and ''.join(x.imspec[0])==arg
                ,'label':lambda x: isinstance(x,ast.Label) and x.name==arg
                }.get(subcommand,None)
            if criteria is None:
                self.error("Unrecognized 'search' target: %r"%subcommand)
            self.context[storeto] = modast.search_for_node_with_criteria(fromnode,criteria,max_depth=depth)
            if self.context[storeto] == None:
                self.error("I couldn't find a node matching type %r with content %r starting from %r:%r"%(subcommand,arg,source,fromnode))
    
    def stmt_jump(self,_,arg,source='here'):
        sourcenode = self.var(source)
        target = modast.find_label(arg)
        if target is None:
            self.error("I couldn't find a label named %r in the Ren'Py tree! Jumps have to be to labels due to Ren'Py inner workings."%arg)
        modast.hook_opcode(sourcenode,None).chain(target)

    def stmt_call(self,_,arg,source='here',returnto=None):
        sourcenode = self.var(source)
        target = modast.find_label(arg)
        if target is None:
            self.error("I couldn't find a label named %r in the Ren'Py tree! Calls have to be into labels due to Ren'Py inner workings."%arg)
        
        if returnto is not None:
            returntarget = self.var_or_label(returnto)
        else:
            returntarget = None
        modast.call_hook(sourcenode,target,None,returntarget)
    
    def stmt_branch(self,_,arg,storeto='here'):
        if 'here' not in self.context:
            self.error("I can't branch from a non-existent node! Branching only supported on the 'here' node.")
        n = self.context['here']
        if isinstance(n,ast.Menu):
            if arg is None:
                self.error("I expected a menu item to branch to!")
            choice = ml.get_menu_hook(n).get_item(arg)
            if choice is None:
                self.error("I couldn't find a menu item labeled %r in the menu %r!"%(arg,n))
            self.context[storeto] = choice[2][0]
        elif isinstance(n,ast.If):
            if arg is None or arg == 'else':
                arg = 'True'
            for e in n.entries:
                if e[0] == arg:
                    self.context[storeto] = e[1][0]
                    return
            else:
                self.error("I couldn't find the condition %r in the if statement %r!"%(arg,n))
        else:
            self.error("I can't branch into a %r!"%type(n))
    
    def stmt_change(self,_,arg,to=None):
        if 'here' not in self.context:
            self.error("I can't change a non-existent node! Changing only supported on the 'here' node.")
        n = self.context['here']

        if arg is None:
            self.error("I expected an option to change! (For If statements, this is the condition wrapped in quotes.)")
        if to is None:
            self.error("Expected a 'to' keyword option to change the option to! (For If statements, this is the condition wrapped in quotes.)")
        
        if isinstance(n,ast.Menu):
            h = ml.get_menu_hook(n)
            choice = h.get_item(arg)
            if choice is None:
                self.error("I couldn't find a menu item labeled %r in the menu %r!"%(arg,n))
            h.delete_item(arg)
            h.add_item(to,choice[1],choice[2])
        elif isinstance(n,ast.If):
            if arg is None or arg == 'else':
                arg = 'True'
            for e in n.entries:
                if e[0] == arg:
                    n.entries.remove(e)
                    n.entries.append((to,e[1]))
                    return
            else:
                self.error("I couldn't find the condition %r in the If node %r!"%(arg,n))
        else:
            self.error("I can't change branches on a node of type %r!"%type(n))


    def stmt_add(self,match,arg,branch=None):
        if 'here' not in self.context:
            self.error("I can't add a branch to a non-existent node! Branch addition is only supported on the 'here' node.")
        n = self.context['here']

        if branch is None:
            self.error("I expected a branch to add!")
        branch_block = modast.find_label(branch)
        if branch_block is None:
            self.error("I couldn't find the label %r in the Ren'Py tree! For sanity, we try to make sure menu choices and if/elif/else branches added by the linker go to full labels."%branch)

        if isinstance(n,ast.Menu) and match.group(1) == 'option':
            if arg is None:
                self.error("I expected a menu item to add!")
            # TODO: Support adding conditions here. May require separating 'add option' code from 'add cond'
            h = ml.get_menu_hook(n)
            h.add_item(arg,branch_block,condition="True")
        elif isinstance(n,ast.If) and match.group(1) in ['if','elif','else']:
            if arg is None:
                arg = 'True'
                if match.group(1) != 'else':
                    self.error("I expected a condition for this %r clause I'm adding!"%match.group(1))
                if n.entries[-1][0] == 'True':
                    self.warn("Overriding existing 'True' condition on %r"%n)
                    n.entries[-1] = ('True',branch_block)
                else:
                    n.entries.append(('True',branch_block))
            elif match.group(1) == 'elif':
                n.entries.append((arg,branch_block))
            else:
                n.entries.insert(0,(arg,branch_block))
        else:
            self.error("I can't add a %r to a %r!"%(match.group(1),type(n)))

    def stmt_link(self,_,arg):
        if 'here' not in self.context:
            self.error("I can't link to a non-existent node! Use a 'find' type statement to find a node before trying this command.")
        n = self.context['here']

        if arg is None:
            self.error("I expected a label to link to the current node!")
        target = modast.find_label(arg)
        if target is None:
            self.error("I couldn't find a label named %r in the Ren'Py tree! Make sure the label is in one of your mod files before trying to add it as a link back."%arg)

        target.chain(n)
    
    def stmt_next(self,_,arg):
        if arg is not None:
            self.error("I don't know what to do with a 'next' statement with an argument!")

        if 'here' not in self.context:
            self.error("I can't go the next node after a non-existent current node! Use a 'find' type statement to find a node before trying this command.")
        self.context['here'] = self.context['here'].next

find_regex = re.compile(r'find\s+(label|jump|menu|say|python)')
search_regex = re.compile(r'search\s+(say|if|menu|show|hide|call|scene|label)')
call_regex = re.compile(r'call')
jump_regex = re.compile(r'jump')
branch_regex = re.compile(r'branch')
change_regex = re.compile(r'change')
add_option_regex = re.compile(r'add\s+(option|if|elif|else)')
link_regex = re.compile(r'link')
next_regex = re.compile(r'next')
statement_kinds = \
            [ (find_regex, {'as':str}, Linker.stmt_find)
            , (search_regex, {'from':str,'as':str,'for':int}, Linker.stmt_search)
            , (call_regex, {'from':str,'return':str}, Linker.stmt_call)
            , (jump_regex, {'from':str}, Linker.stmt_jump)
            , (branch_regex, {'as':str}, Linker.stmt_branch)
            , (change_regex, {'to':str}, Linker.stmt_change)
            , (add_option_regex, {'branch':str}, Linker.stmt_add)
            , (link_regex, {}, Linker.stmt_link)
            , (next_regex, {}, Linker.stmt_next)
            ]





def run_linkfile(linkfile):
    if not path.exists(linkfile):
        linkfile = path.join(path.dirname(__file__), linkfile)
        if not path.exists(linkfile):
            raise IOError("Linkfile %r does not exist." % (linkfile,))
    lines = renpy.parser.list_logical_lines(linkfile)
    lines = renpy.parser.group_logical_lines(lines)
    Linker(linkfile).parse_link_statements(lines, statement_kinds)