import sys
from lexer import Symbol, is_list, is_symbol, expr_to_str

def fn_display(expr):
    print expr_to_str(expr),

def fn_concat(args):
    return ''.join(args)

def fn_list(*args):
    return args

builtins = {
    # mathematical operators
    '+': lambda a, b: a + b,
    '-': lambda a, b: a - b,
    '*': lambda a, b: a * b,
    '/': lambda a, b: a / b,
    '%': lambda a, b: a % b,

    # comparison operators
    '=': lambda a, b: a == b,
    '>': lambda a, b: a > b,
    '>=': lambda a, b: a >= b,
    '<': lambda a, b: a < b,
    '<=': lambda a, b: a <= b,
    'eq': lambda a, b: a == b,

    # type predicates
    'null?': lambda x: not x,
    'boolean?': lambda x: bool == type(x),
    'string?': lambda x: str == type(x),
    'list?': is_list,
    'symbol?': is_symbol,
    'procedure?': lambda x: isinstance(x, Lambda),

    # converters
    'number->string': str,
    'symbol->string': lambda symbol: symbol.name,
    'string->symbol': lambda name: Symbol(name),

    # list manipulation
    'list': fn_list,
    'car': lambda lst: lst[0],
    'cdr': lambda lst: lst[1:],
    'cons': lambda x, lst: [x] + list(lst),

    # string manipulation
    'string-concatenate': fn_concat,

    # display procedures
    'display': fn_display,
    'newline': lambda: sys.stdout.write("\n")
}

def fexpr_quote(scope, expr):
    return expr

def fexpr_eval(scope, expr):
    return scope.eval(scope.eval(expr))

def fexpr_if(scope, cond, a, b):
    if scope.eval(cond):
        return scope.eval(a)

    return scope.eval(b)

def fexpr_lambda(scope, args, *body):
    for arg in args:
        if not is_symbol(arg):
            raise Exception("Syntax error: '%s' is not a valid arg name" % arg)

    return Lambda(args, body, scope)

def fexpr_define(scope, symbol, *tokens):
    try:
        value = scope.eval(tokens[0])
    except IndexError:
        value = None

    return scope.bind(symbol, value)

def fexpr_set(scope, symbol, value):
    if symbol.name not in scope.vars:
        raise Exception("Unbound variable: '%s'" % symbol.name)

    return scope.bind(symbol, scope.eval(value))

fexpr = {
    'quote': fexpr_quote,
    'eval': fexpr_eval,
    'if': fexpr_if,
    'lambda': fexpr_lambda,
    'define': fexpr_define,
    'set!': fexpr_set
}

class Lambda:

    def __init__(self, args, body, scope):
        self.args = args
        self.body = body
        self.scope = scope

    def __repr__(self):
        return '(lambda (%s) %s)' % (
                ' '.join(expr_to_str(arg) for arg in self.args),
                ' '.join(expr_to_str(line) for line in self.body))

    def call(self, args):
        i = 0
        for formal_arg in self.args:
            # all formal args are bound on each call
            if len(args) <= i:
                raise Exception("Missing parameter '%s'" % formal_arg.name)

            self.scope.bind(formal_arg, args[i])
            i += 1

        # return value from last statement
        return [self.scope.eval(stmt) for stmt in self.body][-1]

class NativeLambda(Lambda):

    def __init__(self, body):
        self.body = body

    def __repr__(self):
        return '<native-code>'

    def call(self, args):
        return self.body(*args)

class Scope:

    def __init__(self, parent):
        self.vars = {}
        self.parent = parent

    def __repr__(self):
        vars = "\n".join('%s: %s' % (str(key), str(value))
                for key, value in self.vars.items())

        return "\n----------\n%s\n----------" % vars

    def bind(self, symbol, value):
        self.vars[symbol.name] = value

    def deref(self, symbol):
        if symbol.name in self.vars:
            return self.vars[symbol.name]

        if self.parent:
            return self.parent.deref(symbol)

        raise Exception("Unbound variable: '%s'." % symbol.name)

    def eval(self, token):
        if is_list(token):
            if not len(token):
                return token

            if is_list(token[0]):
                return [self.eval(arg) for arg in token]

            symbol = token[0]

            if symbol.name in fexpr:
                return fexpr[symbol.name](self, *token[1:])

            fn = self.deref(symbol)

            if hasattr(fn, 'call'):
                return fn.call([self.eval(arg) for arg in token[1:]])
            else:
                raise Exception("'%s' is not callable" % symbol.name)

        if is_symbol(token):
            return self.deref(token)

        return token

class GlobalScope(Scope):

    def __init__(self):
        self.parent = None

        self.vars = { key: NativeLambda(value)
            for key, value in builtins.items() }
