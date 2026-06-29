# 🎯 AI Project Orchestrator — Prototype

A Streamlit prototype showcasing AI-powered project management:
**Timeline Prediction · Owner Assignment · Scenario Simulation**

---

## Setup

### 1. Install dependencies
```bash
pip install streamlit anthropic plotly pandas numpy
```

### 2. Set your Anthropic API key
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### 3. Run the app
```bash
cd orchestrator/
streamlit run app.py
```

---

## Pages

| Page | What it does |
|------|-------------|
| 📊 Project Overview | Task board, epic progress, sprint velocity |
| 🔮 Timeline Prediction | AI forecast with Monte Carlo simulation, confidence intervals, risk analysis |
| 👤 Owner Assignment | AI-ranked recommendations by skill map, capacity & velocity |
| 🔀 Scenario Simulation | What-if modeling (hire, descope, parallelize, etc.) |
| 💬 Ask the AI | Chat assistant with full project context |

---

## File structure

```
orchestrator/
├── app.py          # Main Streamlit app (all pages)
├── mock_data.py    # Mocked project, team & sprint data
├── ai_engine.py    # LLM API calls (4 AI functions)
└── README.md
```

---

## Customising the mock data

Edit `mock_data.py` to change:
- **TEAM_MEMBERS** — skills, capacity, velocity multipliers
- **TASKS** — your backlog, story points, dependencies
- **SPRINT_HISTORY** — past velocity data
- **TARGET_DATE** — project deadline

All AI reasoning adapts automatically to your data.