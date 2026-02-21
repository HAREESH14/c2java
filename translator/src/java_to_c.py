# =============================================================================
#  java_to_c.py  -- Java -> C translator
#
#  Uses: javalang (Java AST)  +  pycparser (C AST / CGenerator)
# =============================================================================

from pycparser import c_ast, c_generator
import javalang.tree as jt

GEN = c_generator.CGenerator()


# ---------------------------------------------------------------------------
def _ctype(java_type: str) -> str:
    return {
        'int':'int','long':'long','short':'short','float':'float',
        'double':'double','char':'char','boolean':'int','void':'void',
        'String':'char*','Integer':'int','Long':'long',
        'Double':'double','Float':'float',
    }.get(java_type, java_type)

def _id(n):   return c_ast.ID(n)
def _const(k,v): return c_ast.Constant(k, v)
def _tdecl(n, ct): return c_ast.TypeDecl(n,[],None,c_ast.IdentifierType([ct]))
def _decl(n, t, init=None): return c_ast.Decl(n,[],[],[],[],t,init,None)

def _flat(stmts):
    out = []
    for s in (stmts or []):
        if s is None: continue
        if isinstance(s, list): out.extend(x for x in s if x)
        else: out.append(s)
    return out

def _compound(stmts): return c_ast.Compound(_flat(stmts))

def _is_vd(n):
    return isinstance(n, (jt.LocalVariableDeclaration, jt.VariableDeclaration))


