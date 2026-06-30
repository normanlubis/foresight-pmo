# 🎯 Foresight PMO - A Prototype of AI Project Orchestrator

A Streamlit prototype showcasing AI-powered project management:
**Timeline Prediction · Owner Assignment · Scenario Simulation**

---

## Pages

| Page | What it does |
|------|-------------|
| 📊 Project Overview | Task board, epic progress, sprint velocity |
| 🔮 Timeline Prediction | AI forecast with Monte Carlo simulation, confidence intervals, risk analysis |
| 👤 Owner Assignment | AI-ranked recommendations by skill map, capacity & velocity |
| 🔀 Scenario Simulation | What-if modeling (hire, descope, parallelize, etc.) |

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