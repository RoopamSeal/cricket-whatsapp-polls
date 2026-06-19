"""
Home / Dashboard page
"""
import streamlit as st
import pandas as pd
from datetime import date
from src.config import Config
from src.storage import Storage

config = Config()
storage = Storage(config)

# ==========================================
# NOT LOGGED IN — Landing Page
# ==========================================
if st.session_state.user_id is None:

    # ── Hero Banner ──────────────────────────────────────────────
    st.markdown("""
<div style="background: linear-gradient(135deg, rgba(10,30,15,0.82) 0%, rgba(26,71,42,0.75) 50%, rgba(229,50,56,0.55) 100%),
            url('https://s.yimg.com/ny/api/res/1.2/2DOPtSxLvgCKhWuhEIUNTQ--/YXBwaWQ9aGlnaGxhbmRlcjt3PTk2MDtoPTU0MDtjZj13ZWJw/https://media.zenfs.com/en/wdaf_articles_412/6e591ad86accfc2fa04d6bff48ecf693') center/cover no-repeat;
     padding: 5rem 2rem 3rem; border-radius: 1.5rem; text-align: center;
     margin-bottom: 0; box-shadow: 0 8px 32px rgba(0,0,0,0.35);">
  <div style="display:inline-block; background:rgba(255,184,28,0.15); border:1px solid rgba(255,184,28,0.5);
              border-radius:2rem; padding:0.3rem 1.2rem; margin-bottom:1rem;">
    <span style="color:#ffb81c; font-size:0.85rem; font-weight:700; letter-spacing:3px;">FIFA WORLD CUP</span>
  </div>
  <h1 style="color:#ffffff; font-size:4rem; font-weight:900; margin:0; line-height:1.1;
             text-shadow:0 4px 20px rgba(0,0,0,0.5); border:none; padding:0;">⚽ 2026</h1>
  <h2 style="color:#ffb81c; font-size:1.4rem; font-weight:700; margin:0.5rem 0 0; letter-spacing:4px;
             border:none; text-shadow:0 2px 8px rgba(0,0,0,0.4);">PREDICTION PLATFORM</h2>
  <p style="color:rgba(255,255,255,0.85); font-size:1.1rem; max-width:520px; margin:1rem auto 0;
            line-height:1.6;">Predict every match. Climb the leaderboard. Prove your football IQ.</p>
</div>
""", unsafe_allow_html=True)

    # ── Centered Login Card ───────────────────────────────────────
    st.markdown("<div style='height:0.1rem'></div>", unsafe_allow_html=True)
    _, col_login, _ = st.columns([1, 1.4, 1])
    with col_login:
        st.markdown("""
<div class="glass-card animate-in" style="margin-top:-2rem; position:relative; z-index:10;">
  <div style="font-size:2.8rem; margin-bottom:0.4rem;">🏆</div>
  <h2 style="color:#1a472a; border:none; font-size:1.5rem; margin:0 0 0.3rem; font-weight:800;">
      Join the Tournament
  </h2>
  <p style="color:#666; font-size:0.9rem; margin:0 0 1.5rem;">Create or continue your profile to start predicting</p>
</div>
""", unsafe_allow_html=True)
        username = st.text_input(
            "Username",
            placeholder="Enter your username...",
            label_visibility="collapsed",
            key="home_login_username",
        )
        if st.button("⚡  JOIN NOW", use_container_width=True, type="primary"):
            if username.strip():
                user = storage.get_or_create_user(username.strip())
                st.session_state.user_id = user['user_id']
                st.session_state.user_name = user['user_name']
                st.success(f"🎉 Welcome, {username.strip()}!")
                st.rerun()
            else:
                st.error("Please enter a username to continue.")

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

    # ── Feature Cards ─────────────────────────────────────────────
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
<div class="feature-card" style="background:linear-gradient(145deg,#1a472a,#0d2b18);
     border:1.5px solid rgba(255,184,28,0.4); box-shadow:0 8px 25px rgba(26,71,42,0.3);">
  <div style="font-size:2.5rem; margin-bottom:0.8rem;">🎯</div>
  <h3 style="color:#ffb81c; border:none; margin:0 0 0.5rem; font-size:1.3rem; font-weight:800;">PREDICT</h3>
  <p style="color:rgba(255,255,255,0.8); font-size:0.95rem; margin:0; line-height:1.6;">
      Make predictions on all 104 matches of the tournament
  </p>
