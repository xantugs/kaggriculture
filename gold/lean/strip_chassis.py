"""Chassis: comments and docstrings out, the Apache notice kept once at the top. Semantics untouched (ast.unparse).
usage: strip_chassis.py base.py out.py"""
import ast, sys
src = open(sys.argv[1], encoding='utf-8').read()
lines = src.split('\n')
# the notice: the leading comment block up to the first non-comment line
hdr = []
for l in lines:
    if l.startswith('#') or not l.strip(): hdr.append(l)
    else: break
notice = [l for l in hdr if l.strip()]
tree = ast.parse(src)
class Doc(ast.NodeTransformer):
    def visit_Expr(self, node):
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            return None
        return node
    def visit_FunctionDef(self, node):
        self.generic_visit(node); node.body = node.body or [ast.Pass()]; return node
    def visit_ClassDef(self, node):
        self.generic_visit(node); node.body = node.body or [ast.Pass()]; return node
    def visit_If(self, node):
        self.generic_visit(node); node.body = node.body or [ast.Pass()]; return node
    def visit_For(self, node):
        self.generic_visit(node); node.body = node.body or [ast.Pass()]; return node
    def visit_While(self, node):
        self.generic_visit(node); node.body = node.body or [ast.Pass()]; return node
    def visit_With(self, node):
        self.generic_visit(node); node.body = node.body or [ast.Pass()]; return node
    def visit_Try(self, node):
        self.generic_visit(node); node.body = node.body or [ast.Pass()]
        for h in node.handlers: h.body = h.body or [ast.Pass()]
        return node
tree = Doc().visit(tree); ast.fix_missing_locations(tree)
code = ast.unparse(tree)
open(sys.argv[2], 'w', encoding='utf-8').write('\n'.join(notice) + '\n\n' + code + '\n')
print('%s: %d -> %d lines (notice %d lines kept)' % (sys.argv[1], src.count('\n'), code.count('\n') + len(notice) + 2, len(notice)))
