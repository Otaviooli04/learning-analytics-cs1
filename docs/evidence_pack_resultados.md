# Evidence-pack — Capítulo de Resultados e Validação

Material de base para a escrita. Cada seção traz os números exatos extraídos do código e dos CSVs reais, seguidos de um parágrafo-âncora para expandir no texto final. Números medidos em 2026-06-13 sobre as turmas T1 e T2.

Reprodução:
```
cd backend && source venv/bin/activate
python tools/analyze_real_provas.py 25 --turma=T1 --save
python tools/analyze_real_provas.py 18 --turma=T2 --save
python evaluate_clustering.py            # experimentos sintéticos exp1-4
```
CSVs: `backend/results/real_metrics_T1_25provas.csv`, `real_metrics_T2_18provas.csv`.

---

## 1. Corpus e protocolo de validação

| | T1 | T2 |
|---|---|---|
| Provas | 25 | 18 |
| Submissões extraídas dos PDFs | 143 | 103 |
| Questões de código | 6 | 6 |
| Origem | export CodeRunner/Moodle (PDF) | idem, prova distinta |

As duas turmas resolveram **provas diferentes** (enunciados e questões distintos). O relato as mantém separadas em vez de agregar num pool único, o que permite testar se os resultados se repetem fora dos dados em que o sistema foi calibrado.

**Âncora:** A validação usa 246 submissões reais de duas turmas de Fundamentos de Programação, extraídas dos PDFs de correção do CodeRunner. A T1 calibrou a extração; a T2 funciona como conjunto de verificação, já que traz uma prova diferente e não participou de nenhum ajuste do pipeline.

---

## 2. Robustez da extração estática (tree-sitter)

| | T1 | T2 |
|---|---|---|
| Compila limpo (parse_ok) | 84% (120/143) | 80% (82/103) |
| Não compila | 16% (23/143) | 20% (21/103) |
| **Estruturas extraídas mesmo sem compilar** | **92% (131/143)** | **92% (95/103)** |

**Âncora:** Um em cada cinco códigos de prova não compila, o cenário comum em CS1. O parser tolerante a erros (tree-sitter) recupera as estruturas de controle em 92% das submissões nas duas turmas, incluindo grande parte das que falham na compilação. Esse número justifica a troca de pycparser por tree-sitter: pycparser aborta no primeiro erro de sintaxe e zeraria a análise estática justamente nos casos pedagogicamente mais interessantes. A coincidência de 92% em T1 e T2 indica que a robustez não depende do corpus específico.

---

## 3. Eficiência

| Etapa | T1 | T2 |
|---|---|---|
| Análise estática | 0,33 ms/sub | 0,31 ms/sub |
| Execução dinâmica (Docker GCC + test cases) | 2,06 s/sub | 2,16 s/sub |

**Âncora:** A análise estática custa frações de milissegundo e some no total. O gargalo é a execução em container isolado: cada submissão gasta cerca de 2 segundos, dominados pela inicialização do Docker e pela execução de um processo por caso de teste. Para uma turma de 25 alunos com 6 questões, a avaliação completa roda em poucos minutos. O clustering acrescenta o custo fixo do UMAP (cerca de 5 segundos), que pesa proporcionalmente mais em turmas pequenas. (Nota: a medição de 2,1 s/sub substitui a estimativa anterior de 0,87 s/sub, que media apenas a compilação sem execução de casos de teste.)

---

## 4. Distribuição de diagnósticos

Categorias atribuídas pelas heurísticas (questões com test cases):

**T1 (143):** Saída Incorreta 52 · Correto 48 · Erro de Compilação 17 · Sintaxe—Ponto e Vírgula 9 · Sintaxe—Var/Função Não Declarada 7 · Aviso—Var Não Utilizada 3 · Loop Infinito 3 · Aviso—Var Não Inicializada 3 · Sintaxe—Cabeçalho 1

**T2 (103):** Correto 40 · Saída Incorreta 32 · Erro de Compilação 11 · Sintaxe—Ponto e Vírgula 8 · Sintaxe—Var/Função Não Declarada 7 · Aviso—Var Não Inicializada 3 · Precisão de Saída—Casas Decimais 1 · Loop Infinito 1

**Âncora:** Os diagnósticos se concentram em duas categorias nas duas turmas: código correto e saída incorreta. Os erros de compilação reúnem cerca de 15% das submissões, com ponto e vírgula ausente e variável não declarada à frente. A presença de categorias específicas raras (precisão de casas decimais, loop infinito) mostra que o registro de verificadores cobre o que aparece, sem inflar artificialmente as classes frequentes. A semelhança entre as distribuições reforça que o conjunto de heurísticas captura padrões da disciplina, não particularidades de uma turma.

