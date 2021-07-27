python early:
    def linkmod_main():
        import modloader.modast
        from modloader.modgame import base as ml
        from modloader.modgame import sprnt
        from renpy.parser import Lexer

        hn = 'linkmod_here_node'
        bn = 'linkmod_branch_node'
        hns = 'linkmod_here_node_stack'

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
            

        def linkmod_findsearch():
            linkstep_regex = str('(?:label|jump|menu|if|s(?:cene|how|ay)|hide|python)\\b')

            class LinkStep:
                __slots__ = ['typ','content','depth']
                def __init__(self, l, isglobal):
                    opts = \
                        { 'label':lambda l:l.string() or l.label_name()
                        , 'say':Lexer.string
                        , 'scene':lambda l:l.string() or parse_image_name_forgiving(l,keywords=['for','as'])
                        , 'show':lambda l:l.string() or parse_image_name_forgiving(l,keywords=['for','as'])
                        , 'hide':lambda l:l.string() or parse_image_name_forgiving(l,keywords=['for','as'])
                        , 'jump':lambda l:l.string() or l.label_name()
                        , 'menu':Lexer.string
                        , 'if':Lexer.string
                        , 'python':Lexer.string
                        }
                    
                    self.typ = l.require(linkstep_regex,"node type specifier")
                    if self.typ not in opts:
                        renpy.error("link step typ not yet fully implemented: %r"%typ)
                    self.content = opts[self.typ](l)

                    self.depth = None
                    self.storeto = None
                    def additional_keywords(l):
                        if not isglobal:
                            if l.keyword('for'):
                                self.depth = int(l.require(l.integer,"maximum depth"))
                            else:
                                self.depth = 200

                        if l.keyword('as'):
                            self.storeto = l.require(l.name,"storeto target")

                    while additional_keywords(l):
                        pass

                    l.expect_eol()

            def parse(isglobal=False):
                def wrap(l):
                    return LinkStep(l,isglobal)
                return wrap
            
            def lint(ls):
                if ls.depth is not None and ls.depth < 1:
                    renpy.error("'search %s' statement must be allowed to search at least one node ahead!"%ls.typ)
                if ls.depth is None and not content:
                    renpy.error("'find %s' statement needs some information to narrow the search!"%ls.typ)
                
                if ls.typ=='label' and ls.content and not renpy.game.script.has_label(ls.content):
                    renpy.error("Could not find label %r!"%ls.content)
                elif ls.typ=='say' and ls.content and ls.depth is None:
                    one = False
                    for node in renpy.game.script.all_stmts:
                        if isinstance(node, renpy.ast.Say) and node.what == ls.content:
                            if not one:
                                one = True
                            else:
                                renpy.error("Found at least two say nodes with content %r!"%ls.content)
                    if not one:
                        renpy.error("Say node with content %r not found!"%ls.content)
                else:
                    renpy.error("Lint unimplemented for find typ %r"%ls.typ)
            
            def execute(ls):
                # sprnt("Exec: 'findsearch %s %r'"%(ls.typ,ls.content))
                def find_show(imspec):
                    for node in renpy.game.script.all_stmts:
                        if isinstance(node, renpy.ast.Show) and ' '.join(node.imspec[0])==ls.content:
                            return node
                
                def find_hide(imspec):
                    for node in renpy.game.script.all_stmts:
                        if isinstance(node, renpy.ast.Hide) and ' '.join(node.imspec[0])==ls.content:
                            return node

                if (ls.depth is None) or (ls.typ == 'label' and ls.content): # Find statement or search statement for label with name
                    fn =\
                        {'label':modast.find_label
                        ,'jump':modast.find_jump_target
                        ,'menu':modast.find_menu
                        ,'show':find_show
                        ,'hide':find_hide
                        ,'say':modast.find_say
                        ,'python':modast.find_python_statement
                        }.get(ls.typ,lambda _:renpy.error("Unrecognized 'find' typ: %r"%(ls.typ)))

                    n = fn(ls.content)
                    if n is None:
                        renpy.error("Failed to find node from expression 'find %s' with content %r"%(ls.typ,ls.content))
                else: # Search statement
                    fromnode = renpy.python.store_dicts["store"].get(hn,None)
                    n = None
                    if fromnode is None:
                        renpy.error("The current node must already be defined to run a 'search' statement. Try running a 'find' in this file first!")
                    elif not ls.content:
                        type = \
                            {'say':renpy.ast.Say
                            ,'if':renpy.ast.If
                            ,'menu':renpy.ast.Menu
                            ,'show':renpy.ast.Show
                            ,'hide':renpy.ast.Hide
                            ,'call':renpy.ast.Call
                            ,'scene':renpy.ast.Scene
                            ,'label':renpy.ast.Label
                            }.get(ls.typ,None)
                        if type is None:
                            renpy.error("Unrecognized 'search' target: %r"%type)
                        n = modast.search_for_node_type(fromnode,type,max_depth=ls.depth)
                        if n is None:
                            renpy.error("I couldn't find a node of type %r starting from %r"%(type,fromnode))
                    else:
                        criteria = \
                            {'say':lambda x: isinstance(x,renpy.ast.Say) and x.what==ls.content
                            ,'if':lambda x: isinstance(x,renpy.ast.If) and any((e[0]==ls.content for e in x.entries))
                            ,'menu':lambda x: isinstance(x,renpy.ast.Menu) and any((e[0]==ls.content for e in x.items))
                            ,'show':lambda x: isinstance(x,renpy.ast.Show) and ' '.join(x.imspec[0])==ls.content
                            ,'hide':lambda x: isinstance(x,renpy.ast.Hide) and ' '.join(x.imspec[0])==ls.content
                            ,'call':lambda x: isinstance(x,renpy.ast.Call) and x.label==ls.content
                            ,'scene':lambda x: isinstance(x,renpy.ast.Scene) and x.imspec is not None and ''.join(x.imspec[0])==ls.content
                            }.get(ls.typ,None)
                        if criteria is None:
                            renpy.error("Unrecognized 'search' target: %r" % ls.typ)
                        n = modast.search_for_node_with_criteria(fromnode,criteria,max_depth=ls.depth)
                        if n is None:
                            renpy.error("I couldn't find a node matching type %r with content \n    %r\n starting from %r"%(ls.typ,ls.content,fromnode))

                renpy.python.store_dicts["store"][hn] = n
                if ls.storeto is not None:
                    renpy.python.store_dicts["store"][ls.storeto] = n

            renpy.statements.register(
                'find',
                parse=parse(isglobal=True),
                lint = lint,
                execute=execute,
                init = True
            )
            renpy.statements.register(
                'search',
                parse=parse(isglobal=False),
                lint = lint,
                execute=execute,
                init = True
            )
        linkmod_findsearch()

        def linkmod_next():
            def parse(l):
                l.expect_eol()
            
            def lint(_):
                pass
            
            def execute(_):
                current_node = renpy.python.store_dicts["store"].get(hn,None)
                if current_node is None:
                    renpy.error("The current node must already be defined to run a 'next' statement. Try running a 'find' in this file first!")
                else:
                    renpy.python.store_dicts["store"][hn] = current_node.next

            renpy.statements.register(
                'next',
                parse=parse,
                lint = lint,
                execute=execute,
                init = True
            )
        linkmod_next()

        def linkmod_jumpcallto():
            def parse(is_call=False):
                def wrap(l):
                    name = l.require(l.label_name,"label")
                    return (is_call,name)
                return wrap

            def lint(dat):
                l = modast.find_label(dat[1])
                if l is None:
                    renpy.error("Could not find label named %r."%name)
            
            def execute(dat):
                is_call,name = dat
                origin = renpy.python.store_dicts["store"][hn]
                if origin is None:
                    renpy.error("The current node must already be defined to link a mod %r statement. Try running a 'find' in this file first!"%('call' if is_call else 'jump'))
                if is_call:
                    modast.call_hook(origin,modast.find_label(name),None,None)
                else:
                    modast.hook_opcode(origin,None).chain(modast.find_label(name))

            renpy.statements.register(
                'callto',
                parse= parse(is_call=True),
                lint = lint,
                execute=execute,
                init = True
            )

            renpy.statements.register(
                'jumpto',
                parse=parse(is_call=False),
                lint = lint,
                execute=execute,
                init = True
            )
        linkmod_jumpcallto()

        def linkmod_branch():
            class Branch(renpy.ast.While):
                __slots__ = ['previous_herenode']

                def __init__(self, loc, condition, block):
                    super(Branch, self).__init__(loc,condition,block)
                    self.previous_herenode = None

                def execute(self):
                    # sprnt("Exec: 'branch %s' at hn %r with prevhn %r"%(self.condition,renpy.python.store_dicts["store"][hn],self.previous_herenode))
                    renpy.ast.next_node(self.next)
                    renpy.ast.statement_name('block statement')

                    if self.previous_herenode is not None:
                        renpy.python.store_dicts["store"][hn] = self.previous_herenode
                        self.previous_herenode = None
                    else:
                        renpy.ast.next_node(self.block[0])
                        n = renpy.python.store_dicts["store"].get(hn,None)
                        self.previous_herenode = n
                        if n is None:
                            renpy.error("The current node must already be defined to descend into a branch. Try running a 'find' in this file first!")
                        elif isinstance(n,renpy.ast.Menu):
                            if self.condition is None:
                                renpy.error("I expected a menu item to branch to!")
                            choice = ml.get_menu_hook(n).get_item(self.condition)
                            if choice is None:
                                renpy.error("I couldn't find a menu item labeled %r in the menu %r!"%(self.condition,n))
                            n = choice[2][0]
                        elif isinstance(n,renpy.ast.If):
                            arg = self.condition if self.condition is not None else 'True'
                            for e in n.entries:
                                if e[0] == arg:
                                    n = e[1][0]
                                    break
                            else:
                                renpy.error("I couldn't find the condition %r in the if statement %r!"%(self.condition,n))
                        else:
                            renpy.error("I can't branch into a %r!"%type(n))
                        renpy.python.store_dicts["store"][hn] = n
            
            @renpy.parser.statement("branch")
            def parse(l, loc):
                condition = l.string()
                if condition is None:
                    l.keyword('else') # Allow using else as the target of a branch.
                elif condition == 'else':
                    condition = None # The 'else' statement is a branch, not a condition str.
                l.require(str(':'))
                l.expect_eol()
                l.expect_block("branch statement")
                block = renpy.parser.parse_block(l.subblock_lexer())
                l.advance()
                return Branch(loc,condition,block)
        linkmod_branch()

        def linkmod_add():
            def parse(l):
                condition = l.require(l.string,"branch")
                l.require(str("branch"),"branch keyword")
                label = l.require(l.label_name,"label")
                l.expect_eol()
                return (condition,label)
            
            def lint(dat):
                condition,label = dat
                l = modast.find_label(label)
                if l is None:
                    renpy.error("Could not find label named %r."%label)
            
            def execute(dat):
                condition,label = dat
                branch_block = modast.find_label(label)
                n = renpy.python.store_dicts["store"][hn]
                if n is None:
                    renpy.error("The current node must already be defined 'add' a branch to it. Try running a 'find' in this file first!")
                elif isinstance(n,renpy.ast.Menu):
                    # TODO: Support adding conditions here. May require separating 'add option' code from 'add cond'
                    h = ml.get_menu_hook(n)
                    h.add_item(condition,branch_block,condition="True")
                elif isinstance(n,renpy.ast.If):
                    if n.entries[-1][0] == 'True' and self.condition == 'True':
                        n.entries[-1] = ('True',branch_block)
                    else:
                        n.entries.append((condition,branch_block))
                else:
                    renpy.error("I can't add a branch to a %r!"%type(n))
            
            renpy.statements.register(
                'add',
                parse=parse,
                lint = lint,
                execute=execute,
                init = True
            )
        linkmod_add()

        def linkmod_change():
            def parse(l):
                condition = l.require(l.string,"existing branch")
                if l.keyword('to') is None:
                    renpy.error("Expected 'to' keyword to complete 'change' statement.")
                newcondition = l.require(l.string,"new condition")
                l.expect_eol()
                return (condition,newcondition)
            
            def execute(dat):
                condition,newcondition = dat
                n = renpy.python.store_dicts["store"][hn]
                if n is None:
                    renpy.error("The current node must already be defined to 'change' a branch on it. Try running a 'find' in this file first!")
                elif isinstance(n,renpy.ast.Menu):
                    # TODO: Support changing conditions here. May require separating 'change option' code from 'change cond'
                    h = ml.get_menu_hook(n)
                    choice = h.get_item(condition)
                    if choice is None:
                        self.error("I couldn't find a menu item labeled %r in the menu %r!"%(arg,n))
                    h.delete_item(condition)
                    h.add_item(newcondition,choice[1],choice[2])
                elif isinstance(n,renpy.ast.If):
                    if condition == 'else':
                        condition = 'True'
                    if newcondition == 'else':
                        newcondition = 'True'
                    for e in n.entries:
                        if e[0] == condition:
                            n.entries.remove(e)
                            n.entries.append((newcondition,e[1]))
                            return
                    self.error("I couldn't find the condition %r in the if statement %r!"%(condition,n))
                else:
                    renpy.error("I can't 'change' a branch on a %r!"%type(n))
            
            renpy.statements.register(
                'change',
                parse=parse,
                execute=execute,
                init = True
            )
        linkmod_change()

        def linkmod_delete():
            # TODO: Implement this.
            pass
        linkmod_delete()

        def linkmod_link():
            def parse(l):
                label = l.require(l.label_name,"label")
                l.expect_eol()
                return label
            
            def lint(dat):
                label = dat
                l = modast.find_label(label)
                if l is None:
                    renpy.error("Could not find label named %r."%label)
            
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
                lint = lint,
                execute=execute,
                init = True
            )
        linkmod_link()
    linkmod_main()