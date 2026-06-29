import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json

from mock_data import (
    get_tasks_df, get_sprint_df, get_team_df, get_epic_map,
    compute_project_stats, TEAM_MEMBERS, EPICS, TARGET_DATE, CURRENT_DATE
)
from ai_engine import (
    ai_predict_timeline, ai_assign_owner,
    ai_simulate_scenario, ai_chat_assistant
)

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Foresight PMO",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Theme / CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stSidebar"] { background: #0f0f1a; }
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
.metric-card {
    background: #1e1e2e; border: 1px solid #2d2d44;
    border-radius: 12px; padding: 16px 20px; margin-bottom: 8px;
}
.metric-value { font-size: 28px; font-weight: 700; color: #a78bfa; }
.metric-label { font-size: 12px; color: #94a3b8; text-transform: uppercase; letter-spacing: .05em; }
.risk-high   { background:#3f1212; border-left:4px solid #ef4444; padding:10px 14px; border-radius:6px; }
.risk-medium { background:#3f2d12; border-left:4px solid #f59e0b; padding:10px 14px; border-radius:6px; }
.risk-low    { background:#12312a; border-left:4px solid #10b981; padding:10px 14px; border-radius:6px; }
.rec-item    { background:#1e2535; border-radius:8px; padding:10px 14px; margin:6px 0; font-size:14px; }
.tag { display:inline-block; background:#312e81; color:#a5b4fc; font-size:11px;
       padding:2px 8px; border-radius:9999px; margin:2px; }
.ai-badge { background:linear-gradient(135deg,#7c3aed,#2563eb);
            color:white; font-size:10px; padding:2px 8px;
            border-radius:9999px; font-weight:600; letter-spacing:.05em; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar navigation ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎯 Foresight PMO")
    st.markdown("**Customer Portal v2**")
    st.markdown("---")
    page = st.radio(
        "Navigate",
        ["📊 Project Overview",
         "🔮 Timeline Prediction",
         "👤 Owner Assignment",
         "🔀 Scenario Simulation",
         "💬 Ask the AI"],
        label_visibility="collapsed"
    )
    st.markdown("---")
    stats = compute_project_stats()
    st.markdown(f"**Progress:** {stats['pct_complete']}% complete")
    st.progress(stats["pct_complete"] / 100)
    st.markdown(f"🗓 Target: **{TARGET_DATE.strftime('%b %d, %Y')}**")
    st.markdown(f"⚠️ Unassigned: **{stats['unassigned_tasks']} tasks**")

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — Project Overview
# ═══════════════════════════════════════════════════════════════════════════════
if page == "📊 Project Overview":
    st.title("📊 Project Overview")
    st.caption(f"Customer Portal v2 · Live as of {CURRENT_DATE.strftime('%b %d, %Y')}")

    stats = compute_project_stats()
    df    = get_tasks_df()
    epic_map = get_epic_map()

    # KPI row
    c1, c2, c3, c4, c5 = st.columns(5)
    for col, label, value, suffix in [
        (c1, "Total Points",    stats["total_pts"],       " pts"),
        (c2, "Completed",       stats["done_pts"],        " pts"),
        (c3, "In Progress",     stats["wip_pts"],         " pts"),
        (c4, "Remaining",       stats["remaining_pts"],   " pts"),
        (c5, "Unassigned",      stats["unassigned_tasks"]," tasks"),
    ]:
        with col:
            st.metric(label, f"{value}{suffix}")

    st.markdown("---")
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.subheader("Task Board")
        status_order = ["To Do", "In Progress", "Done"]
        for status in status_order:
            subset = df[df["status"] == status]
            color  = {"To Do":"#64748b","In Progress":"#f59e0b","Done":"#10b981"}[status]
            st.markdown(f"**{status}** &nbsp; <span style='color:{color};font-size:12px'>({len(subset)} tasks · {subset['points'].sum()} pts)</span>", unsafe_allow_html=True)
            for _, row in subset.iterrows():
                epic  = epic_map.get(row["epic"], {})
                ecolor = epic.get("color","#6b7280")
                ename  = epic.get("name","")
                assignee = next((m["name"] for m in TEAM_MEMBERS if m["id"] == row["assignee"]), "Unassigned")
                skills_html = "".join(f'<span class="tag">{s}</span>' for s in row["skills_needed"])
                st.markdown(f"""
                <div style="background:#1a1a2e;border-left:3px solid {ecolor};border-radius:8px;
                     padding:10px 14px;margin:4px 0">
                  <div style="font-size:13px;font-weight:600">{row['id']} · {row['title']}</div>
                  <div style="font-size:11px;color:#94a3b8;margin-top:4px">
                    👤 {assignee} &nbsp;|&nbsp; {row['points']} pts &nbsp;|&nbsp;
                    <span style="color:{ecolor}">{ename}</span>
                  </div>
                  <div style="margin-top:6px">{skills_html}</div>
                </div>""", unsafe_allow_html=True)

    with col_right:
        # Progress donut
        fig = go.Figure(go.Pie(
            values=[stats["done_pts"], stats["wip_pts"], stats["todo_pts"]],
            labels=["Done","In Progress","To Do"],
            hole=0.62,
            marker_colors=["#10b981","#f59e0b","#334155"],
            textinfo="none",
        ))
        fig.add_annotation(text=f"{stats['pct_complete']}%", font_size=28,
                           font_color="#a78bfa", showarrow=False)
        fig.update_layout(height=250, margin=dict(t=10,b=10,l=10,r=10),
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          legend=dict(font_color="#94a3b8"),
                          showlegend=True)
        st.plotly_chart(fig, width="stretch")

        # Epic breakdown
        st.subheader("By Epic")
        for epic in EPICS:
            subset = df[df["epic"] == epic["id"]]
            done = subset[subset["status"]=="Done"]["points"].sum()
            total = subset["points"].sum()
            pct = done/total if total else 0
            st.markdown(f"""
            <div style="margin:6px 0">
              <div style="display:flex;justify-content:space-between;font-size:12px">
                <span style="color:{epic['color']}">{epic['name']}</span>
                <span style="color:#94a3b8">{int(done)}/{int(total)} pts</span>
              </div>
              <div style="background:#1e2535;border-radius:4px;height:6px;margin-top:4px">
                <div style="background:{epic['color']};width:{pct*100:.0f}%;height:6px;border-radius:4px"></div>
              </div>
            </div>""", unsafe_allow_html=True)

        # Sprint velocity chart
        st.subheader("Sprint Velocity")
        sdf = get_sprint_df()
        fig2 = go.Figure()
        fig2.add_bar(x=sdf["sprint"], y=sdf["planned_pts"],
                     name="Planned", marker_color="#334155")
        fig2.add_bar(x=sdf["sprint"], y=sdf["completed_pts"],
                     name="Completed", marker_color="#7c3aed")
        fig2.update_layout(barmode="group", height=180,
                           margin=dict(t=10,b=10,l=0,r=0),
                           paper_bgcolor="rgba(0,0,0,0)",
                           plot_bgcolor="rgba(0,0,0,0)",
                           legend=dict(font_color="#94a3b8"),
                           yaxis=dict(color="#94a3b8"),
                           xaxis=dict(color="#94a3b8"))
        st.plotly_chart(fig2, width="stretch")

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — Timeline Prediction
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🔮 Timeline Prediction":
    st.title("🔮 Timeline Prediction")
    st.caption("Velocity-based probabilistic delivery forecast powered by Gemini")

    stats       = compute_project_stats()
    sprint_data = get_sprint_df().to_dict(orient="records")

    with st.expander("⚙️ Forecast parameters", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            extra_risk = st.slider("Add risk buffer (%)", 0, 30, 0)
            team_change = st.selectbox("Team change", ["No change", "+1 engineer", "-1 engineer"])
        with col2:
            scope_change = st.slider("Scope change (story points)", -30, 30, 0)
            holiday_days = st.number_input("Upcoming holidays / OOO days", 0, 20, 3)

    overrides = {
        "extra_risk_buffer_pct": extra_risk,
        "team_change": team_change,
        "scope_change_pts": scope_change,
        "holiday_days": holiday_days,
    }

    if st.button("🤖 Run Forecast", type="primary", width="stretch"):
        with st.spinner("Gemini is analysing velocity trends and forecasting delivery…"):
            result = ai_predict_timeline(stats, sprint_data, overrides)
            st.session_state["timeline_result"] = result

    result = st.session_state.get("timeline_result")
    if result:
        risk_css = {"low":"risk-low","medium":"risk-medium","high":"risk-high"}.get(result["risk_level"],"risk-medium")
        trend_icon = {"improving":"📈","stable":"➡️","declining":"📉"}.get(result["trend"],"➡️")
        on_track_icon = "✅" if result["on_track"] else "❌"

        # Headline metrics
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Predicted Date",    result["predicted_date"])
        c2.metric("P50 Date",          result["confidence_p50"])
        c3.metric("P95 Date",          result["confidence_p95"])
        c4.metric("Sprints Remaining", result["sprints_remaining"])

        st.markdown("---")
        col_l, col_r = st.columns([2,3])

        with col_l:
            st.markdown(f"### {on_track_icon} On Track" if result["on_track"] else f"### {on_track_icon} At Risk")
            st.markdown(f"""
            <div class="{risk_css}" style="margin-bottom:12px">
              <strong>Risk Level:</strong> {result['risk_level'].upper()} &nbsp;|&nbsp;
              <strong>Trend:</strong> {trend_icon} {result['trend'].capitalize()}<br>
              <strong>Avg Velocity:</strong> {result['avg_velocity']} pts/sprint
            </div>""", unsafe_allow_html=True)

            st.markdown("#### 🚨 Key Risks")
            for r in result["key_risks"]:
                st.markdown(f'<div class="risk-{result["risk_level"]}" style="margin:4px 0;font-size:13px">⚠️ {r}</div>', unsafe_allow_html=True)

            st.markdown("#### 💡 Recommendations")
            for rec in result["recommendations"]:
                st.markdown(f'<div class="rec-item">→ {rec}</div>', unsafe_allow_html=True)

        with col_r:
            st.markdown("#### 📅 Delivery Probability Timeline")

            # Monte Carlo simulation visualisation
            sdf = get_sprint_df()
            avg_v = sdf["completed_pts"].mean()
            std_v = sdf["completed_pts"].std()
            remaining = stats["remaining_pts"]
            simulations = 1000
            end_dates = []
            for _ in range(simulations):
                pts = 0
                sprints = 0
                while pts < remaining:
                    pts += max(1, np.random.normal(avg_v, std_v))
                    sprints += 1
                end_dates.append((CURRENT_DATE + timedelta(days=sprints * 14)).strftime("%Y-%m-%d"))

            end_dt = pd.to_datetime(end_dates)
            fig = go.Figure()
            fig.add_histogram(x=end_dt, nbinsx=30,
                              marker_color="#7c3aed", opacity=0.8,
                              name="Simulated outcomes")
            target_str = TARGET_DATE.strftime("%Y-%m-%d")
            fig.add_vline(x=target_str, line_color="#ef4444", line_dash="dash",
                          annotation_text="Target", annotation_font_color="#ef4444")
            fig.add_vline(x=result["predicted_date"], line_color="#10b981", line_dash="dot",
                          annotation_text="AI Prediction", annotation_font_color="#10b981")
            fig.update_layout(height=300,
                              paper_bgcolor="rgba(0,0,0,0)",
                              plot_bgcolor="rgba(0,0,0,0)",
                              margin=dict(t=20,b=30,l=0,r=0),
                              xaxis=dict(color="#94a3b8"),
                              yaxis=dict(color="#94a3b8", title="Simulations"),
                              legend=dict(font_color="#94a3b8"))
            st.plotly_chart(fig, width="stretch")

            st.info(f"**AI Analysis:** {result['narrative']}")

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — Owner Assignment
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "👤 Owner Assignment":
    st.title("👤 Owner Assignment")
    st.caption("Skill-map + capacity + velocity matching powered by Gemini")

    df       = get_tasks_df()
    team     = TEAM_MEMBERS
    epic_map = get_epic_map()

    unassigned = df[(df["status"] == "To Do") & (df["assignee"].isna())]
    all_tasks  = df.to_dict(orient="records")

    col_l, col_r = st.columns([3, 2])

    with col_l:
        st.subheader(f"Unassigned Tasks ({len(unassigned)})")
        task_options = {
            f"{r['id']} · {r['title']}": r.to_dict()
            for _, r in unassigned.iterrows()
        }
        selected_label = st.selectbox("Select a task to assign", list(task_options.keys()))
        selected_task  = task_options[selected_label]

        if selected_task:
            epic   = epic_map.get(selected_task["epic"], {})
            ecolor = epic.get("color","#6b7280")
            skills = selected_task.get("skills_needed",[])
            blocked = selected_task.get("blocked_by",[])
            st.markdown(f"""
            <div style="background:#1a1a2e;border-left:4px solid {ecolor};
                 border-radius:10px;padding:16px 20px;margin:12px 0">
              <div style="font-size:16px;font-weight:700">{selected_task['title']}</div>
              <div style="color:{ecolor};font-size:12px;margin:4px 0">{epic.get('name','')}</div>
              <div style="margin-top:8px">
                {''.join(f'<span class="tag">{s}</span>' for s in skills)}
              </div>
              <div style="color:#94a3b8;font-size:12px;margin-top:8px">
                📦 {selected_task['points']} story points
                {f'&nbsp;|&nbsp; 🔒 Blocked by: {", ".join(blocked)}' if blocked else ''}
              </div>
            </div>""", unsafe_allow_html=True)

        if st.button("🤖 Get AI Assignment Recommendation", type="primary", width="stretch"):
            with st.spinner("Gemini is analysing skills, capacity, and velocity…"):
                result = ai_assign_owner(selected_task, team, all_tasks)
                st.session_state["assignment_result"] = (selected_task["id"], result)

    with col_r:
        st.subheader("Team Capacity")
        for m in team:
            assigned_pts = sum(t["points"] for t in all_tasks
                               if t.get("assignee")==m["id"] and t["status"]!="Done")
            cap  = m["capacity_pct"]
            load = min(100, assigned_pts * 5)  # normalised load indicator
            color = "#ef4444" if load > 80 else "#f59e0b" if load > 50 else "#10b981"
            st.markdown(f"""
            <div style="background:#1a1a2e;border-radius:10px;padding:12px 16px;margin:6px 0">
              <div style="display:flex;justify-content:space-between;align-items:center">
                <div>
                  <div style="font-weight:600;font-size:13px">{m['name']}</div>
                  <div style="color:#94a3b8;font-size:11px">{m['role']}</div>
                </div>
                <div style="text-align:right">
                  <div style="color:{color};font-size:12px;font-weight:600">
                    {assigned_pts} pts active
                  </div>
                  <div style="color:#64748b;font-size:11px">{cap}% capacity</div>
                </div>
              </div>
              <div style="background:#2d2d44;border-radius:4px;height:4px;margin-top:8px">
                <div style="background:{color};width:{load}%;height:4px;border-radius:4px"></div>
              </div>
            </div>""", unsafe_allow_html=True)

    # Result panel
    if "assignment_result" in st.session_state:
        task_id, result = st.session_state["assignment_result"]
        if task_id == selected_task["id"]:
            st.markdown("---")
            st.markdown('<span class="ai-badge">AI RECOMMENDATION</span>', unsafe_allow_html=True)
            st.markdown(" ")

            top = result["top_pick"]
            member = next((m for m in team if m["id"] == top["id"]), {})

            col1, col2, col3 = st.columns([2,2,1])
            with col1:
                st.markdown(f"""
                <div style="background:#1e1e2e;border:2px solid #7c3aed;border-radius:12px;padding:20px">
                  <div style="font-size:11px;color:#a78bfa;font-weight:600;letter-spacing:.08em">TOP PICK</div>
                  <div style="font-size:20px;font-weight:700;margin:6px 0">{top['name']}</div>
                  <div style="color:#94a3b8;font-size:12px">{member.get('role','')}</div>
                  <div style="background:#312e81;border-radius:6px;padding:6px 10px;margin-top:12px;font-size:13px">
                    Match score: <strong style="color:#a78bfa">{top['score']}/100</strong>
                  </div>
                  <div style="color:#cbd5e1;font-size:13px;margin-top:10px;line-height:1.5">
                    {top['rationale']}
                  </div>
                </div>""", unsafe_allow_html=True)
            with col2:
                st.markdown("**Alternatives**")
                for alt in result.get("alternatives",[]):
                    alt_member = next((m for m in team if m["id"] == alt["id"]), {})
                    st.markdown(f"""
                    <div style="background:#1a1a2e;border-radius:10px;padding:12px 16px;margin:6px 0">
                      <div style="font-weight:600">{alt['name']}
                        <span style="float:right;color:#a78bfa">{alt['score']}/100</span>
                      </div>
                      <div style="color:#94a3b8;font-size:11px">{alt_member.get('role','')}</div>
                      <div style="color:#94a3b8;font-size:12px;margin-top:4px">{alt['rationale']}</div>
                    </div>""", unsafe_allow_html=True)
            with col3:
                if result.get("risk_note"):
                    st.markdown(f"""
                    <div class="risk-medium">
                      <div style="font-size:11px;font-weight:700;margin-bottom:4px">⚠️ NOTE</div>
                      <div style="font-size:12px">{result['risk_note']}</div>
                    </div>""", unsafe_allow_html=True)

            # Skill radar
            if member.get("skills"):
                skills_needed = selected_task.get("skills_needed", [])
                all_skills = list(member["skills"].keys())
                values = [member["skills"][s] for s in all_skills]
                colors = ["#a78bfa" if s in skills_needed else "#4b5563" for s in all_skills]
                fig = go.Figure(go.Scatterpolar(
                    r=values + [values[0]],
                    theta=all_skills + [all_skills[0]],
                    fill="toself",
                    fillcolor="rgba(124,58,237,0.15)",
                    line_color="#7c3aed",
                ))
                fig.update_layout(
                    polar=dict(
                        radialaxis=dict(visible=True, range=[0,100], color="#475569"),
                        angularaxis=dict(color="#94a3b8"),
                        bgcolor="rgba(0,0,0,0)",
                    ),
                    paper_bgcolor="rgba(0,0,0,0)",
                    height=240,
                    margin=dict(t=10,b=10,l=20,r=20),
                    title=dict(text=f"{top['name']}'s skills", font_color="#94a3b8", font_size=12)
                )
                st.plotly_chart(fig, width="stretch")

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — Scenario Simulation
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🔀 Scenario Simulation":
    st.title("🔀 Scenario Simulation")
    st.caption("What-if delivery modeling powered by Gemini")

    stats = compute_project_stats()
    sprint_data = get_sprint_df().to_dict(orient="records")

    # Get or generate baseline
    if "timeline_result" not in st.session_state:
        with st.spinner("Generating baseline forecast…"):
            baseline = ai_predict_timeline(stats, sprint_data)
            st.session_state["timeline_result"] = baseline
    baseline = st.session_state["timeline_result"]

    st.info(f"**Baseline forecast:** {baseline['predicted_date']} · Risk: {baseline['risk_level'].upper()} · {baseline['narrative']}")

    st.markdown("---")
    st.subheader("Build & compare scenarios")

    PRESET_SCENARIOS = {
        "➕ Add 1 contractor (4 weeks)": {
            "action": "hire_contractor",
            "duration_weeks": 4,
            "skill": "Full-stack",
            "cost": "~$8,000",
        },
        "✂️ Descope notifications engine": {
            "action": "descope_epic",
            "epic": "E-05 — Notifications Engine",
            "points_removed": 21,
            "deferred_to": "v2.1",
        },
        "🔄 Parallelize billing + API epics": {
            "action": "parallelize",
            "epics": ["E-03 Billing","E-04 API Gateway"],
            "requires": "team_split",
        },
        "📅 Extend deadline by 3 weeks": {
            "action": "extend_deadline",
            "new_target": (TARGET_DATE + timedelta(weeks=3)).strftime("%Y-%m-%d"),
            "impact": "low_urgency_risk",
        },
        "🚀 Add 5 hrs/week focus time (no meetings)": {
            "action": "focus_time",
            "hours_per_person_per_week": 5,
            "duration_weeks": 6,
        },
    }

    col1, col2 = st.columns([1,2])
    with col1:
        st.markdown("**Preset scenarios**")
        selected_scenarios = []
        for label, params in PRESET_SCENARIOS.items():
            if st.checkbox(label, key=f"sc_{label}"):
                selected_scenarios.append((label, params))

        st.markdown("**Custom scenario**")
        custom_name = st.text_input("Name", placeholder="e.g. Outsource API gateway")
        custom_desc = st.text_area("Describe the change", height=80,
                                   placeholder="e.g. Hire an external vendor to build the API gateway epic, delivering in 3 weeks")
        if custom_name and custom_desc:
            selected_scenarios.append((custom_name, {"description": custom_desc}))

        run_btn = st.button("🤖 Simulate selected scenarios", type="primary",
                            width="stretch",
                            disabled=len(selected_scenarios)==0)

    with col2:
        if run_btn and selected_scenarios:
            results = []
            prog = st.progress(0)
            for i, (name, params) in enumerate(selected_scenarios):
                with st.spinner(f"Simulating: {name}…"):
                    r = ai_simulate_scenario(name, params, stats, baseline)
                    results.append({"scenario": name, **r})
                prog.progress((i+1)/len(selected_scenarios))
            st.session_state["scenario_results"] = results

        if "scenario_results" in st.session_state:
            results = st.session_state["scenario_results"]

            rec_color = {"adopt":"#10b981","consider":"#f59e0b","avoid":"#ef4444"}
            rec_icon  = {"adopt":"✅","consider":"⚠️","avoid":"❌"}

            for r in results:
                delta = r["date_delta_days"]
                delta_str = f"{'−' if delta<0 else '+'}{abs(delta)} days"
                delta_color = "#10b981" if delta <= 0 else "#ef4444"
                rec = r["recommendation"]

                st.markdown(f"""
                <div style="background:#1a1a2e;border-radius:12px;padding:18px 22px;margin:10px 0;
                     border-left:4px solid {rec_color.get(rec,'#6b7280')}">
                  <div style="display:flex;justify-content:space-between;align-items:flex-start">
                    <div>
                      <div style="font-size:15px;font-weight:700">{r['scenario']}</div>
                      <div style="color:#94a3b8;font-size:12px;margin-top:4px">{r['narrative']}</div>
                    </div>
                    <div style="text-align:right;min-width:120px">
                      <div style="color:{delta_color};font-size:18px;font-weight:700">{delta_str}</div>
                      <div style="color:#94a3b8;font-size:11px">{r['new_predicted_date']}</div>
                      <div style="margin-top:4px;font-size:13px">{rec_icon.get(rec,'')} {rec.capitalize()}</div>
                    </div>
                  </div>
                  <div style="display:flex;gap:16px;margin-top:12px;font-size:12px">
                    <span>🎯 Risk: <strong>{r['new_risk_level'].upper()}</strong></span>
                    <span>💰 Cost: <strong>{r['cost_impact']}</strong></span>
                    <span>👥 Team: <strong>{r['team_impact']}</strong></span>
                    <span>📊 Confidence: <strong>{r['confidence']}%</strong></span>
                  </div>
                  <div style="margin-top:10px">
                    <div style="font-size:11px;color:#64748b;margin-bottom:4px">TRADEOFFS</div>
                    {''.join(f'<div style="font-size:12px;color:#94a3b8;margin:2px 0">• {t}</div>' for t in r.get('tradeoffs',[]))}
                  </div>
                </div>""", unsafe_allow_html=True)

            # Comparison chart
            if len(results) > 1:
                st.markdown("#### Scenario comparison")
                fig = go.Figure()
                labels = ["Baseline"] + [r["scenario"][:30] for r in results]
                dates  = [baseline["predicted_date"]] + [r["new_predicted_date"] for r in results]
                colors = ["#475569"] + [
                    rec_color.get(r["recommendation"],"#6b7280") for r in results
                ]
                fig.add_bar(x=labels, y=pd.to_datetime(dates).astype(np.int64)//10**9,
                            marker_color=colors, text=dates, textposition="outside")
                fig.update_layout(
                    height=300, yaxis=dict(visible=False),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(t=30,b=10,l=0,r=0),
                    xaxis=dict(color="#94a3b8"),
                )
                st.plotly_chart(fig, width="stretch")

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 5 — Ask the AI
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "💬 Ask the AI":
    st.title("💬 Ask the AI")
    st.caption("Chat with your Project Orchestrator about anything")

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    project_context = {
        **compute_project_stats(),
        "timeline": st.session_state.get("timeline_result", {}),
        "team": [{"name":m["name"],"role":m["role"],"capacity":m["capacity_pct"]} for m in TEAM_MEMBERS],
        "epics": [e["name"] for e in EPICS],
    }

    # Quick prompts
    st.markdown("**Quick questions**")
    qcols = st.columns(3)
    quick_prompts = [
        "What are the biggest delivery risks?",
        "Which team members are overloaded?",
        "What should the PM focus on this week?",
        "Which epic is most at risk?",
        "How can we improve team velocity?",
        "What's the critical path to delivery?",
    ]
    for i, qp in enumerate(quick_prompts):
        with qcols[i % 3]:
            if st.button(qp, key=f"qp_{i}", width="stretch"):
                st.session_state["pending_question"] = qp

    st.markdown("---")

    # Chat history
    for msg in st.session_state["chat_history"]:
        role = msg["role"]
        with st.chat_message(role):
            st.markdown(msg["content"])

    # Input
    question = st.chat_input("Ask anything about the project…")
    if not question and "pending_question" in st.session_state:
        question = st.session_state.pop("pending_question")

    if question:
        st.session_state["chat_history"].append({"role":"user","content":question})
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                answer = ai_chat_assistant(question, project_context)
            st.markdown(answer)
        st.session_state["chat_history"].append({"role":"assistant","content":answer})
        st.rerun()