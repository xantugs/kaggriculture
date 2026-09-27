"""Chassis: module-level names assigned once to a bool/None/int constant and never reassigned fold to that constant
(dead branches go); top-level functions and classes nothing references (names in code or in any string) go.
usage: fold_chassis.py base.py out.py"""
import ast, re, sys
sys.path.insert(0, '/home/user/kaggriculture/gold/lean')
from shrink import Prune, const_value
src = open(sys.argv[1], encoding='utf-8').read()
notice = src.split('\n\n')[0]
tree = ast.parse(src)
stores = {}
for n in ast.walk(tree):
    if isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)): stores[n.id] = stores.get(n.id, 0) + 1
    if isinstance(n, ast.Global) or isinstance(n, ast.Nonlocal):
        for nm in n.names: stores[nm] = stores.get(nm, 0) + 99
    if isinstance(n, (ast.FunctionDef, ast.ClassDef)): stores[n.name] = stores.get(n.name, 0) + 1
    if isinstance(n, ast.arg): stores[n.arg] = stores.get(n.arg, 0) + 99
    if isinstance(n, ast.Import) or isinstance(n, ast.ImportFrom):
        for a in n.names: stores[(a.asname or a.name).split('.')[0]] = stores.get((a.asname or a.name).split('.')[0], 0) + 99
const = {}
for s in tree.body:
    if isinstance(s, ast.Assign) and len(s.targets) == 1 and isinstance(s.targets[0], ast.Name) and isinstance(s.value, ast.Constant):
        nm = s.targets[0].id
        if stores.get(nm, 0) == 1 and (s.value.value is None or isinstance(s.value.value, (bool, int)) and not isinstance(s.value.value, float)):
            const[nm] = s.value.value
# a string anywhere that mentions the name keeps it a variable (exec'd code, globals().get("x"))
strings = ' '.join(n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str))
tokens = set(re.findall(r'[A-Za-z_][A-Za-z0-9_]*', strings))
const = {k: v for k, v in const.items() if k not in tokens}
import os
if os.environ.get('FOLD_ONLY') is not None:
    only = set(x for x in os.environ['FOLD_ONLY'].split(',') if x)
    const = {k: v for k, v in const.items() if k in only}
class FoldNames(ast.NodeTransformer):
    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load) and node.id in const:
            return ast.copy_location(ast.Constant(const[node.id]), node)
        return node
tree = FoldNames().visit(tree)
tree = Prune().visit(tree)
# no definition is removed: the chassis picks its entry point positionally (`[v for v in globals().values() if callable(v)][-1]`)
removed = 0
def used_names(t):
    u = set(tokens)
    for n in ast.walk(t):
        if isinstance(n, ast.Name): u.add(n.id)
        elif isinstance(n, ast.Attribute): u.add(n.attr)
    return u
# the folded constants' own assignments go when nothing else reads them
u = used_names(tree)
tree.body = [s for s in tree.body if not (isinstance(s, ast.Assign) and len(s.targets) == 1 and isinstance(s.targets[0], ast.Name) and s.targets[0].id in const and s.targets[0].id not in u)]
ast.fix_missing_locations(tree)
code = ast.unparse(tree)
open(sys.argv[2], 'w', encoding='utf-8').write(notice + '\n\n' + code + '\n')
print('folded %d module constants, removed %d unreferenced defs: %d -> %d lines' % (len(const), removed, src.count('\n'), code.count('\n') + notice.count('\n') + 3))
