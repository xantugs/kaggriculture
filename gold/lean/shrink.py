"""Shrink the controller: fold GC_P switches m5 never sets (constant False/None/0), drop the dead branches and the
functions nothing references, bake the configuration into GC_P, strip telemetry, comments and docstrings.
usage: shrink.py ctl.py cfg.json out.py"""
import ast, json, re, sys

FALSY = {'False', 'None', '0', '0.0', '()', '{}', '""', "''"}

def load_defaults(src):
    m = re.search(r'^GC_P = dict\((.*?)^\)', src, flags=re.S | re.M)
    d = {}
    for line in m.group(1).split('\n'):
        mm = re.match(r'\s*([a-z0-9_]+)=(.*?)(,\s*(#.*)?)?$', line)
        if mm: d[mm.group(1)] = mm.group(2).strip().rstrip(',')
    return d

def cfg_keys(cfg):
    keys = set(cfg)
    for k, v in cfg.items():
        if isinstance(v, dict): keys |= set(v)
    return keys

class Fold(ast.NodeTransformer):
    """GC_P["k"] with k constant -> the constant; with GC_P["open"] None the opening machinery folds too."""
    def __init__(self, const):
        self.const = const
    def visit_Attribute(self, node):
        self.generic_visit(node)
        if ('open' in self.const and self.const['open'] is None and node.attr == 'open'
                and isinstance(node.value, ast.Name) and node.value.id == 'self' and isinstance(node.ctx, ast.Load)):
            return ast.copy_location(ast.Constant(None), node)
        return node
    def visit_Subscript(self, node):
        self.generic_visit(node)
        if (isinstance(node.value, ast.Name) and node.value.id == 'GC_P' and isinstance(node.slice, ast.Constant)
                and node.slice.value in self.const):
            return ast.copy_location(ast.Constant(self.const[node.slice.value]), node)
        return node
    def visit_Call(self, node):
        self.generic_visit(node)
        f = node.func
        if ('open' in self.const and self.const['open'] is None and isinstance(f, ast.Attribute) and f.attr == '_open_on'
                and isinstance(f.value, ast.Name) and f.value.id == 'self'):
            return ast.copy_location(ast.Constant(False), node)
        if (isinstance(f, ast.Attribute) and f.attr == 'get' and isinstance(f.value, ast.Name) and f.value.id == 'GC_P'
                and node.args and isinstance(node.args[0], ast.Constant) and node.args[0].value in self.const):
            return ast.copy_location(ast.Constant(self.const[node.args[0].value]), node)
        return node

def const_value(test):
    """Constant truth of a test expression, or None."""
    try:
        code = compile(ast.Expression(test), '<t>', 'eval')
        return bool(eval(code, {'__builtins__': {}}, {}))
    except Exception:
        return None

class Prune(ast.NodeTransformer):
    def _body(self, stmts):
        out = []
        for s in stmts:
            r = self.visit(s)
            if r is None: continue
            if isinstance(r, list): out.extend(r)
            else: out.append(r)
        return out or [ast.Pass()]
    def visit_If(self, node):
        node.test = self.visit(node.test)
        cv = const_value(node.test)
        if cv is True:
            return self._body(node.body)
        if cv is False:
            return self._body(node.orelse) if node.orelse else None
        node.body = self._body(node.body); node.orelse = self._body(node.orelse) if node.orelse else []
        return node
    def visit_IfExp(self, node):
        self.generic_visit(node)
        cv = const_value(node.test)
        if cv is True: return node.body
        if cv is False: return node.orelse
        return node
    def visit_BoolOp(self, node):
        # exact semantics: `or` returns the first truthy operand, `and` the first falsy one; the last operand is
        # returned as it is, so it is never dropped
        self.generic_visit(node)
        vals = []; n = len(node.values)
        for i, v in enumerate(node.values):
            cv = const_value(v); last = i == n - 1
            if isinstance(node.op, ast.And):
                if cv is True and not last: continue     # True and b -> b
                vals.append(v)
                if cv is False: break                    # a and False -> the value is this operand
            else:
                if cv is False and not last: continue    # False or b -> b
                vals.append(v)
                if cv is True: break                     # a or True_const -> the value is this operand
        if len(vals) == 1: return vals[0]
        node.values = vals; return node
    def visit_FunctionDef(self, node):
        node.body = self._body(node.body); return node
    def visit_ClassDef(self, node):
        node.body = self._body(node.body); return node
    def visit_For(self, node):
        node.body = self._body(node.body); node.orelse = self._body(node.orelse) if node.orelse else []; return node
    def visit_While(self, node):
        node.body = self._body(node.body); node.orelse = self._body(node.orelse) if node.orelse else []; return node
    def visit_With(self, node):
        node.body = self._body(node.body); return node
    def visit_Try(self, node):
        node.body = self._body(node.body)
        for h in node.handlers: h.body = self._body(h.body)
        node.orelse = self._body(node.orelse) if node.orelse else []; node.finalbody = self._body(node.finalbody) if node.finalbody else []
        return node

