# Learning Analytics — CS1

Sistema de Learning Analytics para apoio docente em disciplinas introdutórias de programação (CS1). Analisa submissões de código C com análise estática (AST), dinâmica (execução isolada via Docker) e heurísticas pedagógicas, com clustering ML e geração de feedback via LLM (Gemini).

## Arquitetura

```
backend/app/
  main.py                    — FastAPI app
  api/routes.py              — Rotas da API REST
  engine/
    dynamic_analyzer.py      — Compila e executa código C via Docker (--network none, timeout 5s)
    static_analyzer.py       — Gera AST com pycparser, extrai estruturas de controle de fluxo
    heuristics.py            — Cruza resultados dinâmico + estático → diagnóstico pedagógico
    semantic_extractor.py    — Usa Gemini API para extrair metadados do enunciado do exercício
  models/schemas.py          — Modelos Pydantic (CodeRequest, CompileResponse, ASTResponse)
  llm/                       — Geração de feedback via LLM (planejado)
  ml/                        — Clustering UMAP + HDBSCAN (planejado)
  services/                  — Camada de serviços (exercícios, submissões)
```

**Fluxo de dados:**
1. **Fase 1 (Docente):** Professor insere enunciado → Gemini extrai metadados JSON (`requires_loop`, `required_structures`, `forbidden_structures`)
2. **Fase 2 (Estudante):** `CodeRequest` → `dynamic_analyzer` (Docker GCC) + `static_analyzer` (pycparser) → `heuristics.classify_error()` → diagnóstico pedagógico → clustering → feedback LLM

## Pré-requisitos

- Python 3.10+
- Docker (rodando) — o `dynamic_analyzer.py` usa `docker run gcc:latest`
- Node.js 18+
- Variável de ambiente `GEMINI_API_KEY` — necessária para o `semantic_extractor.py`

## Instalação

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Crie um arquivo `.env` em `backend/`:

```env
GEMINI_API_KEY=sua_chave_aqui
```

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
```

### Frontend

```bash
cd frontend
npm run dev      # servidor de desenvolvimento com HMR
npm run build    # build de produção
npm run lint     # ESLint
```

## API Endpoints

| Método | Rota         | Descrição                                                      |
|--------|--------------|----------------------------------------------------------------|
| GET    | `/`          | Health check                                                   |
| POST   | `/evaluate`  | Compila e executa código C, retorna `CompileResponse`          |
| POST   | `/ast`       | Análise estática AST, retorna `ASTResponse` com estruturas de controle |

## Stack

- **Backend:** Python 3, FastAPI, Pydantic, Uvicorn
- **Análise estática:** pycparser
- **Análise dinâmica:** subprocess + Docker + GCC
- **IA/LLM:** Google Gemini API
- **ML:** scikit-learn, UMAP, HDBSCAN
- **Banco de dados:** PostgreSQL + SQLAlchemy (planejado)
- **Frontend:** React + Vite

## Estrutura de Branches

| Branch              | Finalidade                          |
|---------------------|-------------------------------------|
| `main`              | Produção — releases estáveis        |
| `dev`               | Integração de features              |
| `feature/<nome>`    | Novas funcionalidades               |
| `fix/<nome>`        | Correções de bugs                   |
