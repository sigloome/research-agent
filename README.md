# Velvet Research

**Velvet Research** is an AI-powered research assistant designed to help you organize and interact with academic knowledge.

## Features

- **Paper Management**: Search and manage academic papers from ArXiv.
- **Book Library**: Integration with Z-Library for book discovery and management.
- **AI Chat Assistant**: Interact with your library using an intelligent agent powered by Claude.
- **Document Processing**: Upload and process local documents.

## Development Philosophy

We follow **Documentation-Driven Development (DocDD)**.
Please read [CONTRIBUTING.md](./CONTRIBUTING.md) to understand how we build with **Vibe** and **Precision**.

## Tech Stack

- **Backend**: Python, FastAPI, Uvicorn, Claude Agent SDK
- **Frontend**: TypeScript, React, Vite, TailwindCSS
- **Database**: SQLite

## Prerequisites

- Python 3.8+
- Node.js & npm (v18+ recommended)
- Git

## Getting Started

### 1. Quick Setup (Recommended)

Run the interactive setup wizard to configure the environment automatically:

```bash
./scripts/init_wizard.sh
```

### 2. Manual Installation

If you prefer to set up manually:

**Backend Setup:**

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# .\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

**Frontend Setup:**

```bash
cd frontend
npm install
cd ..
```

### 3. Configuration

Create a `.env` file in the root directory. You can use `.env.example` as a template if one exists, otherwise set the following variables:

```env
ANTHROPIC_API_KEY=your_api_key_here
# Optional: Z-Library credentials if using Z-Library MCP
ZLIBRARY_EMAIL=your_email
ZLIBRARY_PASSWORD=your_password
```

### 4. Running the Application

The easiest way to start the application is using the provided start script:

```bash
./scripts/start.sh
```

This will start:
- Backend server at `http://localhost:18000`
- Frontend application at `http://localhost:15173`

**Manual Start:**

If you prefer to run services manually:

**Backend:**
```bash
source venv/bin/activate
python -m uvicorn backend.app:app --host 0.0.0.0 --port 18000
```

**Frontend:**
```bash
cd frontend
npm run dev
```

## Documentation

For more detailed agent guidelines, refer to [AGENTS.md](./AGENTS.md).