class StripTel(ast.NodeTransformer):
    """Statements that only write _GC_REPORT[...] go; the dict itself stays (harness telemetry)."""
    def visit_Assign(self, node):
        if all(isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name) and t.value.id == '_GC_REPORT' for t in node.targets):
            return None
        return node
    def visit_AugAssign(self, node):
        if isinstance(node.target, ast.Subscript) and isinstance(node.target.value, ast.Name) and node.target.value.id == '_GC_REPORT':
            return None
        return node
    def visit_Expr(self, node):
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            return None   # docstring
        return node

def names_used(tree):
    used = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Name): used.add(n.id)
        elif isinstance(n, ast.Attribute): used.add(n.attr)
        elif isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value.isidentifier(): used.add(n.value)  # globals().get("x")
    return used

def drop_dead(tree, keep):
    """Remove top-level functions/classes and class methods that nothing references (iterate to a fixed point)."""
    while True:
        used = names_used(tree)
        removed = 0
        body = []
        for s in tree.body:
            if isinstance(s, (ast.FunctionDef, ast.ClassDef)) and s.name not in keep and s.name not in used:
                removed += 1; continue
            body.append(s)
        tree.body = body
        for s in tree.body:
            if isinstance(s, ast.ClassDef):
                nb = []
                for m in s.body:
                    if isinstance(m, ast.FunctionDef) and m.name not in keep and m.name not in used and not m.name.startswith('__'):
                        removed += 1; continue
                    nb.append(m)
                s.body = nb or [ast.Pass()]
        if not removed:
            return tree

def main():
    src_path, cfg_path, out = sys.argv[1:4]
    src = open(src_path, encoding='utf-8').read()
    cfg = json.load(open(cfg_path))
    defaults = load_defaults(src)
    setk = cfg_keys(cfg)
    const = {k: eval(v) for k, v in defaults.items() if v in FALSY and k not in setk}
    over_keys = set()
    for k, v in cfg.items():
        if isinstance(v, dict): over_keys |= set(v)
    for k, v in cfg.items():
        if not isinstance(v, (dict, list)) and k not in over_keys and k in defaults:
            const[k] = v          # set once by the configuration, never overridden at runtime
    # an override that never changes the value (every override dict and the base agree) is a constant too
    for k in over_keys:
        vals = [d[k] for d in cfg.values() if isinstance(d, dict) and k in d]
        base = cfg[k] if k in cfg and not isinstance(cfg[k], (dict, list)) else (eval(defaults[k]) if k in defaults and defaults[k] in FALSY | {'True'} else ('__skip__',))
        if base != ('__skip__',) and all(v == base for v in vals) and not isinstance(base, (dict, list)):
            const[k] = base
    # keys that code assigns into GC_P by name are not constants
    for m in re.finditer(r'GC_P\["([a-z0-9_]+)"\]\s*=', src):
        const.pop(m.group(1), None)
    tree = ast.parse(src)
    tree = Fold(const).visit(tree)
    tree = StripTel().visit(tree)
    tree = Prune().visit(tree)     # last: it re-bodies every block a removal emptied
    ast.fix_missing_locations(tree)
    # bake the configuration: GC_P = dict(...) then GC_P.update(cfg) as a literal
    for i, s in enumerate(tree.body):
        if isinstance(s, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'GC_P' for t in s.targets):
            upd = ast.parse('GC_P.update(%r)' % (cfg,)).body[0]
            tree.body.insert(i + 1, upd); break
    keep = {'agent', 'GoldCtl', 'act', 'plan_day', 'kaggle_submission_agent'}
    tree = drop_dead(tree, keep)
    # GC_P entries nothing reads any more (folded or never used) leave the dict literal and the baked update
    referenced = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Subscript) and isinstance(n.value, ast.Name) and n.value.id == 'GC_P' and isinstance(n.slice, ast.Constant):
            referenced.add(n.slice.value)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == 'get' and isinstance(n.func.value, ast.Name) and n.func.value.id == 'GC_P' and n.args and isinstance(n.args[0], ast.Constant):
            referenced.add(n.args[0].value)
    referenced |= over_keys | {'div_over', 'rich_over', 'herd_rich_over', 'rich_tom_over', 'rich_car_over', 'rich_tom_dem_over'}
    for s in tree.body:
        if isinstance(s, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'GC_P' for t in s.targets) and isinstance(s.value, ast.Call):
            s.value.keywords = [kw for kw in s.value.keywords if kw.arg in referenced]
        if (isinstance(s, ast.Expr) and isinstance(s.value, ast.Call) and isinstance(s.value.func, ast.Attribute) and s.value.func.attr == 'update'
                and isinstance(s.value.func.value, ast.Name) and s.value.func.value.id == 'GC_P' and s.value.args and isinstance(s.value.args[0], ast.Dict)):
            d = s.value.args[0]
            pairs = [(k, v) for k, v in zip(d.keys, d.values) if isinstance(k, ast.Constant) and k.value in referenced]
            d.keys = [k for k, v in pairs]; d.values = [v for k, v in pairs]
    code = ast.unparse(tree)
    open(out, 'w', encoding='utf-8').write(code + '\n')
    print('folded %d switches; %s -> %s: %d -> %d lines' % (len(const), src_path, out, src.count('\n'), code.count('\n')))

if __name__ == '__main__':
    main()
