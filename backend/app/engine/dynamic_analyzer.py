import subprocess
import tempfile
import os


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
            try:
                run_result = subprocess.run(
                    [
                        "docker", "run", "--rm", "--network", "none", "-i",
                        "-v", f"{temp_dir}:/src", "-w", "/src",
                        "gcc:latest", "./exe.out",
                    ],
                    input=tc["input"],
                    capture_output=True, text=True, timeout=5,
                )
                actual = run_result.stdout.strip()
                expected = tc["expected_output"].strip()
                test_results.append({
                    "input": tc["input"],
                    "expected_output": expected,
                    "actual_output": actual,
                    "passed": actual == expected,
                })
            except subprocess.TimeoutExpired:
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
