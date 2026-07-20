# ResearchForge Architecture

## Project Overview

**ResearchForge** is an AI-powered research workflow automation platform that assists researchers throughout the complete academic research lifecycle. The system is built using a modular, agentic architecture where each agent specializes in a specific stage of the research process while sharing a common project memory.

---

# Core Architecture

```
User
 │
 ▼
Planning Agent
 │
 ▼
Literature Intelligence Agent
 │
 ▼
Literature Synthesis Agent
 │
 ▼
Manuscript Agent
 │
 ▼
Citation Agent
 │
 ▼
Reviewer Response Agent
```

All agents communicate through a shared **ProjectState**.

---

# Agents

## 1. Planning Agent ✅

### Responsibilities

* Refine research ideas
* Define project scope
* Generate objectives
* Generate keywords
* Help formulate research questions
* Update ProjectState

### Status

Completed

---

## 2. Literature Intelligence Agent 🚧

### Responsibilities

* Generate literature search queries
* Search arXiv
* Search OpenAlex
* Merge and rank papers
* Download research papers
* Read PDFs
* Extract structured insights from individual papers
* Store analyzed papers in ProjectState

### Internal Workflow

```
ProjectState
      │
      ▼
Query Builder
      │
      ▼
Arxiv Tool
      │
      ▼
OpenAlex Tool
      │
      ▼
Paper Manager
      │
      ▼
PDF Downloader
      │
      ▼
PDF Reader
      │
      ▼
LLM Analysis
      │
      ▼
Paper.analysis
```

### Status

Paper retrieval completed.

Paper understanding currently under development.

---

## 3. Literature Synthesis Agent

### Responsibilities

Uses analyzed papers to generate:

* Literature Review
* Research Gap
* Research Trends
* Future Research Directions
* Comparative Analysis

### Input

Analyzed papers from Literature Intelligence Agent.

### Output

Structured literature review stored in ProjectState.

### Status

Not started.

---

## 4. Manuscript Agent

### Responsibilities

Generate research manuscript section-by-section.

Supports:

* Title
* Abstract
* Introduction
* Methodology
* Experiments
* Results
* Conclusion
* LaTeX generation
* Overleaf-ready formatting

Uses previously generated project memory instead of inventing content.

### Status

Prompt designed.

Implementation pending.

---

## 5. Citation Agent

### Responsibilities

* Search Google Scholar
* Retrieve citations
* Generate BibTeX
* APA / IEEE formatting
* Find citations for user-provided statements
* Reference management

### Status

Prompt designed.

Implementation pending.

---

## 6. Reviewer Response Agent

### Responsibilities

Generate professional reviewer rebuttals using:

* Reviewer comments
* Current manuscript
* Few-shot examples from successful IEEE reviewer responses

Focuses on appropriate academic tone and deciding when to defend versus accept reviewer comments.

### Status

Prompt designed.

Implementation pending.

---

# Shared Memory

All agents share a common ProjectState.

Current information stored includes:

* Project information
* Objectives
* Keywords
* Literature
* Papers
* Manuscript
* Citations
* Reviewer comments
* Chat history
* Workflow history

---

# Tools

## Completed

* Ollama Client
* Arxiv Tool
* OpenAlex Tool
* Paper Manager
* PDF Downloader
* PDF Reader

## Planned

* Query Builder
* Google Scholar Tool
* LaTeX Compiler
* Overleaf Integration
* Reviewer Example Loader

---

# Data Models

## ProjectState

Global shared memory.

## Paper

Represents an individual research paper.

## PaperMetadata

Stores metadata such as:

* Title
* Authors
* Abstract
* Year
* Venue
* DOI
* PDF URL
* Local PDF Path
* Citation Count
* Categories
* arXiv ID

## PaperAnalysis

Will store structured knowledge extracted from each paper, including:

* Contribution
* Methodology
* Dataset
* Results
* Limitations
* Future Work
* Important Findings

---

# Current Development Status

## Completed

* Project architecture
* Folder structure
* Ollama integration
* Gemma integration
* Base Agent
* Base Tool
* Shared ProjectState
* Planning Agent
* Literature retrieval pipeline
* arXiv integration
* OpenAlex integration
* Paper deduplication
* PDF downloading
* PDF reading
* GitHub repository setup

---

## Currently Working On

Literature Intelligence Agent

Current objective:

Extract structured research knowledge from downloaded papers and populate PaperAnalysis.

---

# Design Principles

* Keep only **6 top-level agents**.
* Prefer reusable **tools** over creating additional agents.
* Use deterministic code whenever AI reasoning is unnecessary.
* Use the LLM only for reasoning-intensive tasks.
* Keep ProjectState as the single source of truth.
* Every new feature should have an independent playground test before integration.
* Maintain modularity so components can be reused by multiple agents.

---

# Long-Term Vision

ResearchForge should function as a complete AI research assistant capable of supporting researchers from the initial idea to the final reviewer response while maintaining project-wide memory and coordinating specialized agents through a unified workflow.
