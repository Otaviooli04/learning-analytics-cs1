from pycparser import c_parser, c_ast
import re


class ControlFlowVisitor(c_ast.NodeVisitor):
    def __init__(self):
        self.structures = []

    def visit_If(self, node):
        self.structures.append("If")
        self.generic_visit(node)

    def visit_For(self, node):
        self.structures.append("For")
        self.generic_visit(node)

    def visit_While(self, node):
        self.structures.append("While")
        self.generic_visit(node)

    def visit_DoWhile(self, node):
        self.structures.append("DoWhile")
        self.generic_visit(node)

    def visit_Switch(self, node):
        self.structures.append("Switch")
        self.generic_visit(node)


def _type_name(node) -> str:
    if isinstance(node, c_ast.TypeDecl):
        return _type_name(node.type)
    if isinstance(node, c_ast.IdentifierType):
        return " ".join(node.names)
    if isinstance(node, c_ast.PtrDecl):
        return f"{_type_name(node.type)} *"
    if isinstance(node, c_ast.ArrayDecl):
        return f"{_type_name(node.type)} []"
    return "unknown"


def _extract_params(args) -> list:
    if args is None:
        return []
    params = []
    for p in args.params:
        if isinstance(p, c_ast.EllipsisParam):
            params.append({"name": "...", "type": "...", "is_pointer": False})
            continue
        ptype = _type_name(p.type)
        # `void` sem nome (ex: int main(void)) não conta como parâmetro real
        if ptype == "void" and p.name is None:
            continue
        params.append({
            "name": p.name,
            "type": ptype,
            "is_pointer": isinstance(p.type, (c_ast.PtrDecl, c_ast.ArrayDecl)),
        })
    return params


class _BodyVisitor(c_ast.NodeVisitor):
    """Coleta chamadas e returns dentro do corpo de uma função."""

    def __init__(self, func_name: str):
        self.func_name = func_name
        self.is_recursive = False
        self.returns_value = False

    def visit_FuncCall(self, node):
        if isinstance(node.name, c_ast.ID) and node.name.name == self.func_name:
            self.is_recursive = True
        self.generic_visit(node)

    def visit_Return(self, node):
        if node.expr is not None:
            self.returns_value = True
        self.generic_visit(node)


class FunctionVisitor(c_ast.NodeVisitor):
    def __init__(self):
        self.functions = []

    def visit_FuncDef(self, node):
        name = node.decl.name
        func_decl = node.decl.type  # FuncDecl
        params = _extract_params(func_decl.args)

        body = _BodyVisitor(name)
        body.visit(node.body)

        self.functions.append({
            "name": name,
            "return_type": _type_name(func_decl.type),
            "params": params,
            "param_count": len(params),
            "is_recursive": body.is_recursive,
            "has_pointer_param": any(p["is_pointer"] for p in params),
            "returns_value": body.returns_value,
        })
        # C não permite funções aninhadas — não precisa descer mais


def extract_control_flow(source_code: str) -> dict:
    clean_code = re.sub(r'#include\s*<.*?>', '', source_code)
    clean_code = re.sub(r'#include\s*".*?"', '', clean_code)

    parser = c_parser.CParser()
    try:
        ast = parser.parse(clean_code)

        cf_visitor = ControlFlowVisitor()
        cf_visitor.visit(ast)

        fn_visitor = FunctionVisitor()
        fn_visitor.visit(ast)

        return {
            "success": True,
            "structures": cf_visitor.structures,
            "functions": fn_visitor.functions,
        }
    except Exception as e:
        return {"success": False, "error": f"Erro de parsing na AST: {str(e)}"}
