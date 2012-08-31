import sys, native
from lexer import Lexer, Symbol

def is_list(token):
    return type(token) in [list, tuple]

def is_symbol(token):
    return isinstance(token, Symbol)

class Lambda:

    def __init__(self, args, body, scope):
        self.args = args
        self.body = body
        self.scope = scope

    def call(self, args):
        i = 0
        for formal_arg in self.args:
            # all formal args are bound on each call
            self.scope.define(formal_arg, args[i])
            i += 1

        # return value from last statement
        return self.scope.eval(self.body)[-1]

    def __repr__(self):
        return '(lambda (%s) %s)' % (
                ' '.join(str(arg) for arg in self.args),
                ' '.join(str(line) for line in self.body))

class Scope:

    def __init__(self, parent):
        self.vars = {}
        self.parent = parent

    def define(self, symbol, value):
        self.vars[symbol.name] = value

    def dereference(self, symbol):
        if symbol.name in self.vars:
            return self.vars[symbol.name]

        if self.parent:
            return self.parent.dereference(symbol)

        raise Exception("Unbound variable: '%s'." % symbol.name)

    def eval(self, thing):
        if not thing:
            return thing

        if is_list(thing):
            if is_list(thing[0]):
                return [self.eval(arg) for arg in thing]

            symbol = thing[0]

            if symbol.name == 'quote':
                return thing[1]

            if symbol.name == 'define':
                return self.define(thing[1], self.eval(thing[2]))

            if symbol.name == 'lambda':
                return self.define_lambda(thing[1], thing[2:])

            if symbol.name == 'if':
                return self.eval_if(*thing[1:])

            if symbol.name in native.forms:
                return native.call(self, symbol.name, thing[1:])

            fn = self.dereference(symbol)

            if not isinstance(fn, Lambda):
                raise Exception("'%s' is not callable" % symbol.name)

            return fn.call([self.eval(arg) for arg in thing[1:]])

        if is_symbol(thing):
            return self.dereference(thing)

        return thing

    def eval_if(self, cond, a, b):
        if self.eval(cond):
            return self.eval(a)

        return self.eval(b)

    def define_lambda(self, args, body):
        for arg in args:
            if not is_symbol(arg):
                raise Exception("Syntax error: '%s' is not a valid arg name" % arg)

        return Lambda(args, body, self)

def execute(fname):
    lexer = Lexer(fname)

    ast = lexer.get_ast(lexer.get_tokens())

    global_scope = Scope(None)

    return global_scope.eval(ast)

if __name__=="__main__":
    execute(sys.argv[1])
