import subprocess
import tempfile
import os


def compile_c_code(source_code: str) -> dict:
    with tempfile.TemporaryDirectory() as temp_dir:
        source_path = os.path.join(temp_dir, "student_code.c")

        with open(source_path, "w", encoding="utf-8") as f:
            f.write(source_code)

        docker_command = [
            "docker", "run", "--rm",
            "--network", "none",
            "-v", f"{temp_dir}:/src",
            "-w", "/src",
            "gcc:latest",
            "sh", "-c", "gcc -Wall student_code.c -o exe.out && ./exe.out",
        ]

        try:
            result = subprocess.run(
                docker_command,
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                return {
                    "success": True,
                    "message": f"Sucesso. Saída:\n{result.stdout}",
                    "warnings": result.stderr,
                }

            erro = result.stderr if result.stderr else result.stdout
            return {"success": False, "message": erro, "warnings": ""}

        except subprocess.TimeoutExpired:
            return {"success": False, "message": "Erro: Tempo limite excedido.", "warnings": ""}
        except Exception as e:
            return {"success": False, "message": f"Erro interno: {str(e)}", "warnings": ""}
