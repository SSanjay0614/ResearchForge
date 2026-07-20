# 📚 ResearchForge

### A Multi-Agent Research Workflow Automation System

ResearchForge is an **agentic AI platform** that automates key stages of the academic research lifecycle through a team of specialized AI agents. Instead of functioning as a generic chatbot, it orchestrates dedicated agents for **research planning, literature discovery, literature synthesis, manuscript drafting, citation management, and reviewer response generation** while maintaining a shared project workspace.

Built using **LangGraph** and **local LLMs with Ollama**, ResearchForge provides researchers with an intelligent workspace that streamlines repetitive research tasks while keeping them in control of every stage.

---

## 🚀 Why ResearchForge?

Academic research involves repetitive and time-consuming tasks such as searching literature, analyzing papers, drafting manuscripts, managing citations, and responding to reviewer comments. These tasks often require switching between multiple tools and repeating similar workflows.

ResearchForge automates these research workflows by coordinating specialized AI agents through a shared project memory and persistent workspace. Rather than replacing the researcher, it assists throughout the research lifecycle by reducing manual effort and improving productivity.

---

## ✨ Features

- 🧠 **Research Planning**
  - Generate research ideas
  - Define objectives and project scope

- 📄 **Literature Discovery**
  - Search papers from ArXiv and OpenAlex
  - Build a project-specific paper library

- 📖 **Literature Synthesis**
  - Summarize research papers
  - Identify research gaps
  - Generate structured literature reviews

- ✍️ **Manuscript Generation**
  - Generate publication-ready LaTeX sections
  - Rewrite, improve, or continue existing content
  - Support custom manuscript sections

- 📑 **Citation Management**
  - Generate BibTeX entries
  - Retrieve citation metadata
  - Recommend references supporting research claims

- 📝 **Reviewer Response Generation**
  - Draft professional rebuttals
  - Suggest manuscript revisions
  - Respond to reviewer comments

- 💾 **Project Workspace**
  - Persistent project memory
  - Save and resume research projects
  - Interactive Streamlit interface

---

## 🔄 Workflow

```text
                    User Request
                          │
                          ▼
               LangGraph Workflow Router
                          │
                          ▼
              Select Specialized AI Agent
                          │
                          ▼
        Research APIs • Project Memory • Storage
                          │
                          ▼
               Updated Research Workspace
```

---

## 🏗️ Architecture

```text
                           User
                             │
                             ▼
                  Streamlit Web Interface
                             │
                             ▼
                    LangGraph Workflow Router
                             │
      ┌──────────┬──────────┬──────────┬──────────┬──────────┬──────────┐
      ▼          ▼          ▼          ▼          ▼          ▼
 Planning   Literature  Synthesis  Manuscript  Citation  Reviewer
   Agent       Agent      Agent       Agent      Agent      Agent
      └──────────┬──────────┴──────────┬──────────┴──────────┘
                 ▼
          Shared Project Memory
                 │
        ┌────────┴─────────┐
        ▼                  ▼
   External APIs      Project Storage
 (ArXiv • OpenAlex •    (JSON Workspace)
      CrossRef)
```

---

## 🛠️ Tech Stack

| Technology | Purpose |
|------------|---------|
| **Python** | Core application development |
| **LangGraph** | Multi-agent workflow orchestration |
| **Ollama** | Local Large Language Model (LLM) inference |
| **Streamlit** | Interactive web application |
| **Pydantic** | Data validation and state management |
| **APIs** | **ArXiv**, **OpenAlex**, and **CrossRef** for literature retrieval, metadata, and citations |

---

## 🚀 Getting Started

### Clone the repository

```bash
git clone https://github.com/<your-username>/ResearchForge.git

cd ResearchForge
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Pull the required Ollama model

```bash
ollama pull gemma4
```

### Launch the application

```bash
streamlit run frontend/app.py
```

---

## 🔮 Future Work

- RAG-powered long-term project memory
- Google Scholar integration
- Automatic PDF ingestion and indexing
- Overleaf synchronization
- Journal-specific manuscript templates
- Multi-user collaboration

---

## 👨‍💻 Author

**Sanjay S**

B.Tech Computer Science and Engineering  
VIT Chennai

---
