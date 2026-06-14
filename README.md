# Multi-Agent Research Engine 🤖

An autonomous, enterprise-grade research platform that orchestrates a swarm of specialized AI agents to plan, scrape, synthesize, and export high-quality technical reports. 

## 🚀 Key Features

* **Autonomous Agent Swarm:** Orchestrates a lifecycle of 8+ agents, including Planners, Scrapers, RAG retrievers, Writers, and Critics.
* **Live Agent Streaming (SSE):** Real-time UI updates using Server-Sent Events—watch the agents think and draft in your terminal and browser.
* **Dynamic Web Scraping:** Integrated **Playwright** engine to bypass bot protection and render JavaScript-heavy pages (e.g., modern SPAs).
* **Intelligent Caching:** Implements **Redis** for cross-session memory, reducing API costs and drop-to-zero latency for repeated queries.
* **Production-Ready Export:** Native support for PDF and Word (`.docx`) document generation with proper formatting and structure.
* **Self-Correction Loop:** An automated Critic Agent loop that enforces quality standards, forcing revisions until the content meets a minimum threshold.

## 🛠 Tech Stack

* **Backend:** FastAPI (Python), LangChain
* **Frontend:** Next.js (React), Tailwind CSS, Lucide Icons
* **Infrastructure:** Redis (Caching), Playwright (Browser Automation), ChromaDB (Vector Store)
* **AI Integration:** OpenAI GPT / Anthropic Claude (via LangChain)

## 📦 Setup & Installation

### Prerequisites
* Node.js (v18+)
* Python (v3.10+)
* Docker (for Redis)

### Backend
1. `cd backend`
2. `python -m venv venv`
3. `source venv/bin/activate` (or `venv\Scripts\activate` on Windows)
4. `pip install -r requirements.txt`
5. `python main.py`

### Frontend
1. `cd frontend`
2. `npm install`
3. `npm run dev`

## 🏗 Architecture Logic

The system follows a feedback-driven orchestration loop. Unlike standard chat apps, this engine operates in parallel:

1.  **Planner:** Decomposes complex topics into structured sub-questions.
2.  **Search & Scraper:** Parallel workers boot headless Chrome instances to gather data from dynamic sources.
3.  **RAG Agent:** Performs semantic search to inject only the most relevant context into the writing buffer.
4.  **Writer/Critic Loop:** A strict "Draft & Evaluate" loop that guarantees citations and content quality before publication.
5.  **Editor:** Compiles fragmented sections into a cohesive Markdown document.

## 🔐 Security Note
This project uses environment variables (`.env`) for API keys. **Never** push your `.env` file to a public repository. The provided `.gitignore` file is configured to exclude these sensitive credentials.

---

### License
MIT License - feel free to use, modify, and build upon this engine.