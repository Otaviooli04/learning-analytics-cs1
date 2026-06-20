"""Localiza as linhas problemáticas do código a partir da saída do compilador.

O `dynamic_analyzer` grava o código do aluno verbatim como `student_code.c`, então
os números de linha que o gcc reporta (`student_code.c:LINHA:COL: error: ...`) batem
1:1 com o `code` da submissão. Extraímos essas linhas para o professor destacar
exatamente onde está o erro de compilação no código representativo do grupo.
"""
import re

# Captura "qualquer.c:LINHA[:COL]: error|warning|note: ...". Só consideramos as
# de 'error' (o que de fato impede a compilação); avisos e notas não marcam a
# parte culpada.
_GCC_LINE = re.compile(
    r"^[^\s:]+:(\d+):(?:\d+:)?\s*(error|warning|note)\b", re.MULTILINE
)


def parse_compile_error_lines(compile_error: str, max_line: int | None = None) -> list[int]:
    """Linhas (1-based, ordenadas e sem repetição) sinalizadas pelo gcc como erro.

    `max_line` (nº de linhas do código) descarta números fora do intervalo — guarda
    contra mensagens internas do toolchain que não apontam para o código do aluno.
    """
    if not compile_error:
        return []
    lines: set[int] = set()
    for m in _GCC_LINE.finditer(compile_error):
        if m.group(2) != "error":
            continue
        n = int(m.group(1))
        if n < 1 or (max_line is not None and n > max_line):
            continue
        lines.add(n)
    return sorted(lines)