# ---------------------------------------------------------------------------
class JavaToCVisitor:

    def __init__(self):
        self.has_printf   = False
        self.has_string_h = False
        self.has_hashmap  = False
        self.fwd_decls    = []
        self._fi_ctr      = 0

    # ── Top-level ─────────────────────────────────────────────────────────────
    def translate(self, tree: jt.CompilationUnit) -> str:
        chunks = []
        for m in tree.types[0].body:
            if isinstance(m, jt.MethodDeclaration):
                chunks.append(self._method(m))

        lines = ['#include <stdio.h>', '#include <stdlib.h>']
        if self.has_string_h: lines.append('#include <string.h>')
        if self.has_hashmap:  lines.append(self._hashmap_code())
        lines.append('')
        for fd in self.fwd_decls: lines.append(fd)
        if self.fwd_decls: lines.append('')
        for c in chunks: lines += [c, '']
        return '\n'.join(lines)

    # ── Method -> C function ──────────────────────────────────────────────────
    def _method(self, m: jt.MethodDeclaration) -> str:
        is_main   = m.name == 'main'
        ret       = 'int' if is_main else (_ctype(m.return_type.name) if m.return_type else 'void')
        params    = []
        if not is_main:
            for p in (m.parameters or []):
                base = _ctype(p.type.name)
                dims = list(getattr(p.type,'dimensions',[]) or [])
                if p.varargs or dims:
                    params.append(_decl(p.name, c_ast.ArrayDecl(_tdecl(p.name,base),None,[])))
                else:
                    params.append(_decl(p.name, _tdecl(p.name, base)))

        pl   = c_ast.ParamList(params) if params else None
        body = _flat(self._stmts(m.body or []))
        if is_main: body.append(c_ast.Return(_const('int','0')))

        fd   = c_ast.FuncDecl(pl, _tdecl(m.name, ret))
        decl = _decl(m.name, fd)
        fdef = c_ast.FuncDef(decl=decl, param_decls=None, body=_compound(body))
        if not is_main:
            self.fwd_decls.append(GEN.visit(decl) + ';')
        return GEN.visit(fdef)

    # ── Statement list ────────────────────────────────────────────────────────
    def _stmts(self, lst):
        out = []
        for s in (lst or []):
            r = self._stmt(s)
            if r is None: continue
            if isinstance(r, list): out.extend(x for x in r if x)
            else: out.append(r)
        return out

    def _block(self, node) -> c_ast.Compound:
        if node is None: return _compound([])
        if isinstance(node, jt.BlockStatement):
            return _compound(self._stmts(node.statements or []))
        if isinstance(node, list): return _compound(self._stmts(node))
        r = self._stmt(node)
        return _compound(r if isinstance(r,list) else ([r] if r else []))

    # ── Statement dispatcher ──────────────────────────────────────────────────
    def _stmt(self, node):
        if node is None: return None
        if _is_vd(node):                         return self._var_decl(node)
        if isinstance(node, jt.IfStatement):      return self._if(node)
        if isinstance(node, jt.ForStatement):     return self._for(node)
        if isinstance(node, jt.WhileStatement):
            return c_ast.While(self._expr(node.condition), self._block(node.body))
        if isinstance(node, jt.DoStatement):
            return c_ast.DoWhile(self._expr(node.condition), self._block(node.body))
        if isinstance(node, jt.ReturnStatement):
            return c_ast.Return(self._expr(node.expression) if node.expression else None)
        if isinstance(node, jt.BreakStatement):    return c_ast.Break()
        if isinstance(node, jt.ContinueStatement): return c_ast.Continue()
        if isinstance(node, jt.SwitchStatement):   return self._switch(node)
        if isinstance(node, jt.StatementExpression): return self._stmt_expr(node.expression)
        if isinstance(node, jt.BlockStatement):    return self._block(node)
        # Graceful error recovery — emit a comment instead of crashing
        return None

    # ── Variable declaration ──────────────────────────────────────────────────
    def _var_decl(self, node):
        results = []
        base_j  = node.type.name
        if base_j == 'HashMap':
            self.has_hashmap = True
            for d in node.declarators:
                results.append(_decl(d.name, _tdecl(d.name,'HashMap'),
                                     c_ast.FuncCall(_id('hashmap_create'), None)))
            return results if len(results)!=1 else results[0]

        t_dims = list(getattr(node.type,'dimensions',[]) or [])
        base_c = _ctype(base_j)

        for d in node.declarators:
            name   = d.name
            d_dims = list(getattr(d,'dimensions',[]) or [])
            ndim   = len(t_dims) + len(d_dims)
            init   = d.initializer

            if ndim == 0:
                results.append(_decl(name, _tdecl(name,base_c),
                                     self._expr(init) if init is not None else None))
            elif ndim == 1:
                if isinstance(init, jt.ArrayCreator):
                    dim_e = self._expr(init.dimensions[0]) if init.dimensions else None
                    results.append(_decl(name, c_ast.ArrayDecl(_tdecl(name,base_c),dim_e,[])))
                elif isinstance(init, jt.ArrayInitializer):
                    vals = [self._expr(v) for v in init.initializers]
                    results.append(_decl(name, c_ast.ArrayDecl(_tdecl(name,base_c),None,[]),
                                        c_ast.InitList(vals)))
                else:
                    results.append(_decl(name, c_ast.ArrayDecl(_tdecl(name,base_c),None,[])))
            elif ndim == 2:
                re, ce = (None, None)
                if isinstance(init, jt.ArrayCreator) and len(init.dimensions)>=2:
                    re, ce = self._expr(init.dimensions[0]), self._expr(init.dimensions[1])
                inner = c_ast.ArrayDecl(_tdecl(name,base_c),ce,[])
                results.append(_decl(name, c_ast.ArrayDecl(inner,re,[])))

        return results if len(results)!=1 else results[0]

    # ── Statement expression ──────────────────────────────────────────────────
    def _stmt_expr(self, expr):
        if expr is None: return None
        if isinstance(expr, jt.Assignment):
            return c_ast.Assignment(expr.type,
                                    self._expr(expr.expressionl),
                                    self._expr(expr.value))
        if isinstance(expr, jt.MethodInvocation):
            return self._call_expr(expr)
        if isinstance(expr, jt.MemberReference):
            return self._member(expr)
        return None

    # ── if / else ─────────────────────────────────────────────────────────────
    def _if(self, node: jt.IfStatement):
        cond = self._expr(node.condition)
        ift  = self._block(node.then_statement)
        iff  = None
        if node.else_statement:
            iff = (self._if(node.else_statement)
                   if isinstance(node.else_statement, jt.IfStatement)
                   else self._block(node.else_statement))
        return c_ast.If(cond, ift, iff)

    # ── for / for-each ────────────────────────────────────────────────────────
    def _for(self, node: jt.ForStatement):
        ctrl = node.control
        if isinstance(ctrl, jt.EnhancedForControl):
            return self._foreach(ctrl, node.body)

        init = None
        if ctrl.init:
            raw = ctrl.init
            if _is_vd(raw):
                v = self._var_decl(raw)
                init = v[0] if isinstance(v,list) else v
            elif isinstance(raw, list) and raw:
                v = self._var_decl(raw[0]) if _is_vd(raw[0]) else self._stmt(raw[0])
                init = v[0] if isinstance(v,list) else v
            else:
                init = self._stmt(raw)

        cond = self._expr(ctrl.condition) if ctrl.condition else None

        upd = None
        if ctrl.update:
            ups = ctrl.update if isinstance(ctrl.update,list) else [ctrl.update]
            uc  = []
            for u in ups:
                if isinstance(u, jt.MemberReference): uc.append(self._member(u))
                elif isinstance(u, jt.Assignment):
                    uc.append(c_ast.Assignment(u.type,self._expr(u.expressionl),self._expr(u.value)))
                else:
                    e = self._expr(u)
                    if e: uc.append(e)
            upd = uc[0] if len(uc)==1 else (c_ast.ExprList(uc) if uc else None)

        return c_ast.For(init, cond, upd, self._block(node.body))

    def _foreach(self, ctrl: jt.EnhancedForControl, body):
        self._fi_ctr += 1
        idx   = f'_fi{self._fi_ctr}'
        vname = ctrl.var.declarators[0].name
        base_c = _ctype(ctrl.var.type.name)
        ae    = self._expr(ctrl.iterable)

        init  = _decl(idx, _tdecl(idx,'int'), _const('int','0'))
        sz    = c_ast.FuncCall(_id('sizeof'), c_ast.ExprList([ae]))
        esz   = c_ast.FuncCall(_id('sizeof'), c_ast.ExprList([c_ast.ArrayRef(ae,_const('int','0'))]))
        cond  = c_ast.BinaryOp('<', _id(idx), c_ast.BinaryOp('/',sz,esz))
        upd   = c_ast.UnaryOp('p++', _id(idx))
        vd    = _decl(vname, _tdecl(vname,base_c), c_ast.ArrayRef(ae, _id(idx)))
        inner = [vd] + self._stmts(
            body.statements if isinstance(body,jt.BlockStatement) else
            (body if isinstance(body,list) else [body]))
        return c_ast.For(init, cond, upd, _compound(inner))

    # ── switch ────────────────────────────────────────────────────────────────
    def _switch(self, node: jt.SwitchStatement):
        # javalang: SwitchStatementCase.case is a LIST [Literal] or [] for default
        cases = []
        for case in (node.cases or []):
            ss = _flat(self._stmts(case.statements or []))
            case_exprs = case.case  # always a list in javalang
            if case_exprs:          # non-empty list -> case N:
                cases.append(c_ast.Case(self._expr(case_exprs[0]), ss))
            else:                   # empty list -> default:
                cases.append(c_ast.Default(ss))
        return c_ast.Switch(self._expr(node.expression), c_ast.Compound(cases))

    # ── Expression builder ────────────────────────────────────────────────────
    def _expr(self, node):
        if node is None: return None
        if isinstance(node, jt.Literal):       return self._literal(node)
        if isinstance(node, jt.MemberReference): return self._member(node)
        if isinstance(node, jt.MethodInvocation): return self._call_expr(node)
        if isinstance(node, jt.BinaryOperation):
            return c_ast.BinaryOp(node.operator,
                                  self._expr(node.operandl),
                                  self._expr(node.operandr))
        if isinstance(node, jt.Assignment):
            return c_ast.Assignment(node.type,
                                    self._expr(node.expressionl),
                                    self._expr(node.value))
        if isinstance(node, jt.TernaryExpression):
            cs = GEN.visit(self._expr(node.condition))
            ts = GEN.visit(self._expr(node.if_true))
            fs = GEN.visit(self._expr(node.if_false))
            return _const('int', f'({cs} ? {ts} : {fs})')
        if isinstance(node, jt.ClassCreator):
            if node.type.name == 'HashMap':
                self.has_hashmap = True
                return c_ast.FuncCall(_id('hashmap_create'), None)
            return c_ast.FuncCall(_id(node.type.name), None)
        if isinstance(node, jt.ArrayCreator):
            return self._expr(node.dimensions[0]) if node.dimensions else _const('int','0')
        if isinstance(node, jt.Cast):
            return c_ast.Cast(
                c_ast.Typename(None,[],None,_tdecl('',_ctype(node.type.name))),
                self._expr(node.expression))
        return _const('int','0')

    def _literal(self, node: jt.Literal):
        v = node.value
        if v in ('true','false'): return _const('int','1' if v=='true' else '0')
        if v.startswith('"'): return _const('string',v)
        if v.startswith("'"): return _const('char',v)
        if v[-1] in ('L','l'): return _const('long',v[:-1])
        if v[-1] in ('f','F'): return _const('float',v[:-1])
        if '.' in v: return _const('double',v)
        return _const('int',v)

    def _member(self, node: jt.MemberReference):
        pre  = list(node.prefix_operators  or [])
        post = list(node.postfix_operators or [])
        base = _id(node.member)
        for sel in (node.selectors or []):
            if isinstance(sel, jt.ArraySelector):
                base = c_ast.ArrayRef(base, self._expr(sel.index))
        if pre:  return c_ast.UnaryOp(pre[0], base)
        if post: return c_ast.UnaryOp('p'+post[0], base)
        return base

    def _call_expr(self, inv: jt.MethodInvocation):
        q    = inv.qualifier or ''
        m    = inv.member
        args = [self._expr(a) for a in (inv.arguments or [])]
        al   = c_ast.ExprList(args) if args else None

        if m in ('println','print','printf') and ('System.out' in q or q=='out'):
            self.has_printf = True
            return self._printf(inv)

        if m == 'equals' and q:
            self.has_string_h = True
            return c_ast.BinaryOp('==',
                c_ast.FuncCall(_id('strcmp'),c_ast.ExprList([_id(q)]+args)),_const('int','0'))
        if m == 'length' and q and not args:
            self.has_string_h = True
            return c_ast.FuncCall(_id('strlen'), c_ast.ExprList([_id(q)]))
        if m == 'put' and q:
            self.has_hashmap = True
            return c_ast.FuncCall(_id('hashmap_put'),
                c_ast.ExprList([c_ast.UnaryOp('&',_id(q))]+args))
        if m == 'get' and q:
            self.has_hashmap = True
            return c_ast.FuncCall(_id('hashmap_get'),
                c_ast.ExprList([c_ast.UnaryOp('&',_id(q))]+args))
        if m == 'containsKey' and q:
            self.has_hashmap = True
            return c_ast.FuncCall(_id('hashmap_contains'),
                c_ast.ExprList([c_ast.UnaryOp('&',_id(q))]+args))

        return c_ast.FuncCall(_id(m), al)

    def _printf(self, inv: jt.MethodInvocation):
        self.has_printf = True
        args = list(inv.arguments or [])
        if inv.member == 'printf':
            if args and isinstance(args[0],jt.Literal) and args[0].value.startswith('"'):
                fmt = args[0].value[1:-1].replace('%n','\\n')
                rest = [self._expr(a) for a in args[1:]]
                return c_ast.FuncCall(_id('printf'),
                    c_ast.ExprList([_const('string',f'"{fmt}"')]+rest))
            return c_ast.FuncCall(_id('printf'), c_ast.ExprList([self._expr(a) for a in args]) if args else None)
        if not args:
            return c_ast.FuncCall(_id('printf'), c_ast.ExprList([_const('string','"\\n"')]))
        a = args[0]
        if isinstance(a,jt.BinaryOperation) and a.operator=='+':
            fmt_, ca = self._flatten_concat(a)
            return c_ast.FuncCall(_id('printf'), c_ast.ExprList([_const('string',f'"{fmt_}\\n"')]+ca))
        if isinstance(a,jt.Literal):
            v = a.value
            if v.startswith('"'):
                raw = v[1:-1].replace('%n','\\n')
                return c_ast.FuncCall(_id('printf'), c_ast.ExprList([_const('string',f'"{raw}\\n"')]))
            if v.startswith("'"):
                return c_ast.FuncCall(_id('printf'), c_ast.ExprList([_const('string','"%c\\n"'),self._expr(a)]))
            if '.' in v or v[-1] in ('f','F'):
                return c_ast.FuncCall(_id('printf'), c_ast.ExprList([_const('string','"%f\\n"'),self._expr(a)]))
        return c_ast.FuncCall(_id('printf'), c_ast.ExprList([_const('string','"%d\\n"'),self._expr(a)]))

    def _flatten_concat(self, node):
        if isinstance(node,jt.BinaryOperation) and node.operator=='+':
            lf,la = self._flatten_concat(node.operandl)
            rf,ra = self._flatten_concat(node.operandr)
            return lf+rf, la+ra
        if isinstance(node,jt.Literal) and node.value.startswith('"'):
            return node.value[1:-1].replace('%n','\\n'), []
        return '%d', [self._expr(node)]

    # ── HashMap boilerplate ───────────────────────────────────────────────────
    def _hashmap_code(self) -> str:
        return """\
/* -- HashMap simulation -- */
#define HASHMAP_SIZE 100
typedef struct { int keys[HASHMAP_SIZE]; int vals[HASHMAP_SIZE]; int count; } HashMap;
HashMap hashmap_create() { HashMap m; m.count=0; return m; }
void hashmap_put(HashMap *m,int k,int v){int i;for(i=0;i<m->count;i++)if(m->keys[i]==k){m->vals[i]=v;return;}m->keys[m->count]=k;m->vals[m->count]=v;m->count++;}
int hashmap_get(HashMap *m,int k){int i;for(i=0;i<m->count;i++)if(m->keys[i]==k)return m->vals[i];return -1;}
int hashmap_contains(HashMap *m,int k){int i;for(i=0;i<m->count;i++)if(m->keys[i]==k)return 1;return 0;}
/* -------------------------*/
"""


# ---------------------------------------------------------------------------
#  Public API
# ---------------------------------------------------------------------------
def translate_string(java_source: str) -> str:
    import javalang
    try:
        tree = javalang.parse.parse(java_source)
    except javalang.parser.JavaSyntaxError as e:
        raise ValueError(f'Java parse error: {e}') from e
    v = JavaToCVisitor()
    return v.translate(tree)


def translate_file(java_path: str) -> str:
    with open(java_path, encoding='utf-8') as f:
        return translate_string(f.read())
