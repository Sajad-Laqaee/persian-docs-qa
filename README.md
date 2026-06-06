# 🔍 Persian Document QA System

A **Retrieval-Augmented Generation (RAG)** system for answering questions over Persian documents using **hybrid search** (dense + sparse) and **Reranking** and Large Language Models. Built with Django REST Framework, Qdrant, and LangChain.

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.0-092E20.svg)](https://www.djangoproject.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)

---

## ✨ Features

- 📄 **Document Processing** — Supports `.docx` files
- 🔪 **Smart Chunking** — Persian-aware text splitting with semantic preservation (powered by [hazm](https://github.com/roshan-research/hazm))
- 🔎 **Hybrid Search** — Combines multiple retrieval strategies:
  - **Dense retrieval** via `intfloat/multilingual-e5-base` for semantic similarity
  - **Sparse retrieval (BM25)** for precise keyword matching
  - **Reciprocal Rank Fusion (RRF)** to merge results optimally
- 🎯 **Optional Reranking** — Cross-encoder reranking with `BAAI/bge-reranker-v2-m3`
- 🤖 **LLM-Powered Answers** — Answer generation via OpenRouter
- 🗂️ **Document Filtering** — Restrict search scope to specific documents
- 💬 **Conversation Management** — Persistent question/answer history
- 📊 **Admin Panel** — Full document management and history inspection
- 📖 **Interactive API Docs** — Swagger/OpenAPI UI out of the box
- 🐳 **Fully Dockerized** — Single-command deployment
- ⚡ **Device-Agnostic** — Automatically uses GPU if available, falls back to CPU

---

## 🏗️ Architecture

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│   Client    │────▶│  Django API  │────▶│  RAG Chain  │
│  (Swagger)  │     │    (DRF)     │     │              │
└─────────────┘     └──────────────┘     └───────┬──────┘
                           │                     │Reranker(optinal)
                    ┌──────┴──────┐       ┌──────┴───────┐
                    │  PostgreSQL │       │   Retriever  │
                    │  (metadata) │       │  ┌─────────┐ │
                    └─────────────┘       │  │ Dense   │ │
                                          │  │ + BM25  │ │
                                          │  │ + RRF   │ │
                                          │  └────┬────┘ │
                                          └───────┼──────┘
                                                  │
                                          ┌───────┴───────┐
                                          │    Qdrant     │
                                          │ (vector store)│
                                          └───────────────┘
```

### Processing Pipeline

**Indexing Flow:**
```
Upload → Parse → Normalize (hazm) → Chunk → Embed (dense) + BM25 (sparse) → Store in Qdrant
```

**Query Flow:**
```
Question → Hybrid Search → [Optional Rerank] → Build Context → LLM → Answer
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Django 5 + Django REST Framework |
| **Vector Database** | Qdrant |
| **Relational Database** | PostgreSQL |
| **Embedding Model** | sentence-transformers (`multilingual-e5-base`) |
| **Reranker** | `BAAI/bge-reranker-v2-m3` |
| **LLM Provider** | OpenRouter |
| **RAG Framework** | LangChain |
| **Persian NLP** | hazm |
| **WSGI Server** | Gunicorn |
| **Static Files** | WhiteNoise |
| **Containerization** | Docker + Docker Compose |

---

## 🚀 Quick Start

### Prerequisites

- [Docker](https://www.docker.com/) and Docker Compose
- An API key from [OpenRouter](https://openrouter.ai)

### Installation

1. **Clone the repository**
```bash
   git clone <repository-url>
   cd docs_qa_system
```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and set your `OPENROUTER_API_KEY` (and other values as needed).

3. **Build and start all services**
   ```bash
   docker compose up --build
   ```
   This launches three containers: `web` (Django), `postgres`, and `qdrant`.

4. **Create an admin user**
   ```bash
   docker compose exec web python manage.py createsuperuser
   ```


### Access Points

| Service | URL |
|---------|-----|
| 🌐 **Swagger API Docs** | http://localhost:8000/api/docs/ |
| 🔧 **Admin Panel** | http://localhost:8000/admin/ |

---

## 📡 API Reference

### `POST /api/ask/`

Submit a question and receive a RAG-generated answer.

**Request Body:**
```json
{
  "query": "When and where was Lionel Messi born?",
  "limit": 5,
  "use_hybrid": true,
  "document_id": null,
  "conversation_id": null
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | ✅ | The question to ask |
| `limit` | integer | ❌ | Number of chunks to retrieve (1–20, default: 5) |
| `use_hybrid` | boolean | ❌ | Use hybrid search vs. dense-only (default: true) |
| `document_id` | integer | ❌ | Restrict search to a specific document |
| `conversation_id` | integer | ❌ | Continue an existing conversation |

**Response:**
```json
// Request
{
  "query": "لیونل مسی در چه تاریخی متولد شد؟",
  "limit": 5,
  "use_hybrid": true,
  "document_id": null,        // optional: محدود به سند خاص
  "conversation_id": null     // optional: ادامه مکالمه
}

// Response
{
  "answer": "لیونل مسی در ۲۴ ژوئن ۱۹۸۷ در روزاریو، آرژانتین متولد شد.",
  "sources": [...],
  "search_mode": "hybrid",
  "conversation_id": 1,
  "question_id": 1
}
```


### `GET /api/history/`

Retrieve question/answer history.

**Query Parameters:**
- `conversation_id` (optional) — Filter by conversation

---

## ⚙️ Configuration

All settings are managed via the `.env` file.

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | — |
| `DEBUG` | Debug mode | `False` |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts | `localhost,127.0.0.1,web` |
| `OPENROUTER_API_KEY` | API key for LLM provider | — |
| `LLM_MODEL` | LLM model identifier | — |
| `EMBEDDING_MODEL` | Embedding model name | `intfloat/multilingual-e5-base` |
| `RERANKER_MODEL` | Reranker model name | `BAAI/bge-reranker-v2-m3` |
| `USE_RERANKER` | Enable reranking | `False` |
| `QDRANT_URL` | Qdrant connection URL | `http://qdrant:6333` |
| `QDRANT_COLLECTION` | Qdrant collection name | `docs_collection` |
| `DB_NAME` | PostgreSQL database name | — |
| `DB_USER` | PostgreSQL user | — |
| `DB_PASSWORD` | PostgreSQL password | — |
| `DB_HOST` | PostgreSQL host | `postgres` |
| `DB_PORT` | PostgreSQL port | `5432` |

---

## 🧪 Example Usage

**Using cURL:**
```bash
curl -X POST http://localhost:8000/api/ask/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What medical condition did Messi have as a child?",
    "use_hybrid": true
  }'
```

**Using the Swagger UI:**

Navigate to http://localhost:8000/api/docs/ and try the `/api/ask/` endpoint interactively.

---

## 📐 Design Decisions

This section documents key engineering choices and their rationale:

- **Hybrid Search (Dense + Sparse + RRF):**
  Dense embeddings capture semantic meaning while BM25 handles exact keyword matches. RRF fusion combines both ranking lists without requiring score normalization, yielding more robust retrieval.

- **Optional Reranking:**
  A cross-encoder reranker was implemented and benchmarked. For the current dataset size, it increased latency 3–5× without measurable improvement in final answer quality. It is therefore **disabled by default** but remains available via the `USE_RERANKER` flag — a data-driven decision rather than blind adoption.

- **Device-Agnostic Inference:**
  Models automatically detect and use a GPU via `torch.cuda.is_available()`, falling back to CPU. This makes the system portable across environments without code changes.

- **Single Gunicorn Worker with Threads:**
  To prevent duplicating heavy ML models in memory across processes, a single worker with multiple threads is used. Models are warmed up at worker boot to avoid first-request latency.

- **WhiteNoise for Static Files:**
  Static assets are served directly by the application, eliminating the need for a separate nginx container and keeping the deployment self-contained.

- **Persistent Volumes:**
  PostgreSQL data, Qdrant storage, and the Hugging Face model cache are persisted via Docker volumes, ensuring data and downloaded models survive container restarts.

---

## 📂 Project Structure

```
docs_qa_system/
├── config/                 # Django project settings & URLs
├── core/                   # Shared services
│   ├── embeddings.py       # Embedding model loader
│   ├── vectorstore.py      # Qdrant client & BM25 encoder
│   ├── reranker.py         # Cross-encoder reranker
│   └── llm.py              # LLM client (OpenRouter)
├── documents/              # Document management
│   ├── models.py           # Document & Chunk models
│   ├── admin.py            # Admin interface
│   └── services/
│       ├── parser.py       # File parsing (.docx/.pdf/.txt)
│       ├── chunker.py      # Persian-aware chunking
│       └── indexer.py      # Embedding & indexing
├── qa/                     # Question answering
│   ├── models.py           # Conversation & Question models
│   ├── views.py            # API endpoints
│   ├── serializers.py      # Request/response schemas
│   └── services/
│       ├── retriever.py    # Hybrid & dense search
│       └── rag_chain.py    # RAG orchestration
├── demo_data/              # Sample documents
├── Dockerfile
├── docker-compose.yml
├── entrypoint.sh
├── requirements.txt
└── .env.example
```

---

## 🔧 Development (Without Docker)

For local development with infrastructure-only Docker:

1. **Start infrastructure** (PostgreSQL + Qdrant)
   ```bash
   docker compose -f docker-compose.infra.yml up -d
   ```

2. **Set up Python environment**
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Run migrations and start the server**
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

---
## 👤 Author

**Sajad laqaee**
