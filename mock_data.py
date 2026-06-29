import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ── Team members ────────────────────────────────────────────────────────────
TEAM_MEMBERS = [
    {
        "id": "U001", "name": "Sarah Chen",       "role": "Senior Frontend Engineer",
        "skills": {"React": 95, "TypeScript": 90, "CSS": 85, "Node.js": 60, "Python": 30, "AWS": 40},
        "capacity_pct": 70, "velocity_multiplier": 1.2,
        "avatar": "SC", "timezone": "PST"
    },
    {
        "id": "U002", "name": "Marcus Johnson",   "role": "Backend Engineer",
        "skills": {"Python": 92, "Django": 88, "PostgreSQL": 85, "AWS": 80, "React": 20, "TypeScript": 30},
        "capacity_pct": 85, "velocity_multiplier": 1.0,
        "avatar": "MJ", "timezone": "EST"
    },
    {
        "id": "U003", "name": "Priya Patel",      "role": "Full-Stack Engineer",
        "skills": {"React": 80, "Python": 78, "Node.js": 82, "TypeScript": 75, "AWS": 65, "PostgreSQL": 70},
        "capacity_pct": 100, "velocity_multiplier": 0.95,
        "avatar": "PP", "timezone": "IST"
    },
    {
        "id": "U004", "name": "David Kim",        "role": "DevOps / Cloud Engineer",
        "skills": {"AWS": 95, "Kubernetes": 90, "Terraform": 88, "Python": 70, "Docker": 92, "PostgreSQL": 55},
        "capacity_pct": 60, "velocity_multiplier": 1.1,
        "avatar": "DK", "timezone": "PST"
    },
    {
        "id": "U005", "name": "Aisha Okonkwo",   "role": "Senior Backend Engineer",
        "skills": {"Python": 90, "PostgreSQL": 88, "AWS": 72, "Django": 85, "Node.js": 65, "React": 25},
        "capacity_pct": 90, "velocity_multiplier": 1.15,
        "avatar": "AO", "timezone": "GMT"
    },
]

# ── Sprint velocity history (last 8 sprints) ────────────────────────────────
SPRINT_HISTORY = [
    {"sprint": "S-01", "planned_pts": 42, "completed_pts": 38, "team_size": 5},
    {"sprint": "S-02", "planned_pts": 45, "completed_pts": 44, "team_size": 5},
    {"sprint": "S-03", "planned_pts": 48, "completed_pts": 40, "team_size": 4},  # 1 OOO
    {"sprint": "S-04", "planned_pts": 46, "completed_pts": 46, "team_size": 5},
    {"sprint": "S-05", "planned_pts": 50, "completed_pts": 47, "team_size": 5},
    {"sprint": "S-06", "planned_pts": 52, "completed_pts": 48, "team_size": 5},
    {"sprint": "S-07", "planned_pts": 50, "completed_pts": 43, "team_size": 5},  # incidents
    {"sprint": "S-08", "planned_pts": 48, "completed_pts": 45, "team_size": 5},
]

# ── Active project: "Customer Portal v2" ───────────────────────────────────
EPICS = [
    {"id": "E-01", "name": "Authentication & SSO",         "color": "#7C3AED"},
    {"id": "E-02", "name": "Dashboard & Analytics",        "color": "#0891B2"},
    {"id": "E-03", "name": "Billing & Subscriptions",      "color": "#D97706"},
    {"id": "E-04", "name": "API Gateway & Rate Limiting",  "color": "#059669"},
    {"id": "E-05", "name": "Notifications Engine",         "color": "#DC2626"},
]

