"""
My Predictions page - View prediction history with FIFA 2026 design
"""
import streamlit as st
import pandas as pd
from src.config import Config
from src.storage import Storage

# Initialize
config = Config()
storage = Storage(config)
storage.initialize_data_layer()

st.markdown("""
<h1 style="text-align: center;">📊 MY PREDICTIONS</h1>
<p style="text-align: center; color: #e53238; font-size: 1rem;">
    Track your prediction history and performance metrics
</p>
""", unsafe_allow_html=True)

st.markdown("---")

# Check authentication
if st.session_state.user_id is None:
    st.info("👈 Please log in from the Home page to view your predictions")
    st.stop()

try:
    # Get user's predictions
    predictions = storage.get_user_predictions(st.session_state.user_id)
    
    if not predictions:
        st.info("🎯 You haven't made any predictions yet. Go to the Predict page to get started!")
        st.stop()
    
    predictions_df = pd.DataFrame(predictions)
    
    # Get match information
    all_matches = pd.DataFrame(storage.get_all_matches())
    
    # Merge data
    predictions_df = predictions_df.merge(
        all_matches[['match_id', 'team_1', 'team_2', 'match_date', 'kickoff_time', 'stage']],
        on='match_id',
        how='left'
    )
    
    # Sort by date descending
    predictions_df = predictions_df.sort_values('prediction_timestamp', ascending=False)
    
    # Display stats
    st.markdown("<h2 style='color: #1a472a; border-bottom: 3px solid #ffb81c;'>📈 Your Performance</h2>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_preds = len(predictions_df)
    
    # Count correct predictions
    correct = 0
    for _, pred in predictions_df.iterrows():
        result = storage.get_match_result(pred['match_id'])
        if result and result['actual_winner'] == pred['predicted_winner']:
            correct += 1
    
    accuracy = (correct / total_preds * 100) if total_preds > 0 else 0
    points = storage.get_user_total_points(st.session_state.user_id)
    
    # Metric card inline CSS
    metric_style = "background-color: #e2e8f0; padding: 1.2rem; border-radius: 0.8rem; border: 2px solid #ffb81c; box-shadow: 0 4px 10px rgba(0,0,0,0.15); margin-bottom: 0.5rem;"
    
    with col1:
        st.markdown(f"""
        <div style="{metric_style}">
            <p style="color: #1a472a; margin: 0; font-size: 1rem; font-weight: 700;">🎯 Total</p>
            <h3 style="color: #e53238; border: none; margin: 0.5rem 0; font-size: 2rem; font-weight: 800;">{total_preds}</h3>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="{metric_style}">
            <p style="color: #1a472a; margin: 0; font-size: 1rem; font-weight: 700;">✅ Correct</p>
            <h3 style="color: #e53238; border: none; margin: 0.5rem 0; font-size: 2rem; font-weight: 800;">{correct}</h3>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="{metric_style}">
            <p style="color: #1a472a; margin: 0; font-size: 1rem; font-weight: 700;">📊 Accuracy</p>
            <h3 style="color: #e53238; border: none; margin: 0.5rem 0; font-size: 2rem; font-weight: 800;">{accuracy:.1f}%</h3>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div style="{metric_style}">
            <p style="color: #1a472a; margin: 0; font-size: 1rem; font-weight: 700;">⭐ Points</p>
            <h3 style="color: #e53238; border: none; margin: 0.5rem 0; font-size: 2rem; font-weight: 800;">{points}</h3>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Display predictions
    st.markdown("<h2 style='color: #1a472a; border-bottom: 3px solid #ffb81c;'>📋 Prediction History</h2>", unsafe_allow_html=True)
    
    for _, pred in predictions_df.iterrows():
        result = storage.get_match_result(pred['match_id'])
        
        # --- IST TIMING CONVERSION ---
        match_datetime_us = pd.to_datetime(f"{pred['match_date']} {pred['kickoff_time']}")
        match_datetime_ist = match_datetime_us + pd.Timedelta(hours=9, minutes=30)
        # -----------------------------
        
        if result:
            is_correct = result['actual_winner'] == pred['predicted_winner']
            if is_correct:
                status_icon = "✅"
                status_text = "CORRECT"
                status_color = "#4caf50"
                bg_color = "#e8f5e9"
            else:
                status_icon = "❌"
                status_text = "INCORRECT"
                status_color = "#e53238"
                bg_color = "#ffebee"
            
            actual = result['actual_winner']
            points_earned = 3 if (is_correct and actual != 'draw') else 2 if (is_correct and actual == 'draw') else 0
            
            result_html = f'<br><strong>Result:</strong><br><span style="color: #666;">{actual}</span>'
            points_html = f'<span style="background: #ffb81c; color: #1a472a; padding: 0.4rem 0.6rem; border-radius: 0.3rem; font-weight: 600; display: block; margin-top: 0.5rem;">+{points_earned} PTS</span>'
        else:
            status_icon = "⏳"
            status_text = "PENDING"
            status_color = "#2196f3"
            bg_color = "#e3f2fd"
            actual = "-"
            points_earned = 0
            
            result_html = '<br>&mdash;'
            points_html = ''
        
        formatted_date = match_datetime_ist.strftime('%B %d, %Y')
        formatted_time = match_datetime_ist.strftime('%H:%M')
        
        # Flattened HTML to prevent Streamlit Markdown parser breakage
        flat_html = f'<div style="background: {bg_color}; padding: 1.2rem; border-radius: 0.8rem; border-left: 5px solid {status_color}; margin-bottom: 1rem; box-shadow: 0 2px 8px rgba(0,0,0,0.08);"><div style="display: grid; grid-template-columns: 2fr 1fr 2fr 1fr 1fr; gap: 1rem; align-items: center;"><div><h4 style="color: #1a472a; margin: 0; font-size: 1rem; font-weight: 700;">{pred["team_1"]}</h4></div><div style="text-align: center;"><span style="background: #ffb81c; color: #1a472a; padding: 0.3rem 0.6rem; border-radius: 0.3rem; font-weight: 600; font-size: 0.8rem;">vs</span></div><div><h4 style="color: #1a472a; margin: 0; font-size: 1rem; font-weight: 700;">{pred["team_2"]}</h4></div><div style="text-align: center;"><p style="color: #666; margin: 0; font-size: 0.85rem;"><strong>Your Pick:</strong><br><span style="color: #1a472a; font-weight: 700;">{pred["predicted_winner"]}</span>{result_html}</p></div><div style="text-align: center;"><span style="background: {status_color}; color: white; padding: 0.5rem 0.8rem; border-radius: 0.4rem; font-weight: 600; font-size: 0.85rem; display: block; margin-bottom: 0.5rem;">{status_icon} {status_text}</span>{points_html}</div></div><div style="margin-top: 0.8rem; padding-top: 0.8rem; border-top: 1px solid rgba(0,0,0,0.1);"><small style="color: #999;">📅 {formatted_date} at {formatted_time} IST &bull; <span style="background: #e53238; color: white; padding: 0.2rem 0.4rem; border-radius: 0.2rem; font-size: 0.75rem; font-weight: 600;">{pred["stage"]}</span></small></div></div>'
        
        st.markdown(flat_html, unsafe_allow_html=True)

except Exception as e:
    st.error(f"Error loading predictions: {e}")
