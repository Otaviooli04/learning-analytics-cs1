# Learning Analytics — CS1

Sistema de Learning Analytics para apoio docente em disciplinas introdutórias de programação (CS1). O professor faz upload de uma prova em PDF, o Gemini estrutura as questões de código, o professor adiciona test cases ocultos, e os alunos submetem código C que é compilado, executado e diagnosticado automaticamente.

## Arquitetura

```
backend/app/
  main.py
  api/routes/
    exam.py           — Upload de prova, gerenciamento de test cases, resultados
    submission.py     — Avaliação de submissão de código
  engine/
    document_parser.py      — Extrai texto de PDF/DOCX (pymupdf, python-docx)
    semantic_extractor.py   — Gemini 2.5 Flash: texto → JSON de questões de código
    dynamic_analyzer.py     — Compila C via Docker GCC, executa contra cada test case
    static_analyzer.py      — AST via pycparser, extrai estruturas de controle
    heuristics.py           — Diagnóstico pedagógico (estruturas + resultados dos testes)
    evaluators/
      code_evaluator.py     — Orquestra dynamic + static + heuristics
  models/
    database.py   — SQLAlchemy engine + sessão
    orm.py        — Modelos ORM: Exam, Question, TestCase, Submission, SubmissionTestResult
    schemas.py    — Schemas Pydantic
  services/
    exam_service.py       — Upload, test cases, resultados agregados
    submission_service.py — Busca contexto do banco, avalia, persiste resultado
  ml/cluster.py             — TF-IDF → UMAP → HDBSCAN (em desenvolvimento)
  llm/feedback_generator.py — Feedback por cluster via Gemini (planejado)
```

## Fluxo

1. **Professor** faz upload da prova (PDF/DOCX) → Gemini extrai questões de código com estruturas obrigatórias/proibidas
2. **Professor** adiciona test cases ocultos por questão
3. **Aluno** submete código C → sistema compila (Docker), roda contra os test cases e analisa a AST
4. **Professor** consulta resultados agregados por questão com distribuição de erros

## Pré-requisitos

- Python 3.10+
- Docker rodando — usado para compilar e executar o código C dos alunos
- PostgreSQL 16+
- Node.js 18+ (frontend)
- Chave da API Gemini — [aistudio.google.com/apikey](https://aistudio.google.com/apikey)

## Instalação

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Crie `backend/.env`:

```env
GEMINI_API_KEY=sua_chave_aqui
DATABASE_URL=postgresql://usuario:senha@localhost:5432/learning_analytics
```

### Banco de dados (PostgreSQL)

```bash
sudo -u postgres psql -c "CREATE USER analytics_user WITH PASSWORD 'analytics_pass';"
sudo -u postgres psql -c "CREATE DATABASE learning_analytics OWNER analytics_user;"
```

As tabelas são criadas automaticamente na primeira execução do servidor.

### Frontend

```bash
cd frontend
npm install
```

## Execução

### Backend

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
# Disponível em http://localhost:8000
# Swagger UI em http://localhost:8000/docs
```

### Frontend

```bash
cd frontend
npm run dev
```

## API Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/` | Health check |
| POST | `/exam/upload` | Upload de prova PDF/DOCX → estrutura questões via Gemini |
| GET | `/exam/{id}` | Consulta prova com contagem de test cases por questão |
| POST | `/exam/{id}/questions/{num}/testcases` | Professor adiciona test cases ocultos |
| GET | `/exam/{id}/results` | Resultados agregados por questão (distribuição de erros, submissões) |
| POST | `/submission/evaluate` | Submete código C → compila, testa e diagnostica |

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Backend | Python 3, FastAPI, Pydantic, Uvicorn |
| Banco de dados | PostgreSQL 16 + SQLAlchemy |
| Análise dinâmica | Docker + GCC |
| Análise estática | pycparser |
| IA / LLM | Google Gemini 2.5 Flash |
| ML | scikit-learn, umap-learn, hdbscan (em desenvolvimento) |
| Frontend | React + Vite |

## Estrutura de Branches

| Branch | Finalidade |
|--------|-----------|
| `main` | Produção — releases estáveis |
| `dev` | Integração de features |
| `feature/<nome>` | Novas funcionalidades |
| `fix/<nome>` | Correções de bugs |