---

## 5. Qualidade do clustering no dado real

Médias entre as 6 questões. Pseudo ground truth = categoria de erro das heurísticas. Mesmas métricas do experimento sintético.

| Métrica | T1 | T2 |
|---|---|---|
| Silhouette | 0,413 | 0,370 |
| DBI | 0,825 | 0,800 |
| DBCV | 0,409 | 0,311 |
| **Purity** | **0,883** | **0,853** |
| Entropy | 0,320 | 0,438 |
| NMI | 0,770 | 0,727 |
| ARI | 0,582 | 0,581 |
| **Score composto** | **0,712** | **0,665** |

Tabela por questão disponível nos CSVs.

**Âncora:** A purity média de 0,88 (T1) e 0,85 (T2) mostra que cada cluster reúne, em sua maioria, alunos com o mesmo tipo de erro. O ARI de 0,58 nas duas turmas confirma concordância entre os agrupamentos e o diagnóstico pedagógico bem acima do acaso. As métricas internas geométricas (silhouette, DBCV) ficam moderadas, o que reflete a sobreposição natural de soluções corretas e quase-corretas no espaço de código. O valor do sistema para o professor está na coerência pedagógica de cada grupo, medida pela purity, não na separação geométrica.

---

## 6. Replicabilidade entre turmas (achado central)

Comparação dos números que mais importam:

| | T1 | T2 | Δ |
|---|---|---|---|
| Estruturas extraídas | 92% | 92% | 0 |
| Purity | 0,883 | 0,853 | 0,030 |
| ARI | 0,582 | 0,581 | 0,001 |
| Score | 0,712 | 0,665 | 0,047 |

**Âncora:** Os resultados se repetem em uma prova que o sistema nunca viu durante o desenvolvimento. Extração estrutural idêntica, purity e ARI praticamente iguais, score com diferença de menos de 0,05. A consistência entre duas provas distintas sustenta a validade externa de forma que uma única turma não permitiria: o pipeline responde a padrões da disciplina, não a um gabarito específico. Esse é o argumento mais forte do capítulo de validação.

---

## 7. Sintético versus real (ressalva de validade)

| | Sintético (exp1, 56 amostras) | Real (T1/T2) |
|---|---|---|
| Silhouette | ~0,65 | 0,37–0,41 |
| Purity | 1,00 (melhor estratégia) | 0,85–0,88 |

**Âncora:** O dado sintético produz métricas mais altas porque cada família foi gerada a partir de um template, o que cria fronteiras limpas entre grupos. O dado real tem ruído: alunos misturam estratégias, erram de formas intermediárias e produzem código que ocupa regiões sobrepostas. Reportar os dois lados é uma escolha de honestidade metodológica. O sintético serve para medir o teto (com ground truth exato, dá para verificar ARI próximo de 1,0); o real mede o que o professor encontra na prática.

---

## 8. Limitações e autocrítica

**Circularidade parcial.** A `error_category` das heurísticas serve ao mesmo tempo como pseudo ground truth (para purity, ARI, NMI) e, na estratégia `tfidf_category`/`behavioral`, como feature do clustering. Purity e ARI altos refletem em parte essa dependência. As métricas puramente geométricas (silhouette, DBCV) e a estratégia `tfidf` pura não sofrem do problema e servem de contraponto.

**Casos de teste visíveis.** A extração recupera os casos que o CodeRunner mostra ao aluno na correção. Casos ocultos, se existirem, não entram na avaliação; só o XML da plataforma os traria.

**Não-determinismo do Docker.** Submissões com loop dependente de tempo ou de leitura podem mudar de categoria entre execuções. No corpus, a Q1 oscila; as demais reproduzem.

**Espaçamento de saída.** A normalização de whitespace corrige falsos negativos em questões de matriz e lista alinhada, ao custo de afrouxar a verificação de formato exato. Trade-off explícito.

**Âncora:** A maior ameaça à validade é a circularidade entre o rótulo de avaliação e a feature de agrupamento. O texto trata isso de frente: relata as métricas geométricas independentes ao lado das pedagógicas e mostra que a estratégia `tfidf` pura, sem usar a categoria como feature, ainda agrupa de forma coerente. Reconhecer o limite e medir ao redor dele demonstra mais rigor do que esconder o número alto.

---

## Pendências de dados antes de fechar o capítulo
- O CSV antigo `real_metrics_25provas.csv` é redundante com `real_metrics_T1_25provas.csv` (mesma corrida). Remover.
- Decidir se entram T3/T4 para n maior (a extração já generaliza).
- Confirmar os números do sintético (exp1-4) na versão de 56 amostras / 5 estratégias antes de citar.