</div>
""", unsafe_allow_html=True)
    with c2:
        st.markdown("""
<div class="feature-card" style="background:linear-gradient(145deg,#c41e3a,#8b0000);
     border:1.5px solid rgba(255,184,28,0.4); box-shadow:0 8px 25px rgba(229,50,56,0.3);">
  <div style="font-size:2.5rem; margin-bottom:0.8rem;">🏆</div>
  <h3 style="color:#ffb81c; border:none; margin:0 0 0.5rem; font-size:1.3rem; font-weight:800;">COMPETE</h3>
  <p style="color:rgba(255,255,255,0.8); font-size:0.95rem; margin:0; line-height:1.6;">
      Battle it out on the global leaderboard with fans worldwide
  </p>
</div>
""", unsafe_allow_html=True)
    with c3:
        st.markdown("""
<div class="feature-card" style="background:linear-gradient(145deg,#d4940a,#b8860b);
     border:1.5px solid rgba(255,255,255,0.3); box-shadow:0 8px 25px rgba(255,184,28,0.3);">
  <div style="font-size:2.5rem; margin-bottom:0.8rem;">⭐</div>
  <h3 style="color:#fff; border:none; margin:0 0 0.5rem; font-size:1.3rem; font-weight:800;">WIN</h3>
  <p style="color:rgba(255,255,255,0.9); font-size:0.95rem; margin:0; line-height:1.6;">
      Earn points, claim badges, and reach the top of the rankings
  </p>
</div>
""", unsafe_allow_html=True)

    st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)
    st.markdown("<hr style='border:1px solid rgba(255,184,28,0.25); margin:0 0 2rem;'>", unsafe_allow_html=True)

    # ── Scoring Rules + Tournament Info ───────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
<div style="background:linear-gradient(135deg,#ffffff,#f0faf4); padding:1.8rem; border-radius:1.2rem;
     box-shadow:0 4px 20px rgba(26,71,42,0.1); border-left:5px solid #1a472a; height:100%;">
  <h3 style="color:#1a472a; border:none; margin:0 0 1rem; font-size:1.2rem;">💰 Scoring Rules</h3>
  <div style="display:flex; flex-direction:column; gap:0.6rem; font-size:1rem;">
    <div style="display:flex; align-items:center; gap:0.7rem; padding:0.6rem; background:rgba(76,175,80,0.08); border-radius:0.6rem;">
      <span style="font-size:1.3rem;">🟢</span>
      <span><strong>Correct Winner</strong> &mdash; <span style="color:#1a472a; font-weight:700;">+3 pts</span></span>
    </div>
    <div style="display:flex; align-items:center; gap:0.7rem; padding:0.6rem; background:rgba(255,184,28,0.08); border-radius:0.6rem;">
      <span style="font-size:1.3rem;">🟡</span>
      <span><strong>Correct Draw</strong> &mdash; <span style="color:#d4940a; font-weight:700;">+2 pts</span></span>
    </div>
    <div style="display:flex; align-items:center; gap:0.7rem; padding:0.6rem; background:rgba(229,50,56,0.06); border-radius:0.6rem;">
      <span style="font-size:1.3rem;">🔴</span>
      <span><strong>Wrong Pick</strong> &mdash; <span style="color:#e53238; font-weight:700;">0 pts</span></span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)
    with col2:
        st.markdown("""
