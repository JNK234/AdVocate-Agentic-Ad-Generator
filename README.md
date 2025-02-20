# AI Marketing Research & Ad Generator

An AI-powered platform that automates market research, marketing strategy development, and advertisement generation through specialized AI agents.

## Core Components

### Research Agent (`src/agents/research/`)
- Conducts automated market research
- Generates research questions
- Analyzes market data
- Produces structured reports

### Marketing Agent (`src/agents/marketing/`)
- Analyzes brand voice
- Creates audience profiles
- Generates campaign ideas
- Develops marketing strategies

### Ad Generator (`src/agents/AdGen/`)
- Creates ad content
- Generates image prompts
- Processes campaigns
- Handles visual assets

## Infrastructure

### Data Storage (`models/vectorstore/`)
- ChromaDB integration
- Two-tier caching system
- Session-based caching
- Persistent storage

### Core Systems (`src/core/`)
- LLM integration
- Tool management
- Utility functions

## Features

### Analysis Pipeline
1. Market Research
2. Brand Analysis
3. Strategy Development
4. Campaign Generation
5. Content Creation

### Campaign Generation
- Multiple campaign variations
- Core messaging
- Visual themes
- Social media strategy
- Implementation plans

### Web Interface
- Streamlit-based dashboard
- Research and Marketing tabs
- Progress tracking
- History management

## Setup

1. Configure environment:
```bash
cp .env.template .env
# Edit .env with your credentials
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run application:
```bash
streamlit run app.py
```

## Requirements
- Python 3.8+
- Azure OpenAI API access
- ChromaDB
- Streamlit
- LangChain

## Data Flow
Research → Marketing → Ad Generation

## Documentation
See individual module directories for detailed documentation:
- `/src/agents/research/`
- `/src/agents/marketing/`
- `/src/agents/AdGen/`
