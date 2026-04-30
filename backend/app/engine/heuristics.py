def check_structures(found: list, required: list, forbidden: list) -> dict:
    missing = [s for s in required if s not in found]
    prohibited = [s for s in forbidden if s in found]
    return {
        "compliant": len(missing) == 0 and len(prohibited) == 0,
        "missing_required": missing,
        "found_forbidden": prohibited,
    }


def classify_error(
    dynamic_result: dict,
    static_result: dict,
    required_structures: list = None,
    forbidden_structures: list = None,
) -> dict:
    dyn_success = dynamic_result.get("success", False)
    compile_error = dynamic_result.get("compile_error", "").lower()
    warnings = dynamic_result.get("warnings", "").lower()
    structures = static_result.get("structures", [])
    test_results = dynamic_result.get("test_results", [])
    all_passed = dynamic_result.get("all_tests_passed")

    if not dyn_success:
        if "error:" in compile_error:
            return _classify_compilation_error(compile_error)

        if "timeout" in compile_error:
            return _classify_timeout(structures)

        if "segmentation fault" in compile_error or "core dumped" in compile_error:
            return {
                "error_category": "Acesso Indevido à Memória",
                "pedagogical_diagnosis": "O programa tentou acessar uma área de memória restrita (Segmentation Fault).",
                "actionable_feedback": "Verifique se os índices de vetores ultrapassam o limite declarado ou se há ponteiros não inicializados.",
            }

        if "floating point exception" in compile_error:
            return {
                "error_category": "Erro Aritmético — Divisão por Zero",
                "pedagogical_diagnosis": "O programa executou uma divisão por zero em tempo de execução.",
                "actionable_feedback": "Adicione uma verificação para garantir que o divisor seja diferente de zero antes da operação.",
            }

    if dyn_success:
        warning_diagnosis = _classify_warnings(warnings)
        if warning_diagnosis:
            return warning_diagnosis

        req = required_structures or []
        forb = forbidden_structures or []
        struct_check = check_structures(structures, req, forb)

        if not struct_check["compliant"]:
            return _classify_structure_violation(struct_check)

        if test_results:
            failed = [r for r in test_results if not r["passed"]]
            if any(r["actual_output"] == "TIMEOUT" for r in failed):
                return _classify_timeout(structures)
            if failed:
                return _classify_wrong_output(failed, len(test_results))
            return {
                "error_category": "Correto",
                "pedagogical_diagnosis": f"Todos os {len(test_results)} testes passaram e as estruturas estão corretas.",
                "actionable_feedback": "Solução correta.",
            }

        return _classify_success(structures)

    return {
        "error_category": "Erro Desconhecido",
        "pedagogical_diagnosis": "Ocorreu uma falha técnica não classificada pelas regras atuais.",
        "actionable_feedback": "Consulte os logs técnicos de execução.",
    }


def _classify_structure_violation(struct_check: dict) -> dict:
    parts = []
    if struct_check["missing_required"]:
        parts.append(f"estruturas obrigatórias não usadas: {struct_check['missing_required']}")
    if struct_check["found_forbidden"]:
        parts.append(f"estruturas proibidas encontradas: {struct_check['found_forbidden']}")
    return {
        "error_category": "Violação de Estrutura",
        "pedagogical_diagnosis": f"O código compilou, mas não respeita as restrições da questão — {'; '.join(parts)}.",
        "actionable_feedback": "Revise o enunciado: verifique quais estruturas de controle são exigidas ou proibidas.",
    }


def _classify_wrong_output(failed: list, total: int) -> dict:
    exemplo = failed[0]
    return {
        "error_category": "Saída Incorreta",
        "pedagogical_diagnosis": (
            f"{len(failed)}/{total} testes falharam. "
            f"Exemplo: entrada '{exemplo['input']}' → esperado '{exemplo['expected_output']}', "
            f"obtido '{exemplo['actual_output']}'."
        ),
        "actionable_feedback": "Revise a lógica do programa. Teste manualmente com as entradas indicadas e compare a saída esperada.",
    }


