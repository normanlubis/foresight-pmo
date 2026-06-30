import os
import json
from datetime import timedelta
from google import genai
from google.genai import types
import streamlit as st

from mock_data import CURRENT_DATE, TARGET_DATE, SPRINT_LENGTH_DAYS

try:
    from google.api_core import exceptions as api_exceptions
except Exception:
    api_exceptions = None

# Using the recommended standard model for general text and reasoning tasks
# MODEL = "gemini-2.5-flash"
# MODEL = "gemini-2.5-flash-lite"
MODEL = "gemini-3.1-flash-lite"

def _get_client():
    # The client automatically pulls GEMINI_API_KEY from the environment if api_key isn't explicit,
    # but we will pass it explicitly to match your previous setup.
    # return genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        try:
            api_key = st.secrets["GEMINI_API_KEY"]
        except Exception:
            api_key = None

    if not api_key:
        st.error("🔑 Gemini API Key not found! Please configure it in your environment or Streamlit Secrets.")
        st.stop()

    return genai.Client(api_key=api_key)

def _is_service_unavailable_error(exc: Exception) -> bool:
    if api_exceptions is not None:
        try:
            if isinstance(exc, api_exceptions.ServiceUnavailable):
                return True
        except Exception:
            pass

    code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
    if code == 503:
        return True

    message = str(exc).upper()
    return "UNAVAILABLE" in message or "503" in message


def _chat(system: str, user: str, max_tokens: int = 900, response_schema: dict = None) -> str:
    client = _get_client()
    
    # Configure parameters using the modern GenerateContentConfig object
    config = types.GenerateContentConfig(
        system_instruction=system,
        max_output_tokens=max_tokens,
    )
    
    # If a schema is provided, enforce a native JSON output matching the specification
    if response_schema:
        config.response_mime_type = "application/json"
        config.response_schema = response_schema

    try:
        resp = client.models.generate_content(
            model=MODEL,
            contents=user,
            config=config,
        )
        return resp.text.strip()
    except Exception as exc:
        if _is_service_unavailable_error(exc):
            st.error(
                "The AI model is currently experiencing high demand. Spikes in demand are usually temporary. Please try again later."
            )
            st.stop()
        raise


def _normalize_timeline_dates(result: dict) -> dict:
    try:
        sprints_remaining = int(result.get("sprints_remaining", 0))
    except (TypeError, ValueError):
        return result

    expected_date = (CURRENT_DATE + timedelta(days=sprints_remaining * SPRINT_LENGTH_DAYS)).strftime("%Y-%m-%d")
    result["predicted_date"] = expected_date
    return result


# ── 1. Timeline prediction ───────────────────────────────────────────────────
def ai_predict_timeline(stats: dict, sprint_history: list, scenario_overrides: dict = None) -> dict:
    overrides_text = ""
    if scenario_overrides:
        overrides_text = f"\nScenario overrides: {json.dumps(scenario_overrides)}"

    system = (
        "You are an expert software delivery coach and project forecaster. "
        "Analyse sprint velocity data and project completion metrics assuming all sprint team members are commited through project duraion."
    )
    user = f"""
Project stats:
{json.dumps(stats, indent=2)}

Sprint history (last 8 sprints):
{json.dumps(sprint_history, indent=2)}

Current date: {CURRENT_DATE.strftime('%Y-%m-%d')}
Target delivery date: {TARGET_DATE.strftime('%Y-%m-%d')}
Sprint length: {SPRINT_LENGTH_DAYS} days
{overrides_text}
"""
    
    # Define the precise schema using OpenAPI 3.0 specification properties
    schema = {
        "type": "OBJECT",
        "properties": {
            "predicted_date": {"type": "STRING"},
            "confidence_p50": {"type": "STRING"},
            "confidence_p95": {"type": "STRING"},
            "sprints_remaining": {"type": "INTEGER"},
            "avg_velocity": {"type": "NUMBER"},
            "trend": {"type": "STRING", "enum": ["improving", "stable", "declining"]},
            "on_track": {"type": "BOOLEAN"},
            "risk_level": {"type": "STRING", "enum": ["low", "medium", "high"]},
            "key_risks": {"type": "ARRAY", "items": {"type": "STRING"}},
            "recommendations": {"type": "ARRAY", "items": {"type": "STRING"}},
            "narrative": {"type": "STRING"}
        },
        "required": [
            "predicted_date", "confidence_p50", "confidence_p95", "sprints_remaining", 
            "avg_velocity", "trend", "on_track", "risk_level", "key_risks", "recommendations", "narrative"
        ]
    }

    raw = _chat(system, user, max_tokens=20000, response_schema=schema)
    return _normalize_timeline_dates(json.loads(raw))


