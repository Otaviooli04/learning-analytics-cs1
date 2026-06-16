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


def compile_and_run(source_code: str, test_cases: list[dict]) -> dict:
    with tempfile.TemporaryDirectory() as temp_dir:
        source_path = os.path.join(temp_dir, "student_code.c")
        with open(source_path, "w", encoding="utf-8") as f:
            f.write(source_code)

        compile_result = subprocess.run(
            [
                "docker", "run", "--rm", "--network", "none",
                "-v", f"{temp_dir}:/src", "-w", "/src",
                "gcc:latest",
                "gcc", "-Wall", "student_code.c", "-o", "exe.out",
            ],
            capture_output=True, text=True, timeout=30,
        )

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

        test_results = []
        for tc in test_cases:
            # "timeout 5" dentro do container garante que o processo filho
            # é morto pelo kernel do container e o container encerra com --rm.
            # subprocess.run(timeout=7) é apenas backup caso o Docker daemon trave.
            try:
                run_result = subprocess.run(
                    [
                        "docker", "run", "--rm", "--network", "none", "-i",
                        "-v", f"{temp_dir}:/src", "-w", "/src",
                        "gcc:latest", "timeout", "5", "./exe.out",
                    ],
                    input=tc["input"],
                    capture_output=True, text=True, timeout=7,
                )
                if run_result.returncode == 124:
                    actual = "TIMEOUT"
                else:
                    actual = run_result.stdout.strip()
                expected = tc["expected_output"].strip()
                test_results.append({
                    "input": tc["input"],
                    "expected_output": expected,
                    "actual_output": actual,
                    "passed": _normalize_ws(actual) == _normalize_ws(expected),
                })
            except subprocess.TimeoutExpired:
                # subprocess.run já mata e aguarda o filho antes de relançar; só
                # registramos o veredito de TIMEOUT. (TimeoutExpired não expõe
                # .process — o acesso anterior derrubava a avaliação inteira quando
                # uma submissão travava além dos 7s de backup.)
                test_results.append({
                    "input": tc["input"],
                    "expected_output": tc["expected_output"],
                    "actual_output": "TIMEOUT",
                    "passed": False,
                })

        return {
            "success": True,
            "compile_error": "",
            "warnings": warnings,
            "test_results": test_results,
            "all_tests_passed": all(r["passed"] for r in test_results),
        }
