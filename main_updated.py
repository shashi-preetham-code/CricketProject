import streamlit as st
import pandas as pd

st.set_page_config(page_title="Cricket Live Pro Scorer", layout="wide", page_icon="🏏")

# --- HELPER FUNCTIONS ---
def format_overs(total_balls):
    """Converts 9 balls into 1.3 formatting"""
    return f"{total_balls // 6}.{total_balls % 6}"

def calculate_economy(runs, balls):
    """Calculates runs per over"""
    if balls == 0:
        return 0.00
    overs = balls / 6
    return round(runs / overs, 2)

# --- INITIALIZING SESSION STATE ---
if 'match' not in st.session_state:
    st.session_state.match = {
        "score": 0, "wickets": 0, "balls": 0,
        "batting_stats": {}, "bowling_stats": {},
        "team_a": [], "team_b": [],
        "team_a_name": "Team 1",
        "team_b_name": "Team 2",
        "striker": "", "non_striker": "", "current_bowler": "",
        "history_log": [],
        "setup": False,
        "innings": 1,
        "target": 0,
        "max_overs": 0,
        "first_innings_score": 0,
        "match_over": False,
        "innings_1_snapshot": None
    }

m = st.session_state.match

if "history_log" not in m:
    m["history_log"] = []

# --- STEP 1: TOURNAMENT SETUP ---
if not m["setup"]:
    st.header("🏟️ Cricket Match Setup")
    
    col_setup1, col_setup2 = st.columns(2)
    with col_setup1:
        m["team_a_name"] = st.text_input("Team 1 Name (Batting First)", "India")
        t_a_input = st.text_area("Team 1 Players", "Rohit\nKohli\nSky\nHardik\nPant")
        m["max_overs"] = st.number_input("Total Match Overs", min_value=1, max_value=50, value=5)
    with col_setup2:
        m["team_b_name"] = st.text_input("Team 2 Name (Bowling First)", "Australia")
        t_b_input = st.text_area("Team 2 Players", "Bumrah\nShami\nSiraj\nKuldeep")
    
    if st.button("🏟️ Start Match", use_container_width=True):
        m["team_a"] = [p.strip() for p in t_a_input.split('\n') if p.strip()]
        m["team_b"] = [p.strip() for p in t_b_input.split('\n') if p.strip()]
        
        for p in m["team_a"]: m["batting_stats"][p] = {"runs": 0, "balls": 0, "out": False}
        for p in m["team_b"]: m["bowling_stats"][p] = {"runs": 0, "balls": 0, "wickets": 0}
        
        if len(m["team_a"]) >= 2 and len(m["team_b"]) >= 1:
            m["striker"], m["non_striker"] = m["team_a"][0], m["team_a"][1]
            m["current_bowler"] = m["team_b"][0]
            m["setup"] = True
            st.rerun()
        else:
            st.error("Ensure both teams have enough players!")