TASKS = [
    # E-01 Auth
    {"id":"T-001","epic":"E-01","title":"OAuth 2.0 integration (Google/GitHub)","status":"Done",       "points":8, "assignee":"U001","skills_needed":["React","TypeScript"],"blocked_by":[]},
    {"id":"T-002","epic":"E-01","title":"JWT refresh token logic",               "status":"Done",       "points":5, "assignee":"U002","skills_needed":["Python","Django"],"blocked_by":[]},
    {"id":"T-003","epic":"E-01","title":"MFA / TOTP setup flow",                 "status":"In Progress","points":8, "assignee":"U001","skills_needed":["React","TypeScript","Node.js"],"blocked_by":["T-002"]},
    {"id":"T-004","epic":"E-01","title":"Role-based access control (RBAC)",      "status":"In Progress","points":13,"assignee":"U002","skills_needed":["Python","PostgreSQL"],"blocked_by":["T-002"]},
    {"id":"T-005","epic":"E-01","title":"SSO admin panel",                       "status":"To Do",      "points":5, "assignee":None, "skills_needed":["React","Python"],"blocked_by":["T-003","T-004"]},
    # E-02 Dashboard
    {"id":"T-006","epic":"E-02","title":"Analytics data model & migrations",     "status":"Done",       "points":8, "assignee":"U005","skills_needed":["PostgreSQL","Python"],"blocked_by":[]},
    {"id":"T-007","epic":"E-02","title":"Real-time metrics WebSocket feed",      "status":"In Progress","points":13,"assignee":"U003","skills_needed":["Node.js","Python"],"blocked_by":["T-006"]},
    {"id":"T-008","epic":"E-02","title":"Chart components (Recharts)",           "status":"In Progress","points":8, "assignee":"U001","skills_needed":["React","TypeScript"],"blocked_by":[]},
    {"id":"T-009","epic":"E-02","title":"Dashboard layout & filters UI",         "status":"To Do",      "points":8, "assignee":None, "skills_needed":["React","CSS"],"blocked_by":["T-007","T-008"]},
    {"id":"T-010","epic":"E-02","title":"Export to CSV/PDF",                     "status":"To Do",      "points":5, "assignee":None, "skills_needed":["Python","React"],"blocked_by":["T-009"]},
    # E-03 Billing
    {"id":"T-011","epic":"E-03","title":"Stripe webhook integration",            "status":"In Progress","points":8, "assignee":"U002","skills_needed":["Python","Django"],"blocked_by":[]},
    {"id":"T-012","epic":"E-03","title":"Subscription plan UI",                  "status":"To Do",      "points":8, "assignee":None, "skills_needed":["React","TypeScript"],"blocked_by":["T-011"]},
    {"id":"T-013","epic":"E-03","title":"Invoice generation & email",            "status":"To Do",      "points":5, "assignee":None, "skills_needed":["Python","Django"],"blocked_by":["T-011"]},
    {"id":"T-014","epic":"E-03","title":"Usage metering & alerts",               "status":"To Do",      "points":8, "assignee":None, "skills_needed":["Python","PostgreSQL","AWS"],"blocked_by":["T-013"]},
    # E-04 API Gateway
    {"id":"T-015","epic":"E-04","title":"API key management service",            "status":"To Do",      "points":13,"assignee":None, "skills_needed":["Python","PostgreSQL","AWS"],"blocked_by":[]},
    {"id":"T-016","epic":"E-04","title":"Rate limiting middleware",               "status":"To Do",      "points":8, "assignee":None, "skills_needed":["Python","AWS","Docker"],"blocked_by":["T-015"]},
    {"id":"T-017","epic":"E-04","title":"API docs portal (Swagger/OpenAPI)",     "status":"To Do",      "points":5, "assignee":None, "skills_needed":["Python","React"],"blocked_by":["T-016"]},
    # E-05 Notifications
    {"id":"T-018","epic":"E-05","title":"Notification preferences data model",   "status":"To Do",      "points":5, "assignee":None, "skills_needed":["Python","PostgreSQL"],"blocked_by":[]},
    {"id":"T-019","epic":"E-05","title":"Email delivery service (SES)",          "status":"To Do",      "points":8, "assignee":None, "skills_needed":["Python","AWS"],"blocked_by":["T-018"]},
    {"id":"T-020","epic":"E-05","title":"In-app notification centre UI",         "status":"To Do",      "points":8, "assignee":None, "skills_needed":["React","TypeScript","Node.js"],"blocked_by":["T-019"]},
]

def get_tasks_df():
    df = pd.DataFrame(TASKS)
    df["points"] = df["points"].astype(int)
    return df

def get_sprint_df():
    df = pd.DataFrame(SPRINT_HISTORY)
    df["velocity"] = df["completed_pts"] / df["team_size"]
    df["completion_rate"] = df["completed_pts"] / df["planned_pts"]
    return df

def get_team_df():
    return pd.DataFrame(TEAM_MEMBERS)

def get_epic_map():
    return {e["id"]: e for e in EPICS}

def compute_project_stats():
    df = get_tasks_df()
    total_pts   = df["points"].sum()
    done_pts    = df[df["status"] == "Done"]["points"].sum()
    wip_pts     = df[df["status"] == "In Progress"]["points"].sum()
    todo_pts    = df[df["status"] == "To Do"]["points"].sum()
    unassigned  = df[(df["status"] == "To Do") & (df["assignee"].isna())]["id"].count()
    return {
        "total_pts": int(total_pts),
        "done_pts":  int(done_pts),
        "wip_pts":   int(wip_pts),
        "todo_pts":  int(todo_pts),
        "pct_complete": round(done_pts / total_pts * 100, 1),
        "unassigned_tasks": int(unassigned),
        "remaining_pts": int(wip_pts + todo_pts),
    }

# Sprint start date
PROJECT_START = datetime(2026, 5, 17)
SPRINT_LENGTH_DAYS = 14
CURRENT_DATE = datetime(2026, 6, 29)
TARGET_DATE  = datetime(2026, 8, 17)