<div style="background:linear-gradient(135deg,#1a472a,#0d2b18); padding:1.8rem; border-radius:1.2rem;
     box-shadow:0 4px 20px rgba(26,71,42,0.2); height:100%;">
  <h3 style="color:#ffb81c; border:none; margin:0 0 1rem; font-size:1.2rem;">📅 Tournament Info</h3>
  <div style="display:flex; flex-direction:column; gap:0.6rem; font-size:0.95rem; color:rgba(255,255,255,0.9);">
    <div style="display:flex; gap:0.7rem; align-items:center;">🌍 <span><strong>Event:</strong> FIFA World Cup 2026</span></div>
    <div style="display:flex; gap:0.7rem; align-items:center;">🏟️ <span><strong>Hosts:</strong> 🇺🇸 USA &bull; 🇨🇦 Canada &bull; 🇲🇽 Mexico</span></div>
    <div style="display:flex; gap:0.7rem; align-items:center;">👥 <span><strong>Teams:</strong> 48 Nations</span></div>
    <div style="display:flex; gap:0.7rem; align-items:center;">⚽ <span><strong>Matches:</strong> 104 Games</span></div>
    <div style="display:flex; gap:0.7rem; align-items:center;">📆 <span><strong>Kicks off:</strong> June 11, 2026</span></div>
  </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# LOGGED IN — Dashboard
