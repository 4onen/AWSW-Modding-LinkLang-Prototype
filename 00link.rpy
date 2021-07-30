python early:
    def linkmod_main():
        import renpy
        import renpy.ast as ast
        from renpy.parser import Lexer

        import modloader.modast as modast
        from modloader.modgame import base as ml
        from modloader.modgame import sprnt

        class CanHaveInitBlock(ast.Node): # Based on ast.While
            __slots__ = ['block', 'executing_body']
            def __init__(self, loc, block):
                super(CanHaveInitBlock, self).__init__(loc)
                self.block = block
                self.executing_body = False
            
            def diff_info(self):
                return (CanHaveInitBlock)
            
            def get_children(self, f):
                f(self)
                for i in self.block:
                    i.get_children(f)
            
            def chain(self,next):
                self.next = next
                ast.chain_block(self.block, self)
            
            def replace_next(self, old, new):
                ast.Node.replace_next(self,old,new)
                if self.block and (self.block[0] is old):
                    self.block.insert(0, new)
            
            def pre_execute(self):
                pass
            
            def post_execute(self):
                pass
            
            def execute(self):
                ast.next_node(self.next)
                if not renpy.game.context().init_phase:
                    return
                elif self.executing_body:
                    if self.post_execute():
                        ast.next_node(self.block[0])
                    else:
                        self.executing_body = False
                elif (not self.pre_execute()) and self.block:
                    ast.next_node(self.block[0])
                    self.executing_body = True

            def predict(self):
                return [ self.block[0], self.next ]
            
            def scry(self):
                rv = ast.Node.scry(self)
                rv._next = None
                return rv
            
            def restructure(self,callback):
                callback(self.block)

        hn = 'linkmod_here_node'

        def node_print_formatter(n):
            return "\n%r\nat line %u of file '%s'"%(n, n.linenumber, n.filename)
        
        def set_herenode(n):
            # sprnt("Herenode set: %s"%node_print_formatter(n))
            renpy.python.store_dicts["store"][hn] = n
        
        def get_herenode(action,fromvar=None):
            if fromvar == None:
                fromvar = hn
            n = renpy.python.store_dicts["store"].get(fromvar, None)
            if n is None or not isinstance(n, ast.Node):
                if fromvar==hn:
                    renpy.error("The current node must already be defined to %s. Try running a 'find' in this file first!"%action)
                else:
                    renpy.error("I couldn't find a `ast.Node` in the variable %r!"%fromvar)
            return n
        
        def parse_condition(l,allow_blank=False):
            keywords=\
                { 'inaccessible': 'False'
                , 'False': 'False'
                , 'always': 'True'
                , 'True': 'True'
                , 'else': 'True'
                }
            w = l.word()
            if w is not None:
                if w not in keywords:
                    if w in ['true', 'false']:
                        renpy.error("%r is not a valid condition keyword. Did you mean to capitalize it?"%w)
                    renpy.error("%r is not a valid condition keyword."%w)
                else:
                    return keywords[w]
            elif allow_blank:
                return l.string()
            else:
                return l.require(l.string,"branch condition")

        def parse_image_name_forgiving(l,keywords=[]):
            cp = l.checkpoint()
            segments = []
            while True:
                v = l.image_name_component()
                if not v:
                    break
                elif v in keywords:
                    l.revert(cp)
                    break
                else:
                    segments.append(v)
                    continue
            return ' '.join(segments)

        def linkmod_commands_setting_new_herenode():
            def find_show(imspec):
                for node in renpy.game.script.all_stmts:
                    if isinstance(node, ast.Show) and ' '.join(node.imspec[0])==imspec:
                        return node
            
            def find_hide(imspec):
                for node in renpy.game.script.all_stmts:
                    if isinstance(node, ast.Hide) and ' '.join(node.imspec[0])==imspec:
                        return node
            
            def find(typ,content):
                fn =\
                    {'label':modast.find_label
                    ,'jump':modast.find_jump_target
                    ,'menu':modast.find_menu
                    ,'show':find_show
                    ,'hide':find_hide
                    ,'say':modast.find_say
                    ,'python':modast.find_python_statement
                    }.get(typ,lambda _:renpy.error("Unrecognized 'find' typ: %r"%(typ)))
                return fn(content)
            
            def branch(n,content):
                if isinstance(n,ast.Menu):
                    if not content:
                        renpy.error("I expected a menu item to branch to!")
                    choice = ml.get_menu_hook(n).get_item(content)
                    if choice is None:
                        renpy.error("I couldn't find a menu item labeled %r in the menu %r!"%(content,n))
                    return choice[2][0]
                elif isinstance(n,ast.If):
                    if not content:
                        if len(n.entries)!=1:
                            renpy.error("The `ast.If` I found here has more than one branch! Specify a condition to select a path.")
                        else:
                            return n.entries[0][1][0]
                    else:
                        for e in n.entries:
                            if e[0] == content:
                                return e[1][0]
                        renpy.error("I couldn't find the condition %r in the if statement %r!"%(content,n))
                else:
                    renpy.error("I can't branch into a %r!"%type(n))

            def search(typ,n,content,depth):
                if not content:
                    type = \
                        {'say':ast.Say
                        ,'if':ast.If
                        ,'menu':ast.Menu
                        ,'show':ast.Show
                        ,'hide':ast.Hide
                        ,'call':ast.Call
                        ,'scene':ast.Scene
                        ,'label':ast.Label
                        ,'python':ast.Python
                        }.get(typ,None)
                    if type is None:
                        renpy.error("Unrecognized 'search' target: %r"%type)
                    found = modast.search_for_node_type(n,type,max_depth=depth)
                else:
                    criteria = \
                        {'say':lambda x: isinstance(x,ast.Say) and x.what==content
                        ,'if':lambda x: isinstance(x,ast.If) and any((e[0]==content for e in x.entries))
                        ,'menu':lambda x: isinstance(x,ast.Menu) and any((e[0]==content for e in x.items))
                        ,'show':lambda x: isinstance(x,ast.Show) and ' '.join(x.imspec[0])==content
                        ,'hide':lambda x: isinstance(x,ast.Hide) and ' '.join(x.imspec[0])==content
                        ,'call':lambda x: isinstance(x,ast.Call) and x.label==content
                        ,'scene':lambda x: isinstance(x,ast.Scene) and x.imspec is not None and ''.join(x.imspec[0])==content
                        ,'python':lambda x: isinstance(x,ast.Python) and x.code.source==content
                        }.get(typ,None)
                    if criteria is None:
                        renpy.error("Unrecognized 'search' target: %r" % typ)
                    found = modast.search_for_node_with_criteria(n,criteria,max_depth=depth)
                
                if found is None:
                    renpy.error("Failed to locate a node from 'search %s' with content\n%r\nstarting from node %s\nand searching for %u nodes.\nPerhaps another mod interfered with the structure of this scene?"%(typ,content,node_print_formatter(n),depth))
                return found

            class HereNodeOp(CanHaveInitBlock):
                __slots__ = ['typ','content','depth','fromvar','storeto','previous_herenode']
                def __init__(self, loc, block, typ, content, depth = None, fromvar = None, storeto = None):
                    super(HereNodeOp, self).__init__(loc, block)
                    self.typ = typ
                    self.content = content
                    self.depth = depth
                    self.fromvar = fromvar
                    self.storeto = storeto
                    self.previous_herenode = None
                
                def diff_info(self):
                    return (HereNodeOp, self.typ, self.content, self.depth, self.fromvar, self.storeto)

                def pre_execute(self):
                    statement_text = ('branch' if self.typ == 'branch' else (('find ' if self.depth is None else 'search ')+self.typ))
                    ast.statement_name("linkmod %s"%statement_text)

                    n = renpy.python.store_dicts["store"].get(hn, None)
                    self.previous_herenode = n
                    found = None
                    if (not self.depth and self.typ != 'branch') or (self.typ == 'label' and self.content): # 'find' statements
                        found = find(self.typ,self.content)
                    else: # 'search' or 'branch' statements
                        if n is None:
                            renpy.error("The current node must already be defined to\nrun a 'search' or 'branch' statement. Try running a 'find' in this file first!")
                        elif self.typ == 'branch':
                            found = branch(n,self.content)
                        else:
                            found = search(self.typ,n,self.content,self.depth)
                    if found is None:
                        renpy.error("Failed to '%s' with content %r"%(statement_text,self.content))
                    else:
                        set_herenode(found)
                        if self.storeto is not None:
                            renpy.python.store_dicts["store"][self.storeto] = found
                
                def post_execute(self):
                    set_herenode(self.previous_herenode)
            
            
            linkstep_regex = str('(?:label|jump|menu|if|s(?:cene|how|ay)|hide|python)\\b')

            def linkstep_specifier(typ,keywords=[]):
                opts = \
                    { 'label':lambda l:l.string() or l.label_name()
                    , 'say':Lexer.string
                    , 'scene':lambda l:l.string() or parse_image_name_forgiving(l,keywords=keywords)
                    , 'show':lambda l:l.string() or parse_image_name_forgiving(l,keywords=keywords)
                    , 'hide':lambda l:l.string() or parse_image_name_forgiving(l,keywords=keywords)
                    , 'jump':lambda l:l.string() or l.label_name()
                    , 'menu':Lexer.string
                    , 'if':Lexer.string
                    , 'python':Lexer.string
                    }
                if typ not in opts:
                    renpy.error("link find/search typ not yet fully implemented: %r"%typ)
                return opts[typ]

            def parse_subblock(l):
                block = []
                if l.match(':'):
                    l.expect_eol()
                    l.expect_block("find statement block")
                    block = renpy.parser.parse_block(l.subblock_lexer(True))
                return block

            @renpy.parser.statement('find')
            def parse_stmt_find(l,loc):
                typ = l.require(linkstep_regex,"node type specifier")
                content = linkstep_specifier(typ,keywords=['as'])(l)
                storeto = None
                if l.keyword('as'):
                    storeto = l.require(l.name,"node storage variable name")

                rv = HereNodeOp(loc,parse_subblock(l),typ,content,storeto=storeto)
                l.advance()
                if not l.init:
                    rv = ast.Init(loc, [ rv ], l.init_offset)
                return rv

            @renpy.parser.statement('search')
            def parse_stmt_search(l,loc):
                typ = l.require(linkstep_regex,"node type specifier")
                content = linkstep_specifier(typ,keywords=['as','for','from'])(l)
                depth = 200
                storeto = None
                fromvar = None
                while True:
                    if l.keyword('for'):
                        depth = int(l.require(l.integer,"maximum depth"))
                    elif l.keyword('from'):
                        fromvar = l.require(l.name,"search origin node")
                    elif l.keyword('as'):
                        storeto = l.require(l.name,"node storage variable name")
                    else:
                        break

                rv = HereNodeOp(loc,parse_subblock(l),typ,content,depth=depth,fromvar=fromvar,storeto=storeto)
                l.advance()
                if not l.init:
                    rv = ast.Init(loc, [ rv ], l.init_offset)
                return rv

            @renpy.parser.statement('branch')
            def parse_stmt_branch(l,loc):
                condition = parse_condition(l,allow_blank=True)

                storeto = None
                while True:
                    if l.keyword('as'):
                        storeto = l.require(l.name,"node storage variable name")
                    elif l.keyword('from'):
                        renpy.error("'from' keyword not supported for branch statements to prevent sanity issues.")
                    else:
                        break

                rv = HereNodeOp(loc,parse_subblock(l),'branch',condition,storeto=storeto)
                l.advance()
                if not l.init:
                    rv = ast.Init(loc, [ rv ], l.init_offset)
                return rv
        linkmod_commands_setting_new_herenode()

        def linkmod_next():
            def parse(l):
                l.expect_eol()
            
            def execute(_):
                set_herenode(get_herenode("run a 'next' statement").next)

            renpy.statements.register(
                'next',
                parse=parse,
                execute=execute,
                init = True
            )
        linkmod_next()

        def linkmod_jumpcallto():
            def parse(is_call=False):
                def wrap(l):
                    name = l.require(l.label_name,"label")
                    fromvar = None
                    returnto = None
                    if l.keyword('from'):
                        fromvar = l.require(l.name,"from node variable")
                    if is_call and l.keyword('return'):
                        returnto = l.require(l.name,"return node variable")
                    return (is_call,fromvar,returnto,name)
                return wrap
            
            def execute(dat):
                if not renpy.game.context().init_phase:
                    renpy.error("jumpcallto may only be executed at init time.\nIf you need more advanced modding features, you may want\nto look at using the `modast` module directly.\nIf you need to run past this statement,\ntry unwrapping your linking operations from the surrounding Init block.")

                is_call,fromvar,returnto,name = dat
                if fromvar is None:
                    fromvar = hn
                origin = get_herenode("link a mod statement",fromvar)
                if is_call:
                    if returnto is not None:
                        # Grab the return node from a variable unless it's 'here', then grab the origin node.
                        # Need to do this because if we set a return node, it will return to the beginning of the
                        #  statement, rather than the end, forming an infinite loop in some cases.
                        returnto = get_herenode("return from a call",returnto if returnto != 'here' else None)
                    modast.call_hook(origin,modast.find_label(name),None,returnto)
                else:
                    modast.hook_opcode(origin,None).chain(modast.find_label(name))

            renpy.statements.register(
                'callto',
                parse= parse(is_call=True),
                execute=execute,
                init = True
            )

            renpy.statements.register(
                'jumpto',
                parse=parse(is_call=False),
                execute=execute,
                init = True
            )
        linkmod_jumpcallto()

        def linkmod_add():
            def parse(l):
                condition = parse_condition(l)
                l.require(str("branch"),"branch keyword")
                label = l.require(l.label_name,"label")
                l.expect_eol()
                return (condition,label)
            
            def execute(dat):
                condition,label = dat
                branch_block = modast.find_label(label)
                n = renpy.python.store_dicts["store"][hn]
                if n is None:
                    renpy.error("The current node must already be defined 'add' a branch to it. Try running a 'find' in this file first!")
                elif isinstance(n,ast.Menu):
                    # TODO: Support adding conditions here. May require separating 'add option' code from 'add cond'
                    h = ml.get_menu_hook(n)
                    h.add_item(condition,branch_block,condition="True")
                elif isinstance(n,ast.If):
                    if n.entries[-1][0] == 'True' and condition == 'True':
                        n.entries[-1] = ('True',branch_block)
                    else:
                        n.entries.append((condition,branch_block))
                else:
                    renpy.error("I can't add a branch to a %r!"%type(n))
            
            renpy.statements.register(
                'add',
                parse=parse,
                execute=execute,
                init = True
            )
        linkmod_add()

        def linkmod_change():
            def parse(l):
                condition = parse_condition(l)

                if l.keyword('to') is None:
                    renpy.error("Expected 'to' keyword to complete 'change' statement.")

                newcondition = parse_condition(l)
                l.expect_eol()
                return (condition,newcondition)

            def execute(dat):
                condition,newcondition = dat
                n = renpy.python.store_dicts["store"][hn]
                if n is None:
                    renpy.error("The current node must already be defined to 'change' a branch on it. Try running a 'find' in this file first!")
                elif isinstance(n,ast.Menu):
                    # TODO: Support changing conditions here. May require separating 'change option' code from 'change cond'
                    h = ml.get_menu_hook(n)
                    for i, (label, src, block) in enumerate(h.get_items()):
                        if label == condition:
                            if newcondition is 'False':
                                h.menu.items[i] = (label, 'False', block)
                            elif newcondition is 'True':
                                h.menu.items[i] = (label, 'True', block)
                            else:
                                h.menu.items[i] = (newcondition, src, block)
                            return
                    renpy.error("I couldn't find a menu item labeled %r in the menu %r!"%(condition,node_print_formatter(n)))
                elif isinstance(n,ast.If):
                    for i,e in enumerate(n.entries):
                        if e[0] == condition:
                            n.entries[i] = (newcondition, e[1])
                            return
                    renpy.error("I couldn't find the condition %r in the if statement %s!"%(condition,node_print_formatter(n)))
                else:
                    renpy.error("I can't 'change' a branch on a %r!"%type(n))

            renpy.statements.register(
                'change',
                parse=parse,
                execute=execute,
                init = True
            )
        linkmod_change()

        def linkmod_link():
            def parse(l):
                label = l.require(l.label_name,"label")
                l.expect_eol()
                return label
            
            def execute(dat):
                label = dat
                l = modast.find_label(label)
                if l is None:
                    renpy.error("Could not find label named %r."%label)
                
                n = renpy.python.store_dicts["store"][hn]
                if n is None:
                    renpy.error("The current node must already be defined to 'link' to it. Try running a 'find' in this file first!")
                else:
                    l.chain(n)

            renpy.statements.register(
                'link',
                parse=parse,
                execute=execute,
                init = True
            )
        linkmod_link()