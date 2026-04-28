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

def extract_control_flow(source_code: str) -> dict:
    clean_code = re.sub(r'#include\s*<.*?>', '', source_code)
    clean_code = re.sub(r'#include\s*".*?"', '', clean_code)

    parser = c_parser.CParser()
    try:
        ast = parser.parse(clean_code)
        visitor = ControlFlowVisitor()
        visitor.visit(ast)
        
        return {"success": True, "structures": visitor.structures}
    except Exception as e:
        return {"success": False, "error": f"Erro de parsing na AST: {str(e)}"}