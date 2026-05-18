# RAG AI Agent Demo

A simple AI agent that answers questions about your PDF documents using Claude and ChromaDB.

## How it works

1. You drop PDF files into the `docs/` folder
2. The ingestion script reads them, splits them into chunks, and stores them in a local vector database (ChromaDB)
3. When you ask a question, Claude uses a `search_docs` tool to look up relevant chunks from the database
4. Claude reads the results and gives you an answer with sources

## Setup

```
pip install -r requirements.txt
```

Create a `.env` file with your Anthropic API key:

```
ANTHROPIC_API_KEY=your-key-here
```

## Usage

Put your PDFs in the `docs/` folder, then ingest them:

```
python main.py ingest
```

Start asking questions:

```
python main.py
```

## QA Agent

There's also a QA agent that can test web apps. It reads your specs/PRDs from the vector DB, generates a test plan, and then executes the tests in a real browser using Playwright.

```
pip install playwright
playwright install chromium
```

Run it:

```
python main.py qa "test the login flow" --url https://staging.myapp.com
```

The agent will:
1. Search your docs for relevant specs
2. Propose a test plan
3. Wait for your approval
4. Open a browser and run the tests
5. Save a JSON report with screenshots to `reports/`

## Stack

- **Claude** - the AI that reads your results and answers questions
- **ChromaDB** - local vector database that stores and searches document chunks
- **pypdf** - reads text from PDF files
- **Anthropic tool use** - lets Claude call `search_docs` on its own when it needs information
- **Playwright** - browser automation for the QA agent
