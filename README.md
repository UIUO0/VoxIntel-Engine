# VoxIntel-Engine

## Overview
Real-time Voice AI Agent with Live Sentiment Analysis (End-to-End Pipeline).

## Project Structure

```
VoxIntel-Engine/
├── data/                   # Storage for SQLite DB (.db) and logs
├── src/
│   ├── core/               # AI Engine (Moshi wrapper & Subprocess management)
│   ├── analysis/           # NLP & Sentiment Analysis (VADER logic)
│   ├── dashboard/          # UI Presentation (Streamlit App)
│   ├── database/           # Data Persistence (SQLite models & connection)
│   └── utils/              # Shared configurations and helpers
├── tests/                  # Unit and integration tests
├── main.py                 # Application Entry Point
├── requirements.txt        # Project dependencies
└── README.md               # Project documentation
```

## Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Ensure `moshi_mlx` is installed manually.
