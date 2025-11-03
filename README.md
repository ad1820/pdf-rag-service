# PDF Agent Microservice 🤖

A stateless, secure PDF question-answering service powered by LangChain and OpenAI. Built as a microservice to handle PDF indexing and intelligent Q&A with conversation context.

## ✨ Features

- 📄 **PDF Processing** - Extract and index text from PDFs
- 🧠 **AI Q&A** - Answer questions using GPT-4.1-mini
- 💬 **Conversation Context** - Maintains chat history awareness
- 💾 **Smart Caching** - Fast subsequent queries with vectorstore caching
- 🔒 **API Key Protection** - Secure endpoints with authentication
- ⚡ **Stateless Design** - No user data stored, fully scalable

## 🏗️ Architecture

```
Your Backend (Auth, Users, Storage)
         ↓
    HTTP Request (with API Key)
         ↓
PDF Agent Service (Stateless)
  ├─ Receives: file_id + query + history
  ├─ Processes: RAG with LangChain + OpenAI
  └─ Returns: AI-generated answer
```

**Key Principle:** This service has NO state. Your backend manages users, authentication, and chat history. The agent only processes requests.

## 📋 Prerequisites

- Python 3.11+
- OpenAI API Key
- MongoDB (handled by your backend)

## 🚀 Quick Start

### 1. Clone & Setup

```bash
git clone https://github.com/yourusername/pdf-agent-service.git
cd pdf-agent-service
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
# Copy template
cp .env.example .env

# Edit .env and add your keys:
# OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
# AGENT_API_KEY=your-secret-key-here
```

**Generate AGENT_API_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 5. Run the Service

```bash
uvicorn main:app --reload --port 8000
```

Service runs at `http://localhost:8000`

### 6. Test

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "healthy", "indexed_files": 0}
```

## 📚 API Endpoints

### Public Endpoints

#### `GET /`
Service information and available endpoints.

#### `GET /health`
Health check endpoint (no authentication required).

**Response:**
```json
{
  "status": "healthy",
  "indexed_files": 0
}
```

### Protected Endpoints (Require `X-API-Key` Header)

#### `POST /index_pdf`
Index a PDF file for querying.

**Headers:**
```
X-API-Key: your-agent-api-key
```

**Request (form-data):**
- `file_id` (string): Unique identifier from your backend
- `file` (file): PDF file to index

**Response:**
```json
{
  "file_id": "abc123",
  "file_name": "document.pdf",
  "text_length": 5432,
  "already_indexed": false
}
```

#### `POST /query`
Query an indexed PDF with conversation context.

**Headers:**
```
X-API-Key: your-agent-api-key
```

**Request (form-data):**
- `file_id` (string): File identifier
- `query` (string): User's question
- `chat_history` (string): JSON array of previous messages

**Example chat_history:**
```json
[
  {"role": "user", "content": "What is this about?"},
  {"role": "assistant", "content": "This document discusses..."}
]
```

**Response:**
```json
{
  "response": "Based on the document, the answer is..."
}
```

#### `DELETE /cache/{file_id}`
Remove a file from vectorstore cache.

**Headers:**
```
X-API-Key: your-agent-api-key
```

**Response:**
```json
{
  "message": "Removed document.pdf from cache"
}
```

#### `GET /cache_stats`
View cached files statistics.

**Headers:**
```
X-API-Key: your-agent-api-key
```

**Response:**
```json
{
  "indexed_files": 2,
  "files": [
    {
      "file_id": "abc123",
      "name": "document.pdf",
      "text_length": 5432
    }
  ]
}
```

#### `POST /clear_cache`
Clear entire vectorstore cache.

**Headers:**
```
X-API-Key: your-agent-api-key
```

## 🔒 Security

### API Key Protection
All important endpoints require `X-API-Key` header. Without it:

```json
{"detail": "Invalid API key"}
```

### Best Practices
- ✅ Store API keys in environment variables
- ✅ Never commit `.env` to version control
- ✅ Use strong, random API keys (32+ characters)
- ✅ Rotate keys if compromised
- ✅ Use HTTPS in production
- ❌ Don't expose agent URL in frontend code
- ❌ Don't hardcode API keys in source code


## 🚢 Deployment

### Deploy to Render

1. Push code to GitHub
2. Connect Render to your repository
3. Render auto-detects Python/Docker
4. Add environment variables:
   - `OPENAI_API_KEY`
   - `AGENT_API_KEY`
5. Deploy!

**Render will provide:** `https://your-app.onrender.com`

## 🛠️ Tech Stack

- **FastAPI** - Modern Python web framework
- **LangChain 1.0** - LLM orchestration
- **OpenAI GPT-4.1-mini** - Language model
- **FAISS** - Vector database for embeddings
- **PyPDF2** - PDF text extraction
- **Pydantic** - Data validation
- **Python 3.11** - Runtime

## 📊 Project Structure

```
pdf-agent-service/
├── main.py                 # FastAPI app & endpoints
├── agents/
│   └── pdf_chain.py       # LangChain RAG chain
├── models/
│   ├── pdf_processor.py   # PDF text extraction
│   └── embeddings_faiss.py # FAISS vectorstore
├── config/
│   └── settings.py        # Environment configuration
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker container
├── docker-compose.yml    # Local Docker setup
├── .env.example          # Environment template
├── .gitignore           # Git ignore rules
└── README.md            # This file
```


**Built with ❤️ for intelligent PDF processing**