# ==========================================
else:
    st.markdown(f"""
<div style="background:linear-gradient(135deg,#1a472a 0%,#2d5a3d 60%,#1a472a 100%);
     padding:2rem; border-radius:1.2rem; text-align:center; margin-bottom:1.5rem;
     box-shadow:0 6px 24px rgba(26,71,42,0.25);">
  <h1 style="color:#ffffff; border:none; padding:0; margin:0; font-size:2.2rem; font-weight:900;">
      ⚽ WORLD CUP 2026 DASHBOARD
  </h1>
  <p style="color:#ffb81c; margin:0.4rem 0 0; font-size:1rem; letter-spacing:2px;">
      🇺🇸 USA &nbsp;|&nbsp; 🇨🇦 CANADA &nbsp;|&nbsp; 🇲🇽 MEXICO
  </p>
</div>
""", unsafe_allow_html=True)

    # Tournament Info Strip
    st.markdown("""
<div style="display:grid; grid-template-columns:repeat(4,1fr); gap:1rem; margin-bottom:1.5rem;">
  <div style="background:linear-gradient(135deg,#ffffff,#f0faf4); padding:1.2rem; border-radius:1rem;
       text-align:center; border:1.5px solid rgba(255,184,28,0.3); box-shadow:0 3px 12px rgba(26,71,42,0.08);">
    <p style="color:#ffb81c; font-size:0.75rem; font-weight:700; letter-spacing:2px; margin:0;">TOURNAMENT</p>
    <h3 style="color:#1a472a; border:none; margin:0.3rem 0 0; font-size:1.2rem;">FIFA 2026</h3>
  </div>
  <div style="background:linear-gradient(135deg,#ffffff,#f0faf4); padding:1.2rem; border-radius:1rem;
       text-align:center; border:1.5px solid rgba(255,184,28,0.3); box-shadow:0 3px 12px rgba(26,71,42,0.08);">
    <p style="color:#ffb81c; font-size:0.75rem; font-weight:700; letter-spacing:2px; margin:0;">HOST NATIONS</p>
    <h3 style="color:#1a472a; border:none; margin:0.3rem 0 0; font-size:1.2rem;">3 Countries</h3>
  </div>
  <div style="background:linear-gradient(135deg,#ffffff,#f0faf4); padding:1.2rem; border-radius:1rem;
       text-align:center; border:1.5px solid rgba(255,184,28,0.3); box-shadow:0 3px 12px rgba(26,71,42,0.08);">
    <p style="color:#ffb81c; font-size:0.75rem; font-weight:700; letter-spacing:2px; margin:0;">TEAMS</p>
    <h3 style="color:#1a472a; border:none; margin:0.3rem 0 0; font-size:1.2rem;">48 Nations</h3>
  </div>
  <div style="background:linear-gradient(135deg,#ffffff,#f0faf4); padding:1.2rem; border-radius:1rem;
       text-align:center; border:1.5px solid rgba(255,184,28,0.3); box-shadow:0 3px 12px rgba(26,71,42,0.08);">
    <p style="color:#ffb81c; font-size:0.75rem; font-weight:700; letter-spacing:2px; margin:0;">MATCHES</p>
    <h3 style="color:#1a472a; border:none; margin:0.3rem 0 0; font-size:1.2rem;">104 Games</h3>
  </div>
</div>
""", unsafe_allow_html=True)

    # Tournament Stats
    st.markdown("<h2 style='color:#1a472a; border-bottom:3px solid #ffb81c;'>📊 Tournament Statistics</h2>", unsafe_allow_html=True)
    try:
        tournament_stats = storage.get_tournament_stats()
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("👥 Users", int(float(tournament_stats.get('Total Users', 0))))
        with col2:
            st.metric("🎯 Matches", int(float(tournament_stats.get('Total Matches', 0))))
        with col3:
            st.metric("🔜 Upcoming", int(float(tournament_stats.get('Scheduled Matches', 0))))
        with col4:
            st.metric("✅ Completed", int(float(tournament_stats.get('Completed Matches', 0))))
        with col5:
            st.metric("⭐ Predictions", int(float(tournament_stats.get('Total Predictions', 0))))
        st.markdown("---")
    except Exception as e:
        st.warning(f"Could not load tournament stats: {e}")

    # Upcoming Matches — Date Picker
    st.markdown("<h2 style='color:#1a472a; border-bottom:3px solid #ffb81c;'>🔜 Upcoming Matches</h2>", unsafe_allow_html=True)

    try:
        matches = storage.get_all_matches()
        matches_df = pd.DataFrame(matches)

        if matches_df.empty:
            st.info("No matches scheduled yet")
        else:
            active_matches = matches_df[matches_df['status'].isin(['scheduled', 'live'])].copy()
            if active_matches.empty:
                st.info("No upcoming matches")
            else:
                active_matches['match_datetime'] = pd.to_datetime(
                    active_matches['match_date'] + ' ' + active_matches['kickoff_time']
                )
                active_matches = active_matches.sort_values('match_datetime')
                match_dates = sorted(pd.to_datetime(active_matches['match_date']).dt.date.unique())

                today = date.today()
                default_date = next((d for d in match_dates if d >= today), match_dates[0])

                if 'home_match_date' not in st.session_state or st.session_state.home_match_date not in match_dates:
                    st.session_state.home_match_date = default_date

                col_prev, col_date, col_next = st.columns([1, 4, 1])
                current_idx = match_dates.index(st.session_state.home_match_date)

                with col_prev:
                    if st.button("◀ Prev", use_container_width=True, disabled=(current_idx == 0)):
                        st.session_state.home_match_date = match_dates[current_idx - 1]
                        st.rerun()
                with col_date:
                    chosen = st.date_input(
                        "Match Date",
                        value=st.session_state.home_match_date,
                        min_value=match_dates[0],
                        max_value=match_dates[-1],
                        key="home_date_picker",
                        label_visibility="collapsed",
                    )
                    if chosen != st.session_state.home_match_date:
                        nearest = min(match_dates, key=lambda d: abs((d - chosen).days))
                        st.session_state.home_match_date = nearest
                        st.rerun()
                with col_next:
                    if st.button("Next ▶", use_container_width=True, disabled=(current_idx >= len(match_dates) - 1)):
                        st.session_state.home_match_date = match_dates[current_idx + 1]
                        st.rerun()

                selected_date = st.session_state.home_match_date
                day_matches = active_matches[
                    pd.to_datetime(active_matches['match_date']).dt.date == selected_date
                ]

                st.markdown(
                    f"<p style='color:#666; margin:0.5rem 0 1rem;'>📋 <strong>{len(day_matches)}</strong> match(es) on "
                    f"<strong>{selected_date.strftime('%B %d, %Y')}</strong></p>",
                    unsafe_allow_html=True,
                )

                if day_matches.empty:
                    st.info(f"No matches on {selected_date.strftime('%B %d, %Y')}. Try another date.")
                else:
                    for _, match in day_matches.iterrows():
                        match_datetime_us = pd.to_datetime(f"{match['match_date']} {match['kickoff_time']}")
                        match_datetime_ist = match_datetime_us + pd.Timedelta(hours=9, minutes=30)
                        st.markdown(f"""
<div class="match-card">
<div style="display:grid; grid-template-columns:2fr 1fr 2fr 1.5fr; gap:1rem; align-items:center;">
<div style="text-align:right;"><h4 style="color:#1a472a; margin:0; font-size:1.1rem; font-weight:700;">{match['team_1']}</h4></div>
<div style="text-align:center;"><span style="background:#ffb81c; color:#1a472a; padding:0.5rem 0.8rem; border-radius:0.4rem; font-weight:700; font-size:0.85rem;">vs</span></div>
<div style="text-align:left;"><h4 style="color:#1a472a; margin:0; font-size:1.1rem; font-weight:700;">{match['team_2']}</h4></div>
<div style="text-align:center;"><p style="color:#666; margin:0; font-size:0.9rem;">📅 {match_datetime_ist.strftime('%b %d')}<br>🕐 {match_datetime_ist.strftime('%H:%M')} IST<br>📍 {match['venue']}</p></div>
</div>
<div style="margin-top:0.8rem; padding-top:0.8rem; border-top:1px solid #e0e0e0;"><span style="background:#e53238; color:white; padding:0.3rem 0.6rem; border-radius:0.3rem; font-size:0.8rem; font-weight:600;">{match['stage']}</span></div>
</div>
""", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error loading matches: {e}")

    st.markdown("---")

    # Leaderboard Preview
    st.markdown("<h2 style='color:#1a472a; border-bottom:3px solid #ffb81c;'>🏆 Top 10 Leaderboard</h2>", unsafe_allow_html=True)
    try:
        leaderboard = storage.get_leaderboard(limit=10)
        if leaderboard:
            lb_df = pd.DataFrame(leaderboard)
            display_df = lb_df[['rank', 'user_name', 'total_points', 'accuracy_percentage']].copy()
            display_df.columns = ['🏅', 'Player', '⭐ Points', '📊 Accuracy %']
            display_df['🏅'] = display_df['🏅'].apply(
                lambda x: '🥇' if x == 1 else '🥈' if x == 2 else '🥉' if x == 3 else f'#{x}'
            )
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("Leaderboard will appear once users make predictions")
    except Exception as e:
        st.error(f"Error loading leaderboard: {e}")

    st.markdown("---")

    # User Stats
    st.markdown("<h2 style='color:#1a472a; border-bottom:3px solid #ffb81c;'>👤 Your Statistics</h2>", unsafe_allow_html=True)
    try:
        col1, col2, col3, col4 = st.columns(4)
        predictions = storage.get_user_prediction_count(st.session_state.user_id)
        correct = storage.get_user_correct_predictions(st.session_state.user_id)
        accuracy = (correct / predictions * 100) if predictions > 0 else 0
        points = storage.get_user_total_points(st.session_state.user_id)
        with col1:
            st.metric("🎯 Predictions", predictions)
        with col2:
            st.metric("✅ Correct", correct)
        with col3:
            st.metric("📊 Accuracy", f"{accuracy:.1f}%")
        with col4:
            st.metric("⭐ Total Points", points)

        user_rank = storage.get_user_rank(st.session_state.user_id)
        if user_rank:
            total_players = len(storage.get_leaderboard())
            pct = (user_rank['rank'] / total_players * 100) if total_players else 0
            st.markdown(f"""
<div style="background:linear-gradient(135deg,#ffb81c 0%,#ffa500 100%); padding:1.5rem; border-radius:1rem;
     text-align:center; color:#1a472a; box-shadow:0 6px 20px rgba(255,184,28,0.3); margin-top:1rem;">
<h3 style="color:#1a472a; border:none; margin:0; font-size:1.8rem;">🎯 Rank #{user_rank['rank']}</h3>
<p style="margin:0.4rem 0 0; font-weight:600;">You're in the top {100 - pct:.1f}% of all players</p>
</div>
""", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error loading user stats: {e}")

    st.markdown("---")

    # How to Play
    st.markdown("<h2 style='color:#1a472a; border-bottom:3px solid #ffb81c;'>ℹ️ How to Play</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
<div class="prediction-card">
<h3 style="color:#e53238; border:none; margin-top:0;">🎯 Make Predictions</h3>
<ul style="color:#555; margin:0; line-height:1.8;">
<li>Go to the <b>Predict</b> page</li>
<li>Choose upcoming matches</li>
<li>Select your predicted winner</li>
<li>Lock in before kickoff</li>
</ul>
</div>
""", unsafe_allow_html=True)
    with col2:
        st.markdown("""
<div class="prediction-card">
<h3 style="color:#e53238; border:none; margin-top:0;">📊 Track Performance</h3>
<ul style="color:#555; margin:0; line-height:1.8;">
<li>Visit <b>My Predictions</b></li>
<li>View your prediction history</li>
<li>Check accuracy metrics</li>
<li>Earn points for correct picks</li>
</ul>
</div>
""", unsafe_allow_html=True)
    with col3:
        st.markdown("""
<div class="prediction-card">
<h3 style="color:#e53238; border:none; margin-top:0;">🏆 Climb Rankings</h3>
<ul style="color:#555; margin:0; line-height:1.8;">
<li>Check the <b>Leaderboard</b></li>
<li>Compete globally</li>
<li>Earn achievement badges</li>
<li>Have fun! ⚽</li>
</ul>
</div>
""", unsafe_allow_html=True)

    st.markdown("---")

    # Scoring System
    st.markdown("<h2 style='color:#1a472a; border-bottom:3px solid #ffb81c;'>⭐ Scoring System</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
<div class="score-pill" style="background:linear-gradient(135deg,#4caf50,#2e7d32); color:white; box-shadow:0 6px 20px rgba(76,175,80,0.3);">
<h3 style="color:#fff; border:none; margin:0; font-size:1.1rem;">✅ CORRECT WINNER</h3>
<p style="margin:0.5rem 0 0; font-size:2rem; font-weight:900;">+3</p>
<small style="opacity:0.85;">points</small>
</div>
""", unsafe_allow_html=True)
    with col2:
        st.markdown("""
<div class="score-pill" style="background:linear-gradient(135deg,#ffb81c,#e65100); color:#1a472a; box-shadow:0 6px 20px rgba(255,184,28,0.35);">
<h3 style="color:#1a472a; border:none; margin:0; font-size:1.1rem;">🤝 CORRECT DRAW</h3>
<p style="margin:0.5rem 0 0; font-size:2rem; font-weight:900;">+2</p>
<small style="opacity:0.7;">points</small>
</div>
""", unsafe_allow_html=True)
    with col3:
        st.markdown("""
<div class="score-pill" style="background:linear-gradient(135deg,#e53238,#8b0000); color:white; box-shadow:0 6px 20px rgba(229,50,56,0.3);">
<h3 style="color:#fff; border:none; margin:0; font-size:1.1rem;">❌ WRONG PICK</h3>
<p style="margin:0.5rem 0 0; font-size:2rem; font-weight:900;">0</p>
<small style="opacity:0.85;">points</small>
</div>
""", unsafe_allow_html=True)