def _classify_compilation_error(message: str) -> dict:
    if "expected ';'" in message or 'expected ";"' in message:
        return {
            "error_category": "Sintaxe — Ponto e Vírgula Ausente",
            "pedagogical_diagnosis": "Uma ou mais instruções não foram terminadas com ';'.",
            "actionable_feedback": "Localize a linha indicada pelo compilador e adicione o ponto e vírgula ao final da instrução.",
        }

    if "undeclared" in message or "was not declared" in message:
        return {
            "error_category": "Sintaxe — Variável ou Função Não Declarada",
            "pedagogical_diagnosis": "O programa utiliza um identificador (variável ou função) que não foi declarado antes do uso.",
            "actionable_feedback": "Declare a variável antes de usá-la ou verifique se o nome está escrito corretamente.",
        }

    if "implicit declaration of function" in message:
        return {
            "error_category": "Sintaxe — Cabeçalho Faltando",
            "pedagogical_diagnosis": "Uma função da biblioteca padrão foi usada sem o #include correspondente (ex: printf sem #include <stdio.h>).",
            "actionable_feedback": "Adicione o #include adequado ao início do arquivo.",
        }

    if "undefined reference" in message:
        return {
            "error_category": "Linker — Função Indefinida",
            "pedagogical_diagnosis": "O compilador encontrou uma chamada de função que não tem implementação vinculada.",
            "actionable_feedback": "Verifique se a função foi implementada ou se falta algum #include de biblioteca.",
        }

    if "incompatible type" in message or "invalid conversion" in message:
        return {
            "error_category": "Semântica — Tipo Incompatível",
            "pedagogical_diagnosis": "Uma atribuição ou operação foi feita entre tipos de dados incompatíveis.",
            "actionable_feedback": "Verifique os tipos das variáveis envolvidas e aplique conversão explícita (cast) se necessário.",
        }

    if "control reaches end of non-void function" in message or "no return" in message:
        return {
            "error_category": "Semântica — Retorno Ausente",
            "pedagogical_diagnosis": "Uma função declarada com tipo de retorno não garante retornar um valor em todos os caminhos de execução.",
            "actionable_feedback": "Certifique-se de que a função possui um 'return' em todos os fluxos possíveis.",
        }

    return {
        "error_category": "Erro de Compilação",
        "pedagogical_diagnosis": "O código não compilou devido a um erro não classificado pelas regras atuais.",
        "actionable_feedback": "Leia a mensagem de erro do compilador com atenção para identificar a linha e o tipo do problema.",
    }


def _classify_timeout(structures: list) -> dict:
    loop_structures = {"While", "For", "DoWhile"}

    if any(s in structures for s in loop_structures):
        loops_found = [s for s in structures if s in loop_structures]
        return {
            "error_category": "Loop Infinito — Controle de Fluxo",
            "pedagogical_diagnosis": f"O programa entrou em loop infinito. Laços detectados: {loops_found}.",
            "actionable_feedback": "Verifique se a variável de parada do laço está sendo modificada corretamente dentro do bloco.",
        }

    return {
        "error_category": "Timeout Anômalo",
        "pedagogical_diagnosis": "O programa excedeu o tempo limite, mas nenhum laço de repetição foi detectado na AST.",
        "actionable_feedback": "Verifique se há recursão infinita ou se o programa aguarda uma entrada (scanf) que nunca chega.",
    }


def _classify_warnings(warnings: str) -> dict | None:
    if "uninitialized" in warnings or "may be uninitialized" in warnings:
        return {
            "error_category": "Aviso — Variável Não Inicializada",
            "pedagogical_diagnosis": "O código compilou, mas uma variável é lida antes de receber um valor definido. Isso causa comportamento imprevisível.",
            "actionable_feedback": "Inicialize todas as variáveis no momento da declaração (ex: int x = 0;).",
        }

    if "unused variable" in warnings:
        return {
            "error_category": "Aviso — Variável Declarada e Não Utilizada",
            "pedagogical_diagnosis": "O código declara uma variável que nunca é lida ou usada na lógica do programa.",
            "actionable_feedback": "Remova a variável ou verifique se esqueceu de usá-la na lógica do exercício.",
        }

    if "implicit declaration" in warnings:
        return {
            "error_category": "Aviso — Declaração Implícita de Função",
            "pedagogical_diagnosis": "Uma função foi chamada sem declaração prévia visível. O compilador assumiu um protótipo genérico, o que pode causar erros silenciosos.",
            "actionable_feedback": "Adicione o #include correto ou declare o protótipo da função antes de chamá-la.",
        }

    return None


def _classify_success(structures: list) -> dict:
    if not structures:
        return {
            "error_category": "Solução Sequencial — Sem Controle de Fluxo",
            "pedagogical_diagnosis": "O código compilou e executou, mas não utilizou nenhuma estrutura de controle de fluxo (if, for, while, switch).",
            "actionable_feedback": "Verifique se o enunciado exige alguma estrutura de decisão ou repetição que ainda não foi implementada.",
        }

    loop_count = sum(structures.count(s) for s in ["For", "While", "DoWhile"])
    if_count = structures.count("If")

    if if_count >= 4 and loop_count == 0:
        return {
            "error_category": "Estrutura Suspeita — Excesso de Condicionais",
            "pedagogical_diagnosis": f"O código usa {if_count} blocos 'if' sem nenhum laço de repetição. Isso pode indicar uma tentativa de simular repetição com condicionais encadeados.",
            "actionable_feedback": "Considere substituir os condicionais encadeados por uma estrutura de repetição (for ou while).",
        }

    return {
        "error_category": "Lógica Estrutural Válida",
        "pedagogical_diagnosis": f"Código compilou e executou. Estruturas utilizadas: {structures}.",
        "actionable_feedback": "A estrutura de controle está operacional. A próxima etapa avaliará a precisão da saída em relação ao enunciado.",
    }