# ── 2. Owner assignment ──────────────────────────────────────────────────────
def ai_assign_owner(task: dict, team: list, all_tasks: list) -> dict:
    # Build workload per person
    workload = {}
    for m in team:
        assigned = [t for t in all_tasks if t.get("assignee") == m["id"] and t["status"] != "Done"]
        workload[m["id"]] = sum(t["points"] for t in assigned)

    system = (
        "You are an expert engineering manager. "
        "Recommend the best owner for a task based on skills, capacity, and velocity."
    )
    user = f"""
Task to assign:
{json.dumps(task, indent=2)}

Team members (with skills 0-100, capacity %, velocity multiplier, and current workload in story points):
"""
    for m in team:
        user += f"\n- {m['name']} ({m['role']}): skills={m['skills']}, capacity={m['capacity_pct']}%, velocity={m['velocity_multiplier']}x, current_workload_pts={workload.get(m['id'],0)}"

    schema = {
        "type": "OBJECT",
        "properties": {
            "top_pick": {
                "type": "OBJECT",
                "properties": {
                    "id": {"type": "STRING"},
                    "name": {"type": "STRING"},
                    "score": {"type": "INTEGER"},
                    "rationale": {"type": "STRING"}
                },
                "required": ["id", "name", "score", "rationale"]
            },
            "alternatives": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "id": {"type": "STRING"},
                        "name": {"type": "STRING"},
                        "score": {"type": "INTEGER"},
                        "rationale": {"type": "STRING"}
                    },
                    "required": ["id", "name", "score", "rationale"]
                }
            },
            "risk_note": {"type": "STRING", "nullable": True}
        },
        "required": ["top_pick", "alternatives", "risk_note"]
    }

    raw = _chat(system, user, max_tokens=20000, response_schema=schema)
    return json.loads(raw)


# ── 3. Scenario simulation ───────────────────────────────────────────────────
def ai_simulate_scenario(scenario_name: str, scenario_params: dict,
                         baseline_stats: dict, baseline_prediction: dict) -> dict:
    system = (
        "You are a senior delivery strategist. "
        "Compare a proposed project scenario against a baseline forecast."
    )
    user = f"""
Scenario name: {scenario_name}
Scenario parameters: {json.dumps(scenario_params, indent=2)}

Baseline project stats: {json.dumps(baseline_stats, indent=2)}
Baseline AI prediction: {json.dumps(baseline_prediction, indent=2)}

Simulate how the scenario changes the delivery outcome.
"""
    
    schema = {
        "type": "OBJECT",
        "properties": {
            "new_predicted_date": {"type": "STRING"},
            "date_delta_days": {"type": "INTEGER"},
            "new_risk_level": {"type": "STRING", "enum": ["low", "medium", "high"]},
            "cost_impact": {"type": "STRING", "enum": ["none", "low", "medium", "high"]},
            "team_impact": {"type": "STRING", "enum": ["positive", "neutral", "negative"]},
            "confidence": {"type": "INTEGER"},
            "tradeoffs": {"type": "ARRAY", "items": {"type": "STRING"}},
            "recommendation": {"type": "STRING", "enum": ["adopt", "consider", "avoid"]},
            "narrative": {"type": "STRING"}
        },
        "required": [
            "new_predicted_date", "date_delta_days", "new_risk_level", "cost_impact", 
            "team_impact", "confidence", "tradeoffs", "recommendation", "narrative"
        ]
    }

    raw = _chat(system, user, max_tokens=20000, response_schema=schema)
    return json.loads(raw)


# ── 4. General chat assistant ────────────────────────────────────────────────
def ai_chat_assistant(question: str, project_context: dict) -> str:
    system = (
        "You are an AI Project Orchestrator assistant. "
        "Answer questions about the project concisely and helpfully. "
        "Use the project context provided."
    )
    user = f"Project context:\n{json.dumps(project_context, indent=2)}\n\nQuestion: {question}"
    
    # Plain text format, no schema required here
    return _chat(system, user, max_tokens=20000)