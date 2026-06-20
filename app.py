"""
FIFA World Cup 2026 Prediction Platform - App Shell & Navigation
"""
import logging
import streamlit as st
from src.config import Config
from src.storage import Storage
from src.fixtures import FixtureLoader

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="World Cup 2026 Predictor",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize config, storage, and fixtures
config = Config()
storage = Storage(config)
storage.initialize_data_layer()

fixture_loader = FixtureLoader(config)
fixture_loader.ensure_fixtures_loaded(storage)

# Session state initialization
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = None

# Global CSS — applied to every page via navigation shell
st.markdown("""
<style>
    :root {
        --primary-color: #1a472a;
        --secondary-color: #ffb81c;
        --accent-color: #e53238;
        --light-bg: #f5f5f5;
        --card-bg: #ffffff;
    }
    .main {
        padding: 1rem 2rem;
        background: linear-gradient(135deg, #f5f5f5 0%, #ffffff 100%);
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a472a 0%, #2d5a3d 100%);
    }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #ffb81c !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
    }
    h1, h2 {
        color: #1a472a;
        text-shadow: 1px 1px 1px rgba(0,0,0,0.1);
        border-bottom: 3px solid #ffb81c;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
    }
    h3 {
        color: #1a472a;
        border-left: 4px solid #e53238;
        padding-left: 0.8rem;
    }
    .banner-header {
        background: linear-gradient(rgba(26, 71, 42, 0.5), rgba(26, 71, 42, 0.6)),
                    url('https://s.yimg.com/ny/api/res/1.2/2DOPtSxLvgCKhWuhEIUNTQ--/YXBwaWQ9aGlnaGxhbmRlcjt3PTk2MDtoPTU0MDtjZj13ZWJw/https://media.zenfs.com/en/wdaf_articles_412/6e591ad86accfc2fa04d6bff48ecf693') center/cover no-repeat;
        padding: 4rem 2rem;
        border-radius: 1rem;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .banner-header h1 {
        color: #ffffff !important;
        border-bottom: none !important;
        font-size: 3.5rem !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        margin: 0 0 0.5rem 0;
        padding: 0;
    }
    .banner-header h2 {
        color: #ffb81c !important;
        border-bottom: none !important;
        font-size: 1.5rem !important;
        margin: 0;
        letter-spacing: 2px;
    }
    .banner-header p {
        color: #f5f5f5;
        font-size: 1.2rem;
        max-width: 600px;
        margin: 1.5rem auto 0 auto;
        opacity: 0.9;
    }
    .leaderboard-header {
        background: linear-gradient(135deg, #1a472a 0%, #e53238 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 0.8rem;
        margin-bottom: 1.5rem;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    .leaderboard-header h2 {
        color: #ffb81c;
        border: none;
        margin: 0;
        font-size: 1.8rem;
    }
    .stButton > button {
        background: linear-gradient(135deg, #ffb81c 0%, #ffa500 100%);
        color: #1a472a !important;
        border: none;
        border-radius: 0.6rem;
        padding: 0.7rem 1.5rem;
        font-weight: 700;
        transition: all 0.3s ease;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        color: #1a472a !important;
    }
    [data-testid="stMetric"] {
        background-color: #e2e8f0;
        padding: 1.2rem;
        border-radius: 0.8rem;
        border: 2px solid #ffb81c;
        box-shadow: 0 4px 10px rgba(0,0,0,0.15);
        margin-bottom: 0.5rem;
    }
    [data-testid="stMetricLabel"] * {
        color: #1a472a !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
    }
    [data-testid="stMetricValue"] * {
        color: #e53238 !important;
        font-weight: 800 !important;
        font-size: 2rem !important;
    }
    .match-card {
        background: linear-gradient(to right, #e2e8f0 0%, #edf2f7 100%);
        padding: 1.5rem;
        border-radius: 0.8rem;
        margin-bottom: 1rem;
        border: 2px solid #e0e0e0;
        border-left: 4px solid #ffb81c;
        box-shadow: 0 3px 12px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    .match-card:hover {
        border-color: #ffb81c;
        box-shadow: 0 6px 20px rgba(255, 184, 28, 0.15);
        transform: translateX(4px);
    }
    .prediction-card {
        background: linear-gradient(135deg, #e2e8f0 0%, #edf2f7 100%);
        padding: 1.2rem;
        border-radius: 0.8rem;
        margin-bottom: 1rem;
        border-left: 5px solid #e53238;
        border-right: 2px solid #ffb81c;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    .prediction-card:hover {
        box-shadow: 0 4px 16px rgba(0,0,0,0.15);
    }
    .stAlert {
        border-radius: 0.8rem;
        border-left: 4px solid #ffb81c;
    }
    hr {
        border: 1px solid rgba(255, 184, 28, 0.3);
        margin: 2rem 0;
    }
    /* Aesthetic additions */
    .glass-card {
        background: rgba(255, 255, 255, 0.96);
        backdrop-filter: blur(20px);
        border: 1.5px solid rgba(255, 184, 28, 0.4);
        border-radius: 1.5rem;
        box-shadow: 0 25px 50px rgba(26, 71, 42, 0.18), 0 8px 24px rgba(0,0,0,0.08);
        padding: 2.5rem 2rem;
        text-align: center;
    }
    .feature-card {
        border-radius: 1.2rem;
        padding: 2rem 1.5rem;
        text-align: center;
        height: 100%;
        transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.3s ease;
    }
    .feature-card:hover {
        transform: translateY(-10px);
        box-shadow: 0 24px 48px rgba(0,0,0,0.25) !important;
    }
    .score-pill {
        border-radius: 1rem;
        padding: 1.5rem;
        text-align: center;
        transition: transform 0.25s ease, box-shadow 0.25s ease;
    }
    .score-pill:hover {
        transform: translateY(-5px);
    }
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(20px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    .animate-in {
        animation: fadeInUp 0.6s ease both;
    }

    /* ============ MOBILE RESPONSIVE ============ */
    @media screen and (max-width: 768px) {
        /* Tighter padding on small screens */
        [data-testid="stMainBlockContainer"] {
            padding: 0.75rem !important;
        }
        /* Stack Streamlit columns vertically */
        [data-testid="stHorizontalBlock"] {
            flex-wrap: wrap !important;
        }
        [data-testid="column"] {
            flex: 1 1 100% !important;
            min-width: 260px !important;
        }
        /* Touch-friendly tap targets */
        .stButton > button {
            min-height: 48px !important;
            font-size: 0.95rem !important;
        }
        /* Prevent iOS auto-zoom when focusing inputs */
        input, textarea, select,
        .stTextInput input,
        .stSelectbox select {
            font-size: 16px !important;
        }
        /* Headings */
        h1 { font-size: 2rem !important; }
        h2 { font-size: 1.4rem !important; }
        h3 { font-size: 1.1rem !important; }
        /* Banner */
        .banner-header { padding: 2rem 1rem !important; }
        .banner-header h1 { font-size: 2.2rem !important; }
        /* Glass login card */
        .glass-card { padding: 1.5rem 1rem !important; }
        /* Match-card inner grids → flex column */
        .match-card [style*="grid-template-columns"],
        .prediction-card [style*="grid-template-columns"] {
            display: flex !important;
            flex-direction: column !important;
            gap: 0.4rem !important;
        }
        /* Tournament info 4-column grid → 2 columns */
        div[style*="grid-template-columns:repeat(4"] {
            display: flex !important;
            flex-wrap: wrap !important;
        }
        div[style*="grid-template-columns:repeat(4"] > div {
            flex: 1 1 calc(50% - 0.5rem) !important;
            min-width: 130px !important;
        }
        /* Scrollable data tables */
        [data-testid="stDataFrameContainer"],
        [data-testid="stDataFrame"] {
            overflow-x: auto !important;
        }
        /* Metric cards */
        [data-testid="stMetric"] {
            margin-bottom: 0.4rem !important;
        }
        /* Tabs */
        .stTabs [data-baseweb="tab"] {
            padding: 0.6rem 0.8rem !important;
            font-size: 0.85rem !important;
        }
        /* Sidebar full-width when open on mobile */
        section[data-testid="stSidebar"][aria-expanded="true"] {
            min-width: min(280px, 85vw) !important;
            max-width: 85vw !important;
        }
    }

    @media screen and (max-width: 480px) {
        [data-testid="stMainBlockContainer"] { padding: 0.5rem !important; }
        h1 { font-size: 1.6rem !important; }
        .banner-header h1 { font-size: 1.8rem !important; }
        /* Tournament grid → 1 column on very small screens */
        div[style*="grid-template-columns:repeat(4"] > div {
            flex: 1 1 100% !important;
        }
        /* Feature cards */
        .feature-card { margin-bottom: 0.75rem !important; }
    }
</style>
""", unsafe_allow_html=True)

# Shared Sidebar — visible on every page
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; margin: 1rem 0;">
        <h1 style="font-size: 3rem; margin: 0;">⚽</h1>
        <h2 style="color: #ffb81c; font-size: 1.8rem; margin: 0.5rem 0; border: none;">WORLD CUP</h2>
        <h3 style="color: #e53238; font-size: 1.5rem; margin: 0; border: none;">2026</h3>
        <p style="color: #ffffff; font-size: 0.9rem; margin-top: 0.5rem; opacity: 0.8;">PREDICTION PLATFORM</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

if st.session_state.user_id is None:
    st.sidebar.markdown("""
    <div style="text-align: center; padding: 1.5rem 1rem;">
        <div style="font-size: 2.5rem; margin-bottom: 0.8rem;">👋</div>
        <p style="color: rgba(255,255,255,0.9); font-size: 0.95rem; line-height: 1.6; margin: 0;">
            Head to the <strong style="color: #ffb81c;">Home</strong> page to log in and start predicting!
        </p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.sidebar.markdown(f"""
    <div style="background: linear-gradient(135deg, #ffb81c 0%, #e53238 100%);
                padding: 1rem; border-radius: 0.8rem; text-align: center;
                margin-bottom: 1.5rem; box-shadow: 0 4px 12px rgba(0,0,0,0.2);">
        <p style="color: white; font-size: 0.9rem; margin: 0; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;">
            ✅ Logged In As
        </p>
        <p style="color: white; font-size: 1.4rem; margin: 0.5rem 0 0 0; font-weight: 800; text-shadow: 1px 1px 2px rgba(0,0,0,0.2);">
            {st.session_state.user_name}
        </p>
    </div>
    """, unsafe_allow_html=True)

    user_predictions = storage.get_user_prediction_count(st.session_state.user_id)
    user_correct = storage.get_user_correct_predictions(st.session_state.user_id)
    user_points = storage.get_user_total_points(st.session_state.user_id)

    st.sidebar.markdown("### 📊 Your Stats")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.metric("🎯 Preds", user_predictions)
        st.metric("⭐ Points", user_points)
    with col2:
        accuracy = (user_correct / user_predictions * 100) if user_predictions > 0 else 0
        st.metric("✅ Correct", user_correct)
        st.metric("📈 Acc %", f"{accuracy:.1f}%")

    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state.user_id = None
        st.session_state.user_name = None
        st.rerun()

st.sidebar.markdown("""
<div style="text-align: center; color: rgba(255,255,255,0.6); font-size: 0.75rem; margin-top: 2rem;">
    ⚽ FIFA World Cup 2026<br>
    v1.0 | Powered by Data
</div>
""", unsafe_allow_html=True)

# Navigation — defines page titles shown in sidebar
pg = st.navigation([
    st.Page("home.py", title="Home", icon="🏠", default=True),
    st.Page("pages/02_Predict.py", title="Predict", icon="⚽"),
    st.Page("pages/03_My_Predictions.py", title="My Predictions", icon="📊"),
    st.Page("pages/04_Leaderboard.py", title="Leaderboard", icon="🏆"),
    st.Page("pages/05_Admin.py", title="Admin", icon="⚙️"),
])
pg.run()
