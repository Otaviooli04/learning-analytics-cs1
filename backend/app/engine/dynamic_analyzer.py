import subprocess
import tempfile
import os


def _normalize_ws(text: str) -> str:
    """Normaliza espaços para a comparação de saída, tolerando alinhamento.

    Colapsa espaços internos de cada linha (ex.: `%4d` imprime "   1    2",
    enquanto a saída esperada extraída do PDF junta tokens com 1 espaço) e
    descarta linhas em branco nas bordas. Preserva as quebras de linha, pois a
    estrutura de linhas é significativa (matrizes, listas). Afrouxa apenas o
    formato horizontal — ordem e número de linhas continuam exigidos.
    """
    lines = [" ".join(line.split()) for line in text.splitlines()]
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines)


# Backup do subprocess.run; o guarda real do laço infinito é o "timeout 5" DENTRO
# do container. Folga generosa para o startup do container sob carga (no lote, vários
# `docker run` em sequência deixam o daemon lento e geram TIMEOUT espúrio).
_RUN_BACKUP_TIMEOUT_S = 15


def _run_once(run_cmd: list[str], stdin: str):
    """Roda o binário no container uma vez.

    Retorna ("ok", saida), ("timeout", None) quando o PRÓPRIO programa estourou os
    5s (returncode 124 do `timeout` do container = provável laço infinito do aluno),
    ou ("hiccup", None) quando o backup do subprocess estourou — sinal de Docker
    lento/sob carga, não do código do aluno (vale uma nova tentativa)."""
    try:
        r = subprocess.run(run_cmd, input=stdin, capture_output=True,
                           text=True, timeout=_RUN_BACKUP_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        return "hiccup", None
    if r.returncode == 124:
        return "timeout", None
    return "ok", r.stdout.strip()


def compile_and_run(source_code: str, test_cases: list[dict]) -> dict:
    with tempfile.TemporaryDirectory() as temp_dir:
        source_path = os.path.join(temp_dir, "student_code.c")
        with open(source_path, "w", encoding="utf-8") as f:
            f.write(source_code)

        compile_cmd = [
            "docker", "run", "--rm", "--network", "none",
            "-v", f"{temp_dir}:/src", "-w", "/src",
            "gcc:latest",
            # -lm: linka a libm. Problemas de CS1 usam sqrt/pow/fabs (math.h);
            # sem isso o gcc dá "undefined reference" e o sistema reprova código
            # correto que o CodeRunner aceita (ele linka math por padrão).
            # -ftrivial-auto-var-init=zero: zera variáveis locais não inicializadas,
            # alinhando o comportamento ao do CodeRunner (que zera por acaso). Sem
            # isso, código com UB produz lixo dependente do ambiente e reprova
            # submissões que o avaliador de referência aceitou.
            "gcc", "-Wall", "-ftrivial-auto-var-init=zero",
            "student_code.c", "-o", "exe.out", "-lm",
        ]
        # Compilar código de CS1 leva <1s; um timeout aqui é quase sempre um
        # engasgo do Docker (container frio / daemon sob carga durante o lote),
        # não o compilador travando. Uma nova tentativa resolve sem perder a
        # submissão; se persistir, devolvemos um veredito limpo em vez de deixar
        # o TimeoutExpired derrubar a avaliação como "erro interno".
        try:
            compile_result = subprocess.run(
                compile_cmd, capture_output=True, text=True, timeout=30)
        except subprocess.TimeoutExpired:
            try:
                compile_result = subprocess.run(
                    compile_cmd, capture_output=True, text=True, timeout=60)
            except subprocess.TimeoutExpired:
                return {
                    "success": False,
                    "compile_error": "A compilação não terminou no tempo limite "
                                     "(Docker indisponível no momento). Reavalie a submissão.",
                    "warnings": "",
                    "test_results": [],
                    "all_tests_passed": None,
                }

        if compile_result.returncode != 0:
            return {
                "success": False,
                "compile_error": compile_result.stderr or compile_result.stdout,
                "warnings": "",
                "test_results": [],
                "all_tests_passed": None,
            }

        warnings = compile_result.stderr.strip()

        if not test_cases:
            return {
                "success": True,
                "compile_error": "",
                "warnings": warnings,
                "test_results": [],
                "all_tests_passed": None,
            }

        # "timeout 5" DENTRO do container mata o laço infinito do aluno e o --rm
        # encerra o container. _run_once distingue isso (returncode 124) de uma
        # lentidão do Docker, que merece uma nova tentativa.
        run_cmd = [
            "docker", "run", "--rm", "--network", "none", "-i",
            "-v", f"{temp_dir}:/src", "-w", "/src",
            "gcc:latest", "timeout", "5", "./exe.out",
        ]
        test_results = []
        for tc in test_cases:
            status, out = _run_once(run_cmd, tc["input"])
            if status == "hiccup":
                # Docker travou (não é o código do aluno): 1 nova tentativa antes de
                # cravar TIMEOUT, para um engasgo do daemon durante o lote não
                # reprovar código correto.
                status, out = _run_once(run_cmd, tc["input"])
            actual = out if status == "ok" else "TIMEOUT"
            expected = tc["expected_output"].strip()
            test_results.append({
                "input": tc["input"],
                "expected_output": expected,
                "actual_output": actual,
                "passed": _normalize_ws(actual) == _normalize_ws(expected),
            })

        return {
            "success": True,
            "compile_error": "",
            "warnings": warnings,
            "test_results": test_results,
            "all_tests_passed": all(r["passed"] for r in test_results),
        }