# --- STEP 2: SCORING LOGIC & INNINGS SWITCH ---
else:
    is_all_out = m["wickets"] >= len(m["team_a"]) - 1
    is_overs_done = m["balls"] >= (m["max_overs"] * 6)
    
    if m["innings"] == 2:
        if m["score"] >= m["target"]:
            st.success(f"🎊 Match Over! {m['team_a_name']} won by {len(m['team_a']) - 1 - m['wickets']} wickets!")
            m["match_over"] = True
        elif (is_all_out or is_overs_done) and m["score"] < m["target"]:
            st.error(f"🎊 Match Over! {m['team_b_name']} won by {m['target'] - m['score'] - 1} runs!")
            m["match_over"] = True

    if (is_all_out or is_overs_done) and m["innings"] == 1:
        st.warning(f"Innings 1 Finished! {m['team_a_name']} Score: {m['score']}/{m['wickets']}")
        if st.button("Start 2nd Innings (Chase Mode)", use_container_width=True):
            # Save 1st Innings Data
            m["innings_1_snapshot"] = {
                "batting": pd.DataFrame([{"Player": p, "R": s["runs"], "B": s["balls"], "SR": round(s["runs"]/s["balls"]*100,2) if s["balls"]>0 else 0, "Status": "Out" if s["out"] else "Not Out"} for p, s in m["batting_stats"].items()]),
                "bowling": pd.DataFrame([{"Bowler": p, "O": format_overs(s['balls']), "W": s["wickets"], "R": s["runs"], "Econ": calculate_economy(s['runs'], s['balls'])} for p, s in m["bowling_stats"].items()]),
                "team_name": m["team_a_name"]
            }
            # Switch roles
            m["target"] = m["score"] + 1
            m["team_a"], m["team_b"] = m["team_b"], m["team_a"]
            m["team_a_name"], m["team_b_name"] = m["team_b_name"], m["team_a_name"]
            m["score"], m["wickets"], m["balls"] = 0, 0, 0
            m["batting_stats"] = {p: {"runs": 0, "balls": 0, "out": False} for p in m["team_a"]}
            m["bowling_stats"] = {p: {"runs": 0, "balls": 0, "wickets": 0} for p in m["team_b"]}
            m["striker"], m["non_striker"] = m["team_a"][0], m["team_a"][1]
            m["current_bowler"] = m["team_b"][0]
            m["innings"] = 2
            m["history_log"] = []
            st.rerun()
        st.stop()

    # --- STEP 3: LIVE SCOREBOARD ---
    st.markdown(f"### {'🎯 Chasing' if m['innings'] == 2 else '🏏 Batting'}: {m['striker']}* vs {m['current_bowler']}")
    
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    m_col1.metric("Score", f"{m['score']} - {m['wickets']}")
    m_col2.metric("Overs", f"{format_overs(m['balls'])} / {m['max_overs']}")
    
    if m["innings"] == 2:
        runs_needed = m["target"] - m["score"]
        balls_left = (m["max_overs"] * 6) - m["balls"]
        m_col3.metric("Need", f"{max(0, runs_needed)} runs")
        m_col4.metric("Req. RR", f"{(runs_needed/(balls_left/6)):.2f}" if balls_left > 0 else "0.00")
    else:
        ov = (m['balls'] / 6)
        m_col3.metric("Current RR", f"{(m['score']/ov):.2f}" if ov > 0 else "0.00")
        m_col4.metric("Last 6 Balls", " | ".join(m["history_log"][-6:]))

    # Scoring Inputs
    if not m["match_over"]:
        st.divider()
        not_out = [p for p, s in m["batting_stats"].items() if not s["out"]]
        
        c1, c2, c3 = st.columns(3)
        with c1: m["striker"] = st.selectbox("On Strike", not_out, index=not_out.index(m["striker"]) if m["striker"] in not_out else 0)
        with c2: 
            others = [p for p in not_out if p != m["striker"]]
            m["non_striker"] = st.selectbox("Non-Striker", others, index=others.index(m["non_striker"]) if m["non_striker"] in others else 0)
        with c3: m["current_bowler"] = st.selectbox("Current Bowler", m["team_b"], index=m["team_b"].index(m["current_bowler"]))

        # Radio buttons for quicker entry
        ball_res = st.radio("Select Ball Result:", options=["0", "1", "2", "3", "4", "6", "W", "WD", "NB"], horizontal=True)

        if st.button("🚀 Record Ball", use_container_width=True):
            swap = False
            if ball_res in ["WD", "NB"]:
                m["score"] += 1
                m["bowling_stats"][m["current_bowler"]]["runs"] += 1
                m["history_log"].append(ball_res)
            else:
                m["balls"] += 1
                m["bowling_stats"][m["current_bowler"]]["balls"] += 1
                m["history_log"].append(ball_res)
                
                if ball_res == "W":
                    m["wickets"] += 1
                    m["batting_stats"][m["striker"]]["out"] = True
                    m["bowling_stats"][m["current_bowler"]]["wickets"] += 1
                    st.toast(f"WICKET! {m['striker']} departed!")
                    st.snow()
                else:
                    runs = int(ball_res)
                    m["score"] += runs
                    m["batting_stats"][m["striker"]]["runs"] += runs
                    m["batting_stats"][m["striker"]]["balls"] += 1
                    m["bowling_stats"][m["current_bowler"]]["runs"] += runs
                    
                    if runs == 4: 
                        st.toast("FOUR! Brilliant shot!"); st.balloons()
                    if runs == 6: 
                        st.toast("SIX! Over the ropes!"); st.balloons()
                    if runs % 2 != 0: 
                        swap = True

            # Handle Over Completion
            if m["balls"] % 6 == 0 and ball_res not in ["WD", "NB"]:
                swap = not swap
                st.success(f"Over completed! {format_overs(m['balls'])} Overs done.")

            if swap: m["striker"], m["non_striker"] = m["non_striker"], m["striker"]
            st.rerun()

    # --- STEP 4: TABLES & DOWNLOADS ---
    st.divider()
    t_bat, t_bow, t_dl = st.tabs(["🏏 Live Batting", "🥎 Live Bowling", "📥 Full Report"])
    
    with t_bat:
        bat_df = pd.DataFrame([{"Player": p, "R": s["runs"], "B": s["balls"], "SR": round(s["runs"]/s["balls"]*100,2) if s["balls"]>0 else 0, "Status": "Out" if s["out"] else "Not Out"} for p, s in m["batting_stats"].items()])
        st.subheader(f"Batting: {m['team_a_name']}")
        st.table(bat_df)
    
    with t_bow:
        bow_df = pd.DataFrame([{"Bowler": p, "O": format_overs(s['balls']), "W": s["wickets"], "R": s["runs"], "Econ": calculate_economy(s['runs'], s['balls'])} for p, s in m["bowling_stats"].items()])
        st.subheader(f"Bowling: {m['team_b_name']}")
        st.table(bow_df)
    
    with t_dl:
        st.header("📥 Match Report Downloads")
        if m["innings_1_snapshot"] is not None:
            st.subheader(f"Innings 1: {m['innings_1_snapshot']['team_name']}")
            c1, c2 = st.columns(2)
            c1.download_button("I1 Batting CSV", m["innings_1_snapshot"]["batting"].to_csv(index=False), "i1_batting.csv")
            c2.download_button("I1 Bowling CSV", m["innings_1_snapshot"]["bowling"].to_csv(index=False), "i1_bowling.csv")
            st.divider()
        
        st.subheader(f"Innings 2: {m['team_a_name']}")
        c3, c4 = st.columns(2)
        c3.download_button("I2 Batting CSV", bat_df.to_csv(index=False), "i2_batting.csv")
        c4.download_button("I2 Bowling CSV", bow_df.to_csv(index=False), "i2_bowling.csv")

if st.sidebar.button("Reset Match"):
    st.session_state.clear()
    st.rerun()