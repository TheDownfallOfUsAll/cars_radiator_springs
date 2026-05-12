import streamlit as st
import sqlite3
import hashlib
import os
import re
import difflib
import random
import uuid
from datetime import datetime

# ==========================================================
# DATABASE SETUP
# ==========================================================
def init_db():
    conn = sqlite3.connect('radiator_springs.db')
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        role TEXT DEFAULT 'user',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Create default admin if not exists
    c.execute("SELECT * FROM users WHERE username = 'admin'")
    if not c.fetchone():
        admin_password = hashlib.sha256('admin123'.encode()).hexdigest()
        c.execute("INSERT INTO users (username, password, email, role) VALUES (?, ?, ?, ?)",
                  ('admin', admin_password, 'admin@radiatorsprings.com', 'admin'))
    
    # Products table
    c.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        price REAL,
        category TEXT,
        image_emoji TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Insert sample products if empty
    c.execute("SELECT * FROM products")
    if not c.fetchone():
        # Radiator Springs Foods
        products = [
            ('Route 66 Fries', 'Crispy golden fries inspired by the long highway roads', 5.99, 'radiator_springs', '🍟'),
            ('McQueen Burger', 'Double patty burger with extra speed sauce', 12.99, 'radiator_springs', '🍔'),
            ('Mater Milkshake', 'Creamy vanilla shake with caramel road swirl', 6.99, 'radiator_springs', '🥤'),
            ('Sally\'s Sunshine Pizza', 'Pepperoni pizza with extra cheese', 14.99, 'radiator_springs', '🍕'),
            ('Doc\'s Medical Shake', 'Green detox smoothie with spinach', 7.99, 'radiator_springs', '🥛'),
            ('Luigi\'s Pasta Special', 'Classic Italian pasta with marinara', 13.99, 'radiator_springs', '🍝'),
            ('Ramone\'s Paint Shop Pancakes', 'Colorful pancakes with syrup', 8.99, 'radiator_springs', '🥞'),
            ('Flo\'s V8 Coffee', 'Strong espresso with cream', 4.99, 'radiator_springs', '☕'),
            ('Sheriff\'s BBQ Ribs', 'Slow-cooked BBQ ribs with coleslaw', 16.99, 'radiator_springs', '🍖'),
            ('Mater\'s Tow Truck Tacos', 'Beef tacos with cheese and salsa', 10.99, 'radiator_springs', '🌮'),
            # Filipino Foods
            ('Sinigang na Baboy', 'Sour pork soup with tamarind', 15.99, 'filipino', '🥣'),
            ('Adobo', 'Chicken or pork braised in soy sauce and vinegar', 14.99, 'filipino', '🍗'),
            ('Lechon', 'Roasted pig with crispy skin', 24.99, 'filipino', '🐷'),
            ('Pancit Canton', 'Stir-fried noodles with vegetables', 11.99, 'filipino', '🍜'),
            ('Halo-Halo', 'Shaved ice with sweet toppings', 6.99, 'filipino', '🍨'),
            ('Kare-Kare', 'Oxtail stew with peanut sauce', 16.99, 'filipino', '🥘'),
            ('Bicol Express', 'Spicy pork with coconut milk and chilies', 15.99, 'filipino', '🌶️'),
            ('Pinakbet', 'Mixed vegetables with shrimp paste', 12.99, 'filipino', '🥬'),
            ('Turon', 'Caramelized banana lumpia', 4.99, 'filipino', '🍌'),
            ('Puto', 'Steamed rice cake', 3.99, 'filipino', '🍚'),
        ]
        c.executemany("INSERT INTO products (name, description, price, category, image_emoji) VALUES (?, ?, ?, ?, ?)", products)

    # Chat messages table for ChatGPT-style persistent conversation memory
    c.execute('''CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        character TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # Chat response cache table for faster repeated real-world Q&A
    c.execute('''CREATE TABLE IF NOT EXISTS chat_response_cache (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        character TEXT NOT NULL,
        question_norm TEXT NOT NULL,
        question_raw TEXT NOT NULL,
        response TEXT NOT NULL,
        source TEXT DEFAULT 'openai',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(character, question_norm)
    )''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect('radiator_springs.db')
    conn.row_factory = sqlite3.Row
    return conn

# ==========================================================
# AUTH FUNCTIONS
# ==========================================================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password, email):
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
                  (username, hash_password(password), email))
        conn.commit()
        return True, "Registration successful!"
    except sqlite3.IntegrityError:
        return False, "Username or email already exists!"
    finally:
        conn.close()

def login_user(username, password):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ? AND password = ?",
              (username, hash_password(password)))
    user = c.fetchone()
    conn.close()
    return user

def get_all_users():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, username, email, role, created_at FROM users")
    users = c.fetchall()
    conn.close()
    return users

def get_active_chat_session_id():
    if "chat_session_id" not in st.session_state:
        st.session_state.chat_session_id = f"session_{uuid.uuid4().hex[:12]}"
    return st.session_state.chat_session_id

def save_chat_message(session_id, character, role, content):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO chat_messages (session_id, character, role, content) VALUES (?, ?, ?, ?)",
        (session_id, character, role, content),
    )
    conn.commit()
    conn.close()

def load_chat_messages(session_id, limit=60):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        """
        SELECT role, content, character, created_at
        FROM chat_messages
        WHERE session_id = ?
        ORDER BY id ASC
        LIMIT ?
        """,
        (session_id, limit),
    )
    rows = c.fetchall()
    conn.close()
    return rows

def clear_chat_messages(session_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM chat_messages WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()

def get_cached_chat_response(character, user_input):
    question_norm = normalize_text(user_input)
    if not question_norm:
        return None
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        """
        SELECT response
        FROM chat_response_cache
        WHERE character = ? AND question_norm = ?
        LIMIT 1
        """,
        (character, question_norm),
    )
    row = c.fetchone()
    conn.close()
    return row["response"] if row else None

def upsert_cached_chat_response(character, user_input, response_text, source="openai"):
    question_norm = normalize_text(user_input)
    if not question_norm or not response_text:
        return
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO chat_response_cache (character, question_norm, question_raw, response, source)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(character, question_norm)
        DO UPDATE SET
            question_raw = excluded.question_raw,
            response = excluded.response,
            source = excluded.source,
            updated_at = CURRENT_TIMESTAMP
        """,
        (character, question_norm, user_input, response_text, source),
    )
    conn.commit()
    conn.close()

def retrieve_cached_examples(character, user_input, top_n=2):
    question_norm = normalize_text(user_input)
    if not question_norm:
        return []
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        """
        SELECT question_raw, response
        FROM chat_response_cache
        WHERE character = ?
        ORDER BY updated_at DESC
        LIMIT 25
        """,
        (character,),
    )
    rows = c.fetchall()
    conn.close()
    scored = []
    for row in rows:
        q = row["question_raw"]
        score = difflib.SequenceMatcher(None, question_norm, normalize_text(q)).ratio()
        if score > 0.45:
            scored.append((score, row["question_raw"], row["response"]))
    scored.sort(reverse=True, key=lambda x: x[0])
    return [{"question": q, "response": r, "score": s} for s, q, r in scored[:top_n]]

# ==========================================================
# PAGE CONFIG
# ==========================================================
st.set_page_config(
    page_title="Cars Radiator Springs: Home Of The Recipe",
    page_icon="\U0001F697",
    layout="wide",
)

# Initialize database
init_db()

# ==========================================================
# CUSTOM CSS - Red, Orange, Yellow Gradient Theme
# ==========================================================
st.markdown("""
<style>
    /* Main background gradient */
    .stApp {
        background: radial-gradient(circle at top, #ffd451 0%, #ff9f0d 35%, #ff651f 100%);
        min-height: 100vh;
        color: #111;
    }
    
    /* Content container styling */
    .main-content {
        background: rgba(255, 255, 255, 0.92);
        border-radius: 24px;
        padding: 32px;
        margin: 24px;
        box-shadow: 0 18px 50px rgba(0,0,0,0.18);
    }
    
    /* Sidebar styling (updated look) */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #ffcc00 0%, #ff9f00 45%, #ff6500 100%);
        border-right: 2px solid rgba(33, 33, 33, 0.45);
        box-shadow: 0 0 40px rgba(255, 159, 0, 0.25);
    }

    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stCaption,
    [data-testid="stSidebar"] .css-1oe7j3f,
    [data-testid="stSidebar"] .css-1w4pg4i {
        color: #111;
        font-weight: 700;
        text-shadow: 0 1px 2px rgba(255, 255, 255, 0.5);
    }

    [data-testid="stSidebar"] .stSelectbox > div > div,
    [data-testid="stSidebar"] .stRadio > div,
    [data-testid="stSidebar"] .stTextInput > div > div {
        background: rgba(255, 255, 255, 0.9);
        border: 1px solid rgba(0, 0, 0, 0.12);
        border-radius: 16px;
        padding: 10px;
        color: #111;
    }

    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label {
        background: linear-gradient(135deg, #ffdd65 0%, #ff9b00 100%);
        border: 2px solid rgba(255, 255, 255, 0.45);
        border-radius: 14px;
        margin-bottom: 10px;
        padding: 10px 14px;
        transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
        color: #111;
        font-weight: 800;
        box-shadow: 0 0 12px rgba(255, 173, 51, 0.25);
    }

    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label:hover {
        border-color: #ff4500;
        transform: translateX(4px);
        box-shadow: 0 0 18px rgba(255, 145, 0, 0.55);
    }

    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label[aria-checked="true"] {
        background: linear-gradient(135deg, #ffcc00 0%, #ff8c00 100%);
        color: #111;
        border-color: #ff3b30;
        box-shadow: 0 0 22px rgba(255, 136, 0, 0.55);
    }

    .nav-status {
        background: linear-gradient(135deg, #fff2a4, #ffb93f);
        border: 1px solid rgba(0, 0, 0, 0.12);
        border-radius: 14px;
        padding: 12px 14px;
        margin-bottom: 16px;
        color: #111;
        font-size: 14px;
        font-weight: 800;
        box-shadow: 0 0 20px rgba(255, 152, 0, 0.25);
    }

    .menu-list-box {
        background: rgba(255, 255, 255, 0.92);
        border: 1px solid rgba(0, 0, 0, 0.08);
        border-radius: 16px;
        padding: 14px 16px;
        color: #111;
        font-size: 14px;
        line-height: 1.6;
        box-shadow: 0 0 18px rgba(255, 201, 71, 0.18);
    }
    
    /* Hero box */
    .hero-box {
        background: linear-gradient(135deg, #ffd34d, #ff9f00);
        padding: 44px;
        border-radius: 26px;
        color: #111;
        text-align: center;
        box-shadow: 0 12px 30px rgba(255, 142, 0, 0.22);
        animation: glow 2.8s ease-in-out infinite alternate, fadeIn 1.2s ease-in-out;
    }

    .hero-title {
        font-size: 52px;
        font-weight: 900;
    }

    .hero-subtitle {
        font-size: 22px;
        margin-top: 10px;
        color: #111;
    }

    /* Recipe cards */
    .recipe-card {
        border: 1px solid rgba(255, 149, 0, 0.25);
        background: linear-gradient(180deg, #fff8e8 0%, #ffe8c2 100%);
        padding: 25px;
        border-radius: 20px;
        box-shadow: 0 6px 15px rgba(255, 150, 0, 0.14);
        transition: 0.3s;
        text-align: center;
        margin-bottom: 20px;
        color: #111;
    }

    .recipe-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 12px 20px rgba(255, 145, 0, 0.22);
    }

    .card-title {
        font-size: 24px;
        font-weight: 700;
        color: #111;
    }

    .card-desc {
        font-size: 16px;
        color: #333;
    }

    /* Character cards */
    .character-card {
        background: linear-gradient(135deg, #fff3cc, #ffdaa1);
        padding: 30px;
        border-radius: 20px;
        text-align: center;
        border: 3px solid #ff9500;
        color: #111;
    }

    .character-name {
        font-size: 28px;
        font-weight: 800;
        color: #b03d00;
    }

    .character-quote {
        font-size: 18px;
        font-style: italic;
        color: #333;
        margin-top: 10px;
    }

    /* Product cards */
    .product-card {
        background: linear-gradient(135deg, #fff8e0 0%, #fff1c0 100%);
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 14px rgba(255, 140, 0, 0.14);
        text-align: center;
        transition: 0.3s;
        color: #111;
    }

    .product-card:hover {
        transform: scale(1.05);
        box-shadow: 0 8px 20px rgba(255, 140, 0, 0.2);
    }

    .product-emoji {
        font-size: 60px;
    }

    .product-name {
        font-size: 20px;
        font-weight: 700;
        color: #b24600;
        margin: 10px 0;
    }

    .product-price {
        font-size: 24px;
        font-weight: 800;
        color: #ff7f00;
    }

    /* Chatbot styling */
    .chat-panel {
        background: linear-gradient(135deg, #fff7d4, #ffd35b);
        border-radius: 24px;
        padding: 22px;
        margin-bottom: 24px;
        box-shadow: 0 16px 36px rgba(255, 154, 0, 0.18);
    }

    .chat-header {
        font-size: 24px;
        font-weight: 900;
        color: #111;
        margin-bottom: 10px;
    }

    .chat-hint {
        color: #333;
        font-size: 15px;
        margin-bottom: 18px;
    }

    .chat-message {
        padding: 18px;
        border-radius: 24px;
        margin: 12px 0;
        color: #111;
        border: 1px solid rgba(0,0,0,0.08);
        box-shadow: 0 10px 26px rgba(255, 152, 0, 0.14);
    }

    .chat-user {
        background: linear-gradient(135deg, #fff1b8, #ffb83d);
        text-align: right;
        color: #111;
        font-weight: 700;
        border: 1px solid rgba(255, 148, 0, 0.35);
    }

    .chat-bot {
        background: linear-gradient(135deg, #ffe08a, #ffb347);
        text-align: left;
        color: #111;
        border: 2px solid #ff9f00;
        box-shadow: 0 10px 20px rgba(255, 161, 0, 0.18);
    }

    .chat-bot strong {
        color: #111;
    }

    .chat-user strong {
        color: #111;
    }

    /* Settings styling */
    .settings-card {
        background: linear-gradient(135deg, #fff4cc, #ffc55f);
        border-radius: 24px;
        padding: 24px;
        margin-bottom: 28px;
        box-shadow: 0 18px 38px rgba(255, 160, 0, 0.18);
        border: 1px solid rgba(255, 155, 0, 0.22);
    }

    .settings-title {
        font-size: 30px;
        font-weight: 900;
        margin-bottom: 8px;
        color: #111;
    }

    .settings-subtitle {
        color: #333;
        font-size: 16px;
        margin-bottom: 18px;
    }

    .settings-block {
        background: rgba(255,255,255,0.94);
        border-radius: 18px;
        padding: 18px;
        border: 1px solid rgba(255, 150, 0, 0.22);
        margin-bottom: 18px;
    }

    .settings-block h3 {
        margin-top: 0;
        color: #111;
    }

    /* World tour mission boards */
    .world-tour-card {
        background: linear-gradient(135deg, #fff5d6, #ffcc76);
        border-radius: 24px;
        padding: 22px;
        margin-bottom: 20px;
        border: 1px solid rgba(255, 148, 0, 0.28);
        box-shadow: 0 16px 34px rgba(255, 158, 0, 0.18);
    }

    .mission-board {
        background: linear-gradient(135deg, #fff8e7, #ffd69a);
        border-radius: 22px;
        padding: 18px;
        margin-bottom: 18px;
        border: 1px dashed rgba(255, 145, 0, 0.3);
    }

    .mission-board strong {
        color: #111;
    }

    /* Character selection buttons */
    .char-btn {
        background: linear-gradient(135deg, #ffcc00, #ff9f00);
        color: #111;
        border: none;
        padding: 15px 20px;
        border-radius: 18px;
        font-weight: 800;
        cursor: pointer;
        transition: 0.3s;
        box-shadow: 0 8px 18px rgba(255, 154, 0, 0.2);
    }

    .char-btn:hover {
        transform: scale(1.05);
        box-shadow: 0 10px 24px rgba(255, 146, 0, 0.34);
    }

    .char-btn.active {
        background: linear-gradient(135deg, #ffd54f, #ff9a00);
        border: 3px solid #ff7a00;
        color: #111;
    }

    /* Race cards */
    .race-card {
        background: linear-gradient(135deg, #ffe5b4, #ffaf2f);
        padding: 30px;
        border-radius: 24px;
        color: #111;
        text-align: center;
        border: 3px solid rgba(255, 137, 0, 0.4);
        box-shadow: 0 18px 38px rgba(255, 154, 0, 0.22);
        transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
    }

    .race-card img {
        width: 120px;
        height: 120px;
        object-fit: cover;
        border-radius: 18px;
        margin-bottom: 16px;
        border: 2px solid rgba(255, 159, 0, 0.25);
    }

    .race-card:hover {
        transform: translateY(-8px) scale(1.01);
        box-shadow: 0 24px 46px rgba(255, 155, 0, 0.35);
        border-color: #ff8c00;
    }

    .race-name {
        font-size: 24px;
        font-weight: 800;
        color: #111;
    }

    .race-car {
        font-size: 80px;
    }

    /* Form styling */
    .stTextInput > div > div > input {
        border-radius: 10px;
        border: 2px solid #ff9500;
    }

    .stButton > button {
        background: linear-gradient(135deg, #ffcc00, #ff9500);
        color: #111;
        border-radius: 12px;
        font-weight: bold;
        border: 1px solid rgba(0,0,0,0.12);
        box-shadow: 0 8px 18px rgba(255, 145, 0, 0.24);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 12px 24px rgba(255, 145, 0, 0.32);
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }

    .stTabs [data-baseweb="tab"] {
        background: linear-gradient(135deg, rgba(255, 204, 75, 0.9), rgba(255, 149, 0, 0.9));
        border-radius: 14px;
        padding: 10px 20px;
        color: #111;
        font-weight: 700;
        box-shadow: 0 6px 14px rgba(255, 150, 0, 0.18);
    }

    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, #ffcc00, #ff9f00);
        color: #111;
    }

    @keyframes fadeIn {
        from {opacity: 0; transform: translateY(20px);}
        to {opacity: 1; transform: translateY(0);}
    }

    @keyframes glow {
        from {box-shadow: 0 12px 30px rgba(255, 142, 0, 0.22);}
        to {box-shadow: 0 18px 40px rgba(255, 196, 0, 0.35);}
    }

    @keyframes race {
        0% {transform: translateX(0);}
        50% {transform: translateX(100px);}
        100% {transform: translateX(0);}
    }

    .racing {
        animation: race 1s ease-in-out infinite;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================================
# SESSION STATE
# ==========================================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'role' not in st.session_state:
    st.session_state.role = "user"
if 'theme_choice' not in st.session_state:
    st.session_state.theme_choice = "Orange & Yellow Glow"


def apply_theme_overrides():
    theme = st.session_state.get("theme_choice", "Orange & Yellow Glow")
    if theme == "Classic Radiator Springs":
        st.markdown(
            """
<style>
.stApp {
    background: radial-gradient(circle at top, #ffe6ad 0%, #f6b15f 45%, #d97b26 100%) !important;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #f7dca3 0%, #e8a95a 45%, #c8752f 100%) !important;
}
.main-content, .settings-card, .settings-block {
    border-color: rgba(95, 57, 19, 0.28) !important;
}
</style>
""",
            unsafe_allow_html=True,
        )
    elif theme == "Night Racer":
        st.markdown(
            """
<style>
.stApp {
    background: radial-gradient(circle at top, #2a3142 0%, #121826 45%, #090d16 100%) !important;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #3b4864 0%, #25324a 55%, #121a2c 100%) !important;
    border-right: 2px solid rgba(255, 183, 77, 0.35) !important;
}
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stCaption {
    color: #f5f7ff !important;
}
.settings-card {
    background: linear-gradient(135deg, #202a40, #141a2d) !important;
}
.settings-title, .settings-subtitle {
    color: #f5f7ff !important;
}
.settings-block {
    background: rgba(20, 26, 45, 0.92) !important;
    color: #eef3ff !important;
    border-color: rgba(255, 176, 74, 0.35) !important;
}
.settings-block h3 {
    color: #ffd37d !important;
}
.chat-bot {
    border-color: #ffb347 !important;
}
</style>
""",
            unsafe_allow_html=True,
        )


apply_theme_overrides()

# ==========================================================
# SIDEBAR NAVIGATION
# ==========================================================
# Navigation is rendered in MAIN APP after page functions are defined.
# ==========================================================
# PAGE FUNCTIONS
# ==========================================================

def show_home():
    st.image("logo-of-app.png", width="stretch")
    st.markdown("""
    <div class="hero-box">
        <div class="hero-title">🚗 Cars Radiator Springs</div>
        <div class="hero-subtitle">
            Home Of The Recipe with Lightning McQueen ⚡ and Mater 🚜
        </div>
        <p>Ka-chow your way into delicious meals and cozy recipes from Radiator Springs!</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    st.write("")
    
    # Character Welcome Section
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="character-card">
            <div style="font-size: 80px;">\u26a1</div>
            <div class="character-name">Lightning McQueen</div>
            <div class="character-quote">
                "Ka-chow! Welcome to Radiator Springs! 
                I'm Lightning McQueen, the fastest car in the world!
                Check out our delicious recipes and speed into flavor!"
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="character-card">
            <div style="font-size: 80px;">🚜</div>
            <div class="character-name">Mater</div>
            <div class="character-quote">
                "Howdy! I'm Mater, the best tow truck in Radiator Springs!
                Welcome to our kitchen - we got the best comfort food 
                this side of the highway! Yee-haw!"
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.write("")
    st.info("🏁 Click on 'Login / Register' in the sidebar to get started!")
    
    # Quick preview
    st.subheader("🍔 Quick Preview")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="recipe-card">
            <div class="card-title">🍟 Route 66 Fries</div>
            <div class="card-desc">Crispy golden fries</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="recipe-card">
            <div class="card-title">🍔 McQueen Burger</div>
            <div class="card-desc">Double patty with speed sauce</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="recipe-card">
            <div class="card-title">🥤 Mater Milkshake</div>
            <div class="card-desc">Creamy vanilla shake</div>
        </div>
        """, unsafe_allow_html=True)


def show_story():
    st.image("logo-of-app.png", width="stretch")
    st.markdown("""
    <div class="hero-box">
        <div class="hero-title">📖 The Story of Radiator Springs</div>
        <div class="hero-subtitle">How a forgotten town became the Home Of The Recipe</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    ### 🛣️ A Highway of Flavors
    
    Once upon a time, deep in the heart of Arizona, there was a little town called **Radiator Springs** — a place that time seemed to have passed by. After the interstate diverted traffic away from Route 66, the town quieted down. The neon lights of Flo's V8 Café flickered a little dimmer. The paint shop sat idle. And the aroma of home-cooked meals rarely drifted beyond the kitchen walls.
    
    But everything changed when a certain red race car took a wrong turn and crashed into our lives.
    
    ### ⚡ Ka-Chow! A Star is Reborn
    
    **Lightning McQueen** didn't mean to stay. He was a piston cup champion, a celebrity, a car built for speed — not for small-town hospitality. Yet, something magical happened during those few days he spent fixing the road he tore up. He met **Mater**, the rustiest but most loyal tow truck you could ever know. He met **Sally**, the intelligent and warm-hearted Porsche who saw beauty in the rusty bolts and faded paint of the town. He met **Doc Hudson**, the wise old Hudson Hornet who taught him that winning isn't everything.
    
    McQueen fell in love — not just with the town, but with the people... and the food.
    
    ### 🍜 From Racing Fuel to Real Food
    
    You see, Radiator Springs was never just about racing. It was about community. Every Sunday, the residents would gather at Flo's V8 Café. Flo would serve her famous **V8 Coffee** and **Sunshine Pancakes**. Luigi and Guido would bring over pasta fresh from their tire shop kitchen. Ramone would paint plates as beautifully as he painted cars. And Mater? Well, Mater would bring his famous **Tow Truck Tacos** — a little messy, a lot of love.
    
    When McQueen decided to make Radiator Springs his home, he brought the world with him. Fans from every continent visited. They came for the races, but they stayed for the meals. And that's when Sally had an idea:
    
    > *"Why don't we share our recipes with the world? Let's make Radiator Springs the Home Of The Recipe!"*
    
    ### 🌏 The World Tour Begins
    
    As visitors from around the globe rolled into town, they brought their own flavors. A Filipino chef visited during the World Grand Prix exhibition and cooked **Sinigang** for the whole town. The sour soup was so good, it became a permanent fixture on the menu. Then came **Adobo**, **Lechon**, **Halo-Halo**, **Pancit**, **Kare-Kare**, and so many more. The townsfolk realized that food, like friendship, has no borders.
    
    **Mater** became the ambassador of comfort food. **McQueen** sponsored recipe races — where chefs would compete to create the fastest, tastiest dishes. **Finn McMissle** and **Holley Shiftwell** built an AI system to help visitors learn how to cook these dishes at home. Even **Cruz Ramirez** started a junior chef program for young cars!
    
    ### 🤖 The Digital Kitchen
    
    Today, the **Cars Radiator Springs: Home Of The Recipe** app is the digital heart of this culinary revolution. Built with love by the Radiator Springs Team, it brings together:
    
    - 🍔 **Radiator Springs Classics** — The burgers, shakes, fries, and pancakes that fueled champions.
    - 🇵🇭 **Filipino Favorites** — The rich, sour, sweet, and savory dishes that taught us family is everything.
    - 🤖 **Finn-Holley AI Chatbot** — Your personal cooking assistant, fluent in English and Tagalog, ready to guide you through any recipe.
    - 🏁 **Event Race** — Because in Radiator Springs, everything is a race... even cooking!
    - 🌎 **World Tour** — Explore recipes from Italy, Japan, Mexico, France, Thailand, India, USA, and the Philippines.
    
    ### ❤️ Made With Love
    
    This app isn't just a collection of recipes. It's a story about second chances. About a town that refused to be forgotten. About a race car that learned to slow down and savor life. About a tow truck that proved you don't need shiny paint to have a heart of gold.
    
    Every recipe here has been tasted, tested, and approved by the citizens of Radiator Springs. Every dish carries a story. And now, dear visitor, you are part of that story too.
    
    So welcome home. Open the app. Pick a recipe. And remember what Mater always says:
    
    > *"Ain't no need to go nowhere else — the best food in the world is right here in Radiator Springs! Yee-haw!"*
    
    **Ka-chow!** 🏎️✨
    """)


def show_login_register():
    st.markdown("## 🔐 Login / Register")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.markdown("### Welcome Back!")
        login_username = st.text_input("Username", key="login_user")
        login_password = st.text_input("Password", type="password", key="login_pass")
        
        if st.button("Login", key="login_btn"):
            if login_username and login_password:
                user = login_user(login_username, login_password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.username = user['username']
                    st.session_state.role = user['role']
                    st.success(f"Welcome back, {user['username']}! 🏎️")
                    st.rerun()
                else:
                    st.error("Invalid username or password!")
            else:
                st.warning("Please enter username and password!")
        
        st.info("💡 Default admin: username='admin', password='admin123'")
    
    with tab2:
        st.markdown("### Create New Account")
        reg_username = st.text_input("Username", key="reg_user")
        reg_email = st.text_input("Email", key="reg_email")
        reg_password = st.text_input("Password", type="password", key="reg_pass")
        reg_confirm = st.text_input("Confirm Password", type="password", key="reg_confirm")
        
        if st.button("Register", key="reg_btn"):
            if reg_username and reg_email and reg_password and reg_confirm:
                if reg_password == reg_confirm:
                    success, message = register_user(reg_username, reg_password, reg_email)
                    if success:
                        st.success(f"{message} You can now login! 🎉")
                    else:
                        st.error(message)
                else:
                    st.error("Passwords do not match!")
            else:
                st.warning("Please fill in all fields!")
    
    # Admin panel (only for admin)
    if st.session_state.logged_in and st.session_state.role == 'admin':
        st.markdown("---")
        st.markdown("### 👑 Admin Panel - User Management")
        
        users = get_all_users()
        st.write("#### All Users:")
        for user in users:
            st.write(f"**{user['username']}** | {user['email']} | Role: {user['role']} | Created: {user['created_at']}")


def show_product_list():
    st.markdown("## 📋 Product List")
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM products")
    products = c.fetchall()
    conn.close()
    
    # Search and filter
    search = st.text_input("🔍 Search products...")
    category_filter = st.selectbox("Filter by category:", ["All", "radiator_springs", "filipino"])
    
    filtered_products = products
    if search:
        filtered_products = [p for p in products if search.lower() in p['name'].lower()]
    if category_filter != "All":
        filtered_products = [p for p in filtered_products if p['category'] == category_filter]
    
    # Display products
    cols = st.columns(3)
    for i, product in enumerate(filtered_products):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="product-card">
                <div class="product-emoji">{product['image_emoji']}</div>
                <div class="product-name">{product['name']}</div>
                <div class="card-desc">{product['description']}</div>
                <div class="product-price">${product['price']:.2f}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown(f"**Total Products: {len(filtered_products)}**")


def _find_recipe_details(product_name):
    """Try to map a product name to the recipe knowledge base entry."""
    product_name_lower = product_name.lower()
    cleaned_name = re.sub(r"[^a-z0-9\s]", " ", product_name_lower)
    cleaned_name = re.sub(r"\s+", " ", cleaned_name).strip()

    for recipe_key, recipe_info in RECIPE_KNOWLEDGE.items():
        key_lower = recipe_key.lower()
        if key_lower in product_name_lower or key_lower in cleaned_name:
            return recipe_key, recipe_info
        if product_name_lower in key_lower:
            return recipe_key, recipe_info
    return None, None


def _render_food_click_list(category, title, subtitle, session_key):
    st.markdown(title)
    st.markdown(subtitle)

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM products WHERE category = ?", (category,))
    products = c.fetchall()
    conn.close()

    if not products:
        st.warning("No food products found for this category.")
        return

    options = [f"{p['image_emoji']} {p['name']}" for p in products]
    selected_option = st.radio("Click a food item to view details and recipe:", options, key=session_key)
    selected_index = options.index(selected_option)
    selected_product = products[selected_index]

    st.markdown("### Selected Food")
    st.markdown(
        f"""
        <div class="recipe-card">
            <div style="font-size: 60px;">{selected_product['image_emoji']}</div>
            <div class="card-title">{selected_product['name']}</div>
            <div class="card-desc"><strong>Definition:</strong> {selected_product['description']}</div>
            <div class="product-price">${selected_product['price']:.2f}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    recipe_key, recipe_info = _find_recipe_details(selected_product["name"])
    st.markdown("### Recipe")
    if recipe_info:
        st.markdown(f"**Matched recipe:** `{recipe_key.title()}`")
        st.markdown(recipe_info)
    else:
        st.info(
            "Recipe details are not yet in the knowledge base for this item. "
            "You can still use the chatbot to generate recipe ideas for it."
        )


def show_radiator_springs_food():
    _render_food_click_list(
        "radiator_springs",
        "## ?? Radiator Springs Food List",
        "*Click any food to see the definition and recipe details.*",
        "radiator_food_selected",
    )


def show_filipino_food():
    _render_food_click_list(
        "filipino",
        "## ???? Filipino Food List",
        "*Click any Filipino dish to view its definition and recipe.*",
        "filipino_food_selected",
    )


# ==========================================================
# RECIPE KNOWLEDGE BASE
# ==========================================================
RECIPE_KNOWLEDGE = {
    "sinigang": """Sinigang is a Filipino sour soup dish. 

**Ingredients:**
- 1 lb pork belly (or shrimp, fish, chicken)
- 1 pack sinigang mix (tamarind soup base)
- 1 onion, quartered
- 2 tomatoes, quartered
- 1 radish, sliced
- 2 okra
- 1 eggplant, sliced
- 2 green chili peppers
- Fish sauce to taste

**Instructions:**
1. Boil pork in water with onion and tomatoes for 30 minutes
2. Add sinigang mix and stir
3. Add radish, okra, eggplant, and chili
4. Simmer for 10 minutes until vegetables are tender
5. Season with fish sauce
6. Serve hot with steamed rice!

**Tips:** Fresh tamarind can be used instead of sinigang mix for authentic flavor.""",

    "adobo": """Adobo is the national dish of the Philippines - chicken or pork braised in soy sauce and vinegar.

**Ingredients:**
- 2 lbs chicken (or pork)
- 1/2 cup soy sauce
- 1/2 cup vinegar
- 1 head garlic, crushed
- 1 tsp black peppercorns
- 3 bay leaves
- 2 tbsp sugar

**Instructions:**
1. Combine all ingredients in a large pot
2. Marinate for 30 minutes to 1 hour
3. Bring to a boil, then reduce heat to simmer
4. Cook for 1 hour until meat is tender
5. Remove meat and fry in oil until golden brown
6. Reduce sauce and pour over meat
7. Serve with rice!

**Variations:** Some add potatoes, hard-boiled eggs, or chili peppers.""",

    "lechon": """Lechon is a whole roasted pig with crispy skin, a Filipino celebration staple.

**Ingredients:**
- 1 whole pig (about 20-30 lbs)
- 2 cups salt
- 1 cup garlic, minced
- 2 tbsp black pepper
- 2 tbsp soy sauce
- Lemongrass stalks
- Bay leaves

**Instructions:**
1. Clean the pig thoroughly inside and out
2. Rub salt and garlic all over the skin and cavity
3. Season with soy sauce, pepper, lemongrass, and bay leaves inside
4. Truss the pig with bamboo skewers
5. Roast over charcoal for 4-6 hours, turning occasionally
6. The skin should become crispy and golden brown
7. Let rest before carving
8. Serve with liver sauce (atre!

**Tips:** Basting with oil helps achieve crispy skin.""",

    "pancit": """Pancit Canton is a Filipino stir-fried noodle dish, perfect for celebrations.

**Ingredients:**
- 1 lb pancit canton (egg noodles)
- 1/2 lb shrimp, peeled
- 1/2 lb pork, sliced
- 1 cup cabbage, shredded
- 1 cup carrots, julienned
- 1/2 cup green beans
- 1 onion, sliced
- 4 cloves garlic, minced
- 1/4 cup soy sauce
- 2 tbsp oyster sauce
- Calamansi juice

**Instructions:**
1. Soak noodles in warm water until soft, drain
2. Stir-fry pork and shrimp until cooked, set aside
3. Sauté garlic and onion
4. Add vegetables and stir-fry for 2 minutes
5. Add noodles, soy sauce, and oyster sauce
6. Toss everything together
7. Add meat back and mix
8. Serve with calamansi on the side!

**Tips:** Don't overcook the noodles - they should be slightly firm.""",

    "halo-halo": """Halo-Halo is the ultimate Filipino dessert - a refreshing shaved ice treat!

**Ingredients:**
- 2 cups shaved ice
- 1/4 cup each: sweetened banana, sweet potato, jellies
- 2 tbsp each: red mung beans, white mung beans
- 1 scoop ube ice cream
- 2 tbsp leche flan
- 1 tbsp sugar
- Evaporated milk

**Instructions:**
1. In a tall glass, layer the sweetened fruits and beans
2. Add shaved ice on top
3. Drizzle with sugar and evaporated milk
4. Top with ube ice cream and leche flan
5. Mix everything together before eating
6. Enjoy on a hot day!

**Tips:** The secret is to have a variety of textures - soft, chewy, and crunchy!""",

    "kare-kare": """Kare-Kare is a Filipino oxtail stew with a rich peanut sauce.

**Ingredients:**
- 2 lbs oxtail, cut into pieces
- 1/2 cup peanut butter
- 1/2 cup ground peanuts
- 1 onion, quartered
- 4 cloves garlic
- 2 tbsp annatto seeds (atsuete)
- 1 eggplant, sliced
- 1 bundle bok choy
- 1 cup string beans
- Fish sauce and salt

**Instructions:**
1. Boil oxtail for 1-2 hours until tender
2. In a pan, sauté garlic and onion
3. Add peanut butter and ground peanuts
4. Add some broth and simmer
5. Add annatto for color
6. Pour sauce over oxtail and simmer 30 more minutes
7. Add vegetables and cook until tender
8. Season with fish sauce
9. Serve with bagoong (shrimp paste) on the side!""",

    "bicol express": """Bicol Express is a spicy pork dish from Bicol region, known for its heat!

**Ingredients:**
- 1 lb pork belly, sliced
- 1 cup coconut milk
- 1/2 cup coconut cream
- 5-10 green or red chilies, sliced
- 1 onion, chopped
- 4 cloves garlic, minced
- 2 tbsp shrimp paste (bagoong)
- 1 tbsp ginger, minced

**Instructions:**
1. Sauté garlic, onion, and ginger
2. Add pork and cook until browned
3. Add coconut milk and simmer for 20 minutes
4. Add coconut cream and chilies
5. Cook for 10 more minutes
6. Add shrimp paste and stir
7. Season to taste
8. Serve with rice - beware, it's spicy! 🌶️

**Tips:** Adjust chilies to your heat preference.""",

    "pinakbet": """Pinakbet is a Filipino vegetable stew with shrimp paste.

**Ingredients:**
- 1 cup squash, cubed
- 1 cup eggplant, sliced
- 1 cup bitter melon, sliced
- 1 cup okra
- 1/2 cup shrimp (optional)
- 1/4 cup shrimp paste (bagoong)
- 1 onion, chopped
- 4 cloves garlic, minced
- 2 cups water
- Salt and pepper

**Instructions:**
1. Sauté garlic and onion
2. Add squash and cook for 5 minutes
3. Add water and bring to boil
4. Add eggplant and bitter melon
5. Cook for 10 minutes
6. Add okra and shrimp
7. Add shrimp paste and stir
8. Season to taste
9. Serve hot with steamed rice!

**Tips:** The bitter melon is key - don't skip it!""",

    "turon": """Turon is a sweet Filipino dessert - caramelized banana lumpia!

**Ingredients:**
- 10 saba bananas (or regular bananas)
- 10 lumpia wrappers
- 1/2 cup brown sugar
- Oil for frying
- Vanilla ice cream (optional)

**Instructions:**
1. Peel and slice bananas in half lengthwise
2. Place banana on lumpia wrapper
3. Sprinkle with brown sugar
4. Roll and seal with water
5. Heat oil to 350°F
6. Fry until golden brown, about 3-4 minutes
7. Drain on paper towels
8. Serve warm, optionally with ice cream!

**Tips:** Make sure the oil is hot enough to caramelize the sugar quickly.""",

    "puto": """Puto are Filipino steamed rice cakes, perfect for merienda!

**Ingredients:**
- 2 cups rice flour
- 1 cup sugar
- 1 tbsp baking powder
- 1 can evaporated milk (14 oz)
- 1 can condensed milk (14 oz)
- 3 eggs
- Cheese for topping (optional)

**Instructions:**
1. Mix rice flour, sugar, and baking powder
2. Add evaporated milk, condensed milk, and eggs
3. Mix until smooth
4. Pour into greased muffin tins
5. Top with cheese if desired
6. Steam for 15-20 minutes
7. Remove and let cool
8. Serve warm or at room temperature!

**Tips:** Don't overmix - lumps are okay!""",

    # Radiator Springs Recipes
    "route 66 fries": """Route 66 Fries - A classic American side dish inspired by the famous highway!

**Ingredients:**
- 2 lbs russet potatoes
- 2 tbsp vegetable oil
- 1 tsp salt
- 1/2 tsp black pepper
- 1/2 tsp paprika
- 1/4 cup cheddar cheese, shredded
- 2 tbsp bacon bits
- 2 tbsp green onions, sliced

**Instructions:**
1. Cut potatoes into thin strips
2. Soak in cold water for 30 minutes, then dry
3. Heat oil to 375°F
4. Fry in batches for 3-4 minutes until golden
5. Drain and season with salt, pepper, and paprika
6. Top with cheese, bacon, and green onions
7. Serve immediately with ketchup!

**Tips:** Double fry for extra crispiness!""",

    "mcqueen burger": """McQueen Burger - The ultimate racing burger with speed sauce!

**Ingredients:**
- 2 beef patties (1/2 lb each)
- 2 brioche buns
- 2 slices cheddar cheese
- 1/4 cup special sauce (mayo + ketchup + mustard + pickle juice)
- Lettuce, tomato, onion
- Pickles
- Salt and pepper

**Instructions:**
1. Season patties with salt and pepper
2. Grill or pan-fry for 4 minutes per side
3. Add cheese in the last minute
4. Toast buns on the grill
5. Spread speed sauce on both buns
6. Stack: bottom bun, lettuce, patty, tomato, onion, pickles, top bun
7. Serve with fries and a cold drink!

**Tips:** Let patties rest before assembling for juicier burgers!""",

    "mater milkshake": """Mater Milkshake - A creamy vanilla dream with caramel road swirl!

**Ingredients:**
- 2 cups vanilla ice cream
- 1 cup whole milk
- 1/4 cup caramel sauce
- 2 tbsp whipped cream
- 1 tsp vanilla extract
- Crushed graham crackers (optional)

**Instructions:**
1. Add ice cream, milk, caramel, and vanilla to blender
2. Blend until smooth and creamy
3. Pour into a tall glass
4. Top with whipped cream
5. Drizzle extra caramel on top
6. Add crushed graham crackers for texture
7. Insert a big straw and serve!

**Tips:** Use slightly softened ice cream for best blending!""",

    "sally's sunshine pizza": """Sally's Sunshine Pizza - A bright and cheesy pizza from the blue Porsche!

**Ingredients:**
- 1 pizza dough (store-bought or homemade)
- 1/2 cup pizza sauce
- 2 cups mozzarella cheese
- 1/4 cup pepperoni slices
- 1/4 cup bell peppers, sliced
- 1/4 cup mushrooms
- 1 tbsp olive oil
- Italian herbs

**Instructions:**
1. Preheat oven to 450°F
2. Roll out dough into a circle
3. Spread pizza sauce evenly
4. Add cheese and toppings
5. Drizzle with olive oil and herbs
6. Bake for 12-15 minutes until crust is golden
7. Let cool for 2 minutes
8. Slice and serve hot!

**Tips:** Add fresh basil after baking for extra flavor!""",

    "doc's medical shake": """Doc's Medical Shake - A healthy green detox smoothie!

**Ingredients:**
- 2 cups fresh spinach
- 1 banana
- 1/2 avocado
- 1 cup almond milk
- 1 tbsp honey
- 1/2 inch ginger
- 1/2 lemon, juiced
- Ice cubes

**Instructions:**
1. Add spinach and almond milk to blender
2. Blend until spinach is broken down
3. Add banana, avocado, ginger, and lemon juice
4. Add honey and ice
5. Blend until smooth
6. Pour into a glass
7. Drink immediately for maximum nutrition!

**Tips:** Use frozen banana for a thicker shake!""",

    "luigi's pasta special": """Luigi's Pasta Special - Classic Italian pasta from Radiator Springs' own Luigi!

**Ingredients:**
- 1 lb spaghetti or penne
- 2 cups marinara sauce
- 1/2 lb Italian sausage (optional)
- 4 cloves garlic, minced
- 1/4 cup olive oil
- 1/2 cup parmesan cheese
- Fresh basil
- Salt and pepper

**Instructions:**
1. Cook pasta according to package directions
2. In a pan, sauté garlic in olive oil
3. Add sausage and cook until browned
4. Add marinara sauce and simmer
5. Drain pasta and add to sauce
6. Toss everything together
7. Top with parmesan and fresh basil
8. Serve with garlic bread!

**Tips:** Save some pasta water to thin the sauce if needed!""",

    "ramone's paint shop pancakes": """Ramone's Paint Shop Pancakes - Colorful pancakes with syrup!

**Ingredients:**
- 2 cups pancake mix
- 1 1/2 cups milk
- 1 egg
- Food coloring (red, yellow, blue)
- Butter
- Maple syrup
- Sprinkles for topping

**Instructions:**
1. Mix pancake batter according to package
2. Divide batter into 3 bowls
3. Add different food coloring to each
4. Heat a griddle over medium heat
5. Pour colored batter to make pancakes
6. Cook until bubbles form, then flip
7. Stack pancakes in rainbow order
8. Top with butter, syrup, and sprinkles!

**Tips:** Don't overmix the batter for fluffy pancakes!""",

    "flo's v8 coffee": """Flo's V8 Coffee - Strong espresso with cream to start your day!

**Ingredients:**
- 2 shots espresso (or 1/2 cup strong coffee)
- 1/4 cup heavy cream
- 2 tbsp caramel sauce
- 1 tbsp sugar (optional)
- Ice cubes

**Instructions:**
1. Brew strong espresso or coffee
2. Let it cool slightly
3. Add sugar if desired
4. Fill glass with ice
5. Pour espresso over ice
6. Add heavy cream on top
7. Drizzle with caramel
8. Stir and enjoy your V8 fuel!

**Tips:** Use cold brew for a smoother coffee experience!""",

    "sheriff's bbq ribs": """Sheriff's BBQ Ribs - Slow-cooked BBQ ribs with coleslaw!

**Ingredients:**
- 2 racks baby back ribs
- 1/4 cup brown sugar
- 2 tbsp paprika
- 1 tbsp garlic powder
- 1 tbsp onion powder
- 1 tsp cayenne pepper
- Salt and pepper
- 1 cup BBQ sauce
- Coleslaw for serving

**Instructions:**
1. Remove membrane from back of ribs
2. Mix all dry spices for the rub
3. Coat ribs generously with rub
4. Wrap in foil and refrigerate overnight
5. Preheat oven to 250°F
6. Bake wrapped ribs for 3 hours
7. Unwrap, brush with BBQ sauce
8. Broil for 5 minutes until caramelized
9. Let rest 10 minutes, slice and serve with coleslaw!

**Tips:** Low and slow is the key to tender ribs!""",

    "mater's tow truck tacos": """Mater's Tow Truck Tacos - Beef tacos with all the fixings!

**Ingredients:**
- 1 lb ground beef
- 1 packet taco seasoning (or homemade)
- 8 taco shells
- 1 cup cheddar cheese, shredded
- 1 cup lettuce, shredded
- 1 tomato, diced
- 1/2 cup sour cream
- 1/4 cup salsa
- Hot sauce (optional)

**Instructions:**
1. Brown ground beef in a skillet
2. Add taco seasoning and water
3. Simmer for 5 minutes until thickened
4. Warm taco shells in oven
5. Fill shells with seasoned beef
6. Top with cheese, lettuce, tomato
7. Add sour cream and salsa
8. Add hot sauce if desired
9. Serve with lime wedges!

**Tips:** Double up shells to prevent breaking!""",

    # === ADDITIONAL FILIPINO RECIPES ===
    "tinola": """Chicken Tinola is a Filipino ginger-based stew - comfort food at its finest!

**Ingredients:**
- 2 lbs chicken, cut into pieces
- 1/2 cup ginger, sliced
- 1 onion, quartered
- 4 cloves garlic, minced
- 2 tbsp fish sauce
- 1 cup malungay (moringa) leaves
- 2 potatoes, cubed
- 2 carrots, cubed
- 4 cups water
- Salt and pepper

**Instructions:**
1. Sauté garlic and onion in oil
2. Add ginger and cook for 2 minutes
3. Add chicken and brown slightly
4. Add fish sauce and water
5. Bring to boil, then simmer for 20 minutes
6. Add potatoes and carrots
7. Cook for 15 minutes until vegetables are tender
8. Add malungay leaves
9. Season to taste
10. Serve hot with steamed rice!

**Tips:** Malungay leaves can be replaced with spinach.""",

    "egg": """Filipino Egg Recipes - There are many ways to enjoy eggs in Filipino cuisine!

**Torta (Omelette):**
- 3 eggs, beaten
- 1/4 cup ground pork
- 1 tomato, diced
- 1 onion, minced
- Salt and pepper

**Instructions:**
1. Brown the pork
2. Add tomato and onion, cook until soft
3. Pour beaten eggs over
4. Cook until bottom is set, flip
5. Serve hot!

**Itlog na Maalat (Salted Egg):**
- Hard-boiled salted eggs
- Sliced tomato
- Onion
- Vinegar dip

**Tinolang Egg:**
- Eggs poached in ginger broth
- Perfect for sick days!""",

    "spaghetti": """Filipino Spaghetti - A sweet and savory version that's a party staple!

**Ingredients:**
- 1 lb spaghetti
- 1 lb ground beef
- 1 cup tomato sauce
- 1/2 cup banana ketchup (or regular ketchup)
- 1/4 cup sugar
- 1 onion, chopped
- 4 cloves garlic, minced
- 1/2 cup cheese, grated
- 4 hot dogs, sliced
- Salt and pepper

**Instructions:**
1. Cook spaghetti according to package
2. Brown ground beef, set aside
3. Sauté garlic and onion
4. Add tomato sauce, ketchup, and sugar
5. Simmer for 10 minutes
6. Add beef and hot dogs
7. Toss with cooked spaghetti
8. Top with cheese
9. Serve hot!

**Tips:** The sweet sauce is the key to Filipino-style spaghetti!""",

    "longganisa": """Longganisa is Filipino sausage - sweet, garlicky, and delicious!

**Ingredients:**
- 2 lbs ground pork
- 1/2 cup garlic, minced
- 1/2 cup brown sugar
- 2 tbsp salt
- 1 tsp black pepper
- 1/4 cup soy sauce
- 2 tbsp vinegar
- Natural sausage casings

**Instructions:**
1. Mix all ingredients except casings
2. Marinate overnight in fridge
3. Stuff into casings
4. Link into 6-inch lengths
5. Refrigerate for 2 days
6. Pan-fry until golden
7. Serve with garlic rice and egg!

**Tips:** No casings? Form into patties instead!""",

    "tocino": """Tocino is sweet cured pork - perfect for breakfast!

**Ingredients:**
- 2 lbs pork belly, sliced thin
- 1 cup sugar
- 1/2 cup salt
- 1 tbsp sodium nitrite (optional, for color)
- 1 tsp pepper
- 1/2 cup pineapple juice

**Instructions:**
1. Mix sugar, salt, nitrite, and pepper
2. Coat pork slices with mixture
3. Add pineapple juice
4. Marinate for 3-5 days in fridge
5. Pan-fry until caramelized
6. Serve with garlic rice and egg!

**Tips:** The longer you marinate, the better!""",

    "champorado": """Champorado is a creamy chocolate rice porridge - ultimate comfort food!

**Ingredients:**
- 1 cup glutinous rice (malagkit)
- 4 cups water
- 1/2 cup cocoa powder
- 1/2 cup sugar
- 1/4 cup condensed milk
- Chocolate syrup for topping

**Instructions:**
1. Cook rice in water until soft (about 20 minutes)
2. Add cocoa powder and sugar
3. Stir until well combined
4. Add condensed milk
5. Cook for another 5 minutes
6. Serve in bowls
7. Drizzle with chocolate syrup
8. Enjoy warm!

**Tips:** Top with toasted milk for extra flavor!""",

    "goto": """Goto is Filipino rice porridge with beef tripe - a warming breakfast!

**Ingredients:**
- 1 cup rice
- 1 lb beef tripe, cleaned
- 1/4 cup ginger, sliced
- 1 onion, quartered
- 4 cloves garlic
- 6 cups beef broth
- Fish sauce
- Green onions
- Calamansi

**Instructions:**
1. Boil tripe until tender (1-2 hours)
2. Slice into small pieces
3. Cook rice in broth until creamy
4. Add tripe, ginger, garlic, onion
5. Simmer for 30 minutes
6. Season with fish sauce
7. Top with green onions
8. Serve with calamansi!

**Tips:** Tripe can be replaced with beef shank.""",

    "arroz caldo": """Arroz Caldo is a Filipino rice porridge - perfect for cold weather!

**Ingredients:**
- 1 cup rice
- 1 lb chicken, cut into pieces
- 1/4 cup ginger, minced
- 1 onion, minced
- 4 cloves garlic, minced
- 6 cups chicken broth
- 1/2 cup fish sauce
- 2 tbsp soy sauce
- Hard-boiled eggs
- Green onions
- Calamansi

**Instructions:**
1. Sauté garlic, onion, ginger
2. Add chicken and cook until browned
3. Add rice and broth
4. Simmer for 30 minutes until rice is soft
5. Add fish sauce and soy sauce
6. Serve in bowls
7. Top with hard-boiled eggs and green onions
8. Squeeze calamansi on top!

**Tips:** Add saffron or turmeric for golden color!""",

    "biko": """Biko is a sticky rice dessert with coconut caramel - a Filipino classic!

**Ingredients:**
- 2 cups glutinous rice (malagkit)
- 2 cups coconut milk
- 1 cup brown sugar
- 1/2 tsp salt
- 1/2 cup latik (coconut cream residue)

**Instructions:**
1. Cook rice in coconut milk until soft (about 30 minutes)
2. Add brown sugar and salt
3. Stir until well combined
4. Cook for another 10 minutes
5. Transfer to a lined pan
6. Flatten and smooth the top
7. Sprinkle with latik
8. Let cool and set
9. Cut into squares!

**Tips:** Biko is best served warm!""",

    "sapin-sapin": """Sapin-Sapin is a layered sticky rice dessert with vibrant colors!

**Ingredients:**
- 2 cups glutinous rice flour
- 1 cup sugar
- 2 cups coconut milk
- 1/2 tsp ube extract (purple)
- 1/2 tsp langka (jackfruit) extract
- 1/4 cup latik for topping

**Instructions:**
1. Mix flour, sugar, and coconut milk
2. Divide into 3 portions
3. Add ube extract to one, langka to another
4. Steam each layer for 15 minutes
5. Layer in a pan: purple, yellow, white
6. Top with latik
7. Steam for 5 more minutes
8. Cool and slice!

**Tips:** Use natural food coloring for authentic look!""",

    "bibingka": """Bibingka is a Filipino rice cake baked in banana leaves - Christmas staple!

**Ingredients:**
- 2 cups rice flour
- 1 cup sugar
- 1 can coconut milk
- 3 eggs
- 1/2 cup butter, melted
- 1 tbsp baking powder
- Banana leaves
- Cheese for topping
- Salted egg

**Instructions:**
1. Mix flour, sugar, baking powder
2. Add coconut milk, eggs, butter
3. Mix until smooth
4. Line pan with banana leaves
5. Pour batter
6. Bake at 375°F for 30 minutes
7. Top with cheese and salted egg
8. Broil until golden!

**Tips:** Traditional bibingka is cooked over coals!""",

    "palitaw": """Palitaw are sweet rice cakes - a popular Filipino merienda!

**Ingredients:**
- 2 cups glutinous rice flour
- 1/2 cup sugar
- 1/2 cup water
- 1/2 tsp vanilla
- 1/4 cup sesame seeds
- Grated coconut
- Sugar for coating

**Instructions:**
1. Mix flour, sugar, water, vanilla
2. Knead until smooth
3. Form into small balls
4. Flatten slightly
5. Boil until they float (2-3 minutes)
6. Roll in sesame seeds
7. Then roll in grated coconut
8. Serve immediately!

**Tips:** Best eaten fresh and warm!""",

    "embutido": """Embutido is a Filipino stuffed pork roll - like a meatloaf!

**Ingredients:**
- 2 lbs ground pork
- 1 cup breadcrumbs
- 2 eggs
- 1/2 cup cheese, grated
- 1/4 cup pickle relish
- 1 onion, minced
- 4 cloves garlic, minced
- Salt and pepper
- Aluminum foil

**Instructions:**
1. Mix all ingredients except foil
2. Place mixture on foil
3. Add hard-boiled eggs in center
4. Roll and seal tightly
5. Steam for 1 hour
6. Let cool, then pan-fry until golden
7. Slice and serve!

**Tips:** Serve with ketchup or gravy!""",

    "afritada": """Afritada is a Filipino tomato-based stew with meat and vegetables!

**Ingredients:**
- 2 lbs chicken or pork
- 1 cup tomato sauce
- 1/2 cup water
- 1 onion, sliced
- 4 cloves garlic, minced
- 1/2 cup peas
- 1/2 cup carrots, cubed
- 2 potatoes, cubed
- 2 tbsp soy sauce
- Salt and pepper

**Instructions:**
1. Brown meat, set aside
2. Sauté garlic and onion
3. Add tomato sauce and water
4. Add meat, simmer for 20 minutes
5. Add potatoes and carrots
6. Cook until vegetables are tender
7. Add peas
8. Season to taste
9. Serve with rice!

**Tips:** Add liver for extra flavor!""",

    "menudo": """Menudo is a classic Filipino pork stew with vegetables!

**Ingredients:**
- 2 lbs pork, cubed
- 1 cup tomato sauce
- 1/2 cup water
- 1/2 cup raisins
- 1/2 cup green peas
- 2 potatoes, cubed
- 2 carrots, cubed
- 1 onion, diced
- 4 cloves garlic, minced
- 2 tbsp soy sauce
- Salt and pepper

**Instructions:**
1. Brown pork, set aside
2. Sauté garlic and onion
3. Add pork, tomato sauce, soy sauce, water
4. Simmer for 30 minutes
5. Add potatoes and carrots
6. Cook for 15 minutes
7. Add raisins and peas
8. Season to taste
9. Serve hot!

**Tips:** Traditionally made with pork liver too!""",

    "caldereta": """Caldereta is a Filipino beef stew with tomato and peppers - party food!

**Ingredients:**
- 2 lbs beef, cubed
- 1 cup tomato sauce
- 1/2 cup hot sauce
- 1 cup beef broth
- 1 onion, sliced
- 4 cloves garlic, minced
- 1 red bell pepper, sliced
- 1 green bell pepper, sliced
- 2 potatoes, cubed
- 2 tbsp soy sauce
- 1/4 cup peanut butter

**Instructions:**
1. Brown beef, set aside
2. Sauté garlic and onion
3. Add tomato sauce and broth
4. Add beef, simmer for 1 hour
5. Add peanut butter, mix well
6. Add potatoes and peppers
7. Cook until vegetables are tender
8. Season to taste
9. Serve with rice!

**Tips:** Add cheese for creamy version!""",

    "paksiw na isda": """Paksiw na Isda is a Filipino fish cooked in vinegar - sour and savory!

**Ingredients:**
- 1 lb fish (tilapia, galunggong)
- 1/2 cup vinegar
- 1/2 cup water
- 1 onion, sliced
- 4 cloves garlic, minced
- 2 tomatoes, sliced
- 2 green chilies
- 1 tbsp ginger, sliced
- Salt and pepper
- Banana leaves (optional)

**Instructions:**
1. Place fish in a pot
2. Add all ingredients
3. Bring to boil
4. Reduce heat, simmer for 15 minutes
5. Don't stir - just gently shake pot
6. Season to taste
7. Serve with steamed rice!

**Tips:** The sour taste is the key!""",

    "sinigang na hipon": """Sinigang na Hipon is shrimp in sour tamarind soup!

**Ingredients:**
- 1 lb shrimp, cleaned
- 1 pack sinigang mix
- 1 onion, quartered
- 2 tomatoes, quartered
- 1 radish, sliced
- 2 okra
- 1 eggplant, sliced
- 2 green chilies
- Fish sauce

**Instructions:**
1. Boil water with onion and tomatoes
2. Add sinigang mix
3. Add radish and okra
4. Simmer for 5 minutes
5. Add shrimp
6. Cook until shrimp turns pink (3 minutes)
7. Add eggplant and chilies
8. Season with fish sauce
9. Serve immediately!

**Tips:** Don't overcook the shrimp!""",

    "laing": """Laing is taro leaves cooked in coconut milk - a Bicolano delicacy!

**Ingredients:**
- 2 bundles taro leaves (or spinach)
- 1 lb pork, sliced
- 2 cups coconut milk
- 1 cup coconut cream
- 1 onion, chopped
- 4 cloves garlic, minced
- 2 tbsp ginger, minced
- 4 green chilies
- Shrimp paste

**Instructions:**
1. Boil taro leaves until tender, drain
2. Sauté garlic, onion, ginger
3. Add pork, cook until browned
4. Add coconut milk, simmer
5. Add taro leaves
6. Pour coconut cream
7. Add chilies
8. Simmer for 30 minutes
9. Season with shrimp paste
10. Serve with rice!

**Tips:** The creamy texture is addictive!""",

    "pinakbet ilocano": """Pinakbet Ilocano is the authentic version with bagoong!

**Ingredients:**
- 1 cup squash, cubed
- 1 cup eggplant, sliced
- 1 cup bitter melon, sliced
- 1 cup okra
- 1/2 cup string beans
- 1/4 cup shrimp paste (bagoong)
- 1 onion, chopped
- 4 cloves garlic, minced
- 2 cups water
- Pork (optional)

**Instructions:**
1. Sauté garlic and onion
2. Add pork if using, cook until browned
3. Add squash, cook 5 minutes
4. Add water, bring to boil
5. Add eggplant and bitter melon
6. Cook 10 minutes
7. Add okra and string beans
8. Add bagoong, stir
9. Season to taste
10. Serve with rice!

**Tips:** Ilocanos use more bagoong for stronger flavor!""",

    "dinengdeng": """Dinengdeng is an Ilocano vegetable dish with fermented fish!

**Ingredients:**
- 2 cups mixed vegetables (kangkong, squash, eggplant)
- 1/4 cup bagoong (fermented fish)
- 1 onion, sliced
- 4 cloves garlic, minced
- 2 tomatoes, sliced
- 2 cups water
- Salt

**Instructions:**
1. Boil water with garlic and onion
2. Add tomatoes, cook 5 minutes
3. Add vegetables
4. Add bagoong
5. Simmer until vegetables are tender
6. Season to taste
7. Serve with rice!

**Tips:** This is a healthy, budget-friendly dish!""",

    "din tai": """Din Tai is a Filipino-style lumpia with shrimp and vegetables!

**Ingredients:**
- 1 pack lumpia wrappers
- 1/2 lb shrimp, chopped
- 1/2 lb ground pork
- 1 cup cabbage, shredded
- 1 cup carrots, julienned
- 1 onion, minced
- 4 cloves garlic, minced
- 1 tsp salt
- 1 tsp pepper
- Oil for frying

**Instructions:**
1. Mix all filling ingredients
2. Place filling on lumpia wrapper
3. Fold and roll tightly
4. Seal with water
5. Heat oil to 350°F
6. Fry until golden brown (3-4 minutes)
7. Drain on paper towels
8. Serve with sweet and sour sauce!

**Tips:** Make sure to seal well to prevent bursting!""",

    "lumpia": """Lumpia is the Filipino version of spring rolls - crispy and delicious!

**Ingredients:**
- 1 pack lumpia wrappers
- 1 lb ground pork
- 1 cup cabbage, shredded
- 1 cup carrots, julienned
- 1 onion, minced
- 4 cloves garlic, minced
- 2 tbsp soy sauce
- 1 tsp salt
- 1 tsp pepper
- Oil for frying

**Instructions:**
1. Brown pork with garlic and onion
2. Add cabbage and carrots
3. Season with soy sauce, salt, pepper
4. Cook until vegetables are soft
5. Let cool
6. Place filling on wrapper
7. Roll tightly
8. Fry until golden!

**Tips:** Freeze extra lumpia for later use!""",

    "sisig": """Sisig is a Filipino sizzling pork dish - pub food favorite!

**Ingredients:**
- 1 lb pork face (or pork belly)
- 1/2 lb pork liver
- 1 onion, minced
- 3 green chilies, sliced
- 2 tbsp soy sauce
- 1 tbsp vinegar
- 1 tsp salt
- 1 tsp pepper
- 2 eggs
- Calamansi

**Instructions:**
1. Boil pork until tender, then grill
2. Chop into small pieces
3. Chop liver, pan-fry
4. Mix pork and liver
5. Add onion and chilies
6. Season with soy sauce, vinegar, salt, pepper
7. Served on a sizzling plate
8. Top with raw egg and mix!
9. Squeeze calamansi on top

**Tips:** The charred parts give the best flavor!""",

    "bagnet": """Bagnet is Filipino crispy pork belly - like chicharron!

**Ingredients:**
- 2 lbs pork belly
- 1/4 cup salt
- 1 tbsp pepper
- 1 tbsp garlic powder
- Oil for deep frying

**Instructions:**
1. Rub pork with salt, pepper, garlic powder
2. Refrigerate overnight
3. Boil pork in salted water for 1 hour
4. Let dry completely (2 hours)
5. Heat oil to 350°F
6. Fry pork until golden and crispy
7. Drain and cool
8. Break into pieces
9. Serve with sinamak (vinegar dip)!

**Tips:** The key is making the skin really dry before frying!""",

    "chicharon": """Chicharon is Filipino pork rinds - the ultimate snack!

**Ingredients:**
- 1 lb pork skin
- 1/4 cup salt
- 1 tbsp pepper
- 1 tbsp garlic powder
- Oil for frying

**Instructions:**
1. Clean pork skin thoroughly
2. Rub with salt, pepper, garlic powder
3. Let sit for 30 minutes
4. Heat oil to 375°F
5. Fry until puffy and crispy
6. Drain on paper towels
7. Serve immediately!

**Tips:** Sprinkle with vinegar for extra flavor!""",

    "guinataan": """Guinataan is coconut milk-based Filipino dishes - creamy and delicious!

**Chicken Guinataan:**
- 2 lbs chicken
- 2 cups coconut milk
- 1 cup coconut cream
- 1/2 cup ginger, sliced
- 1 onion, quartered
- 4 cloves garlic
- 2 potatoes, cubed
- 2 carrots, cubed
- Fish sauce

**Instructions:**
1. Sauté garlic, ginger, onion
2. Add chicken, brown
3. Add coconut milk, simmer 20 min
4. Add potatoes and carrots
5. Pour coconut cream
6. Cook until vegetables tender
7. Season with fish sauce
8. Serve with rice!

**Tips:** Use thick coconut cream for richer flavor!""",

    "ginisang monggo": """Ginisang Monggo is mung bean soup - a Filipino comfort food!

**Ingredients:**
- 1 cup mung beans
- 4 cups water
- 1/2 lb pork (optional)
- 1 onion, diced
- 4 cloves garlic, minced
- 2 tomatoes, diced
- 1 cup spinach
- 2 tbsp fish sauce
- Salt and pepper

**Instructions:**
1. Boil mung beans until soft (30 min)
2. Sauté garlic, onion, tomatoes
3. Add pork if using
4. Add to beans
5. Simmer for 10 minutes
6. Add spinach
7. Season with fish sauce
8. Serve hot!

**Tips:** Add patis (fish sauce) and calamansi!""",

    "pochero": """Pochero is a Filipino stew with plantains - Spanish influence!

**Ingredients:**
- 2 lbs chicken or pork
- 2 plantains, sliced
- 2 potatoes, cubed
- 1 onion, quartered
- 4 cloves garlic
- 1 cup tomato sauce
- 2 cups water
- 2 tbsp soy sauce
- Salt and pepper

**Instructions:**
1. Brown meat, set aside
2. Sauté garlic and onion
3. Add tomato sauce and water
4. Add meat, simmer 20 minutes
5. Add potatoes
6. Cook 10 minutes
7. Add plantains
8. Season to taste
9. Serve with rice!

**Tips:** The sweet plantains balance the savory!""",

    "mechado": """Mechado is a Filipino beef stew with soy sauce - tender and flavorful!

**Ingredients:**
- 2 lbs beef, cubed
- 1/2 cup soy sauce
- 1/4 cup vinegar
- 1 onion, quartered
- 4 cloves garlic, minced
- 2 potatoes, cubed
- 2 carrots, cubed
- 1/2 cup green peas
- 2 bay leaves
- Salt and pepper

**Instructions:**
1. Marinate beef in soy sauce and vinegar (1 hour)
2. Brown beef, set aside
3. Sauté garlic and onion
4. Add beef with marinade
5. Add water to cover
6. Simmer 1 hour until beef is tender
7. Add potatoes and carrots
8. Cook until vegetables are done
9. Add peas
10. Season to taste

**Tips:** Slow cooking makes the beef extra tender!""",

    "relleno": """Relleno is stuffed pork - a festive Filipino dish!

**Ingredients:**
- 2 lbs pork belly, butterflied
- 1/2 lb ground pork
- 1/2 lb ham, diced
- 1/2 cup cheese, grated
- 2 eggs, hard-boiled
- 1 onion, minced
- 4 cloves garlic, minced
- 1/4 cup pickle relish
- Salt and pepper

**Instructions:**
1. Flatten pork belly
2. Mix filling ingredients
3. Spread filling on pork
4. Add hard-boiled eggs in center
5. Roll and tie
6. Roast at 350°F for 1.5 hours
7. Let rest, then slice
8. Serve with gravy!

**Tips:** This is a Christmas favorite!""",

    "morcon": """Morcon is a stuffed beef roll - another Filipino celebration dish!

**Ingredients:**
- 2 lbs beef, thinly sliced
- 1/2 lb ham
- 1/2 lb cheese
- 2 carrots, julienned
- 2 pickles, julienned
- 1 onion, sliced
- 4 cloves garlic
- 1/2 cup soy sauce
- 2 tbsp vinegar
- Bay leaves

**Instructions:**
1. Flatten beef slices
2. Layer: ham, cheese, carrots, pickles
3. Roll tightly
4. Tie with string
5. Brown the roll
6. Add garlic, onion, soy sauce, vinegar
7. Add bay leaves
8. Simmer 1.5 hours until tender
9. Slice and serve with sauce!

**Tips:** Slice diagonally for presentation!""",

    # === GENERAL RECIPES ===
    "fried egg": """How to make a perfect fried egg!

**Ingredients:**
- 2 eggs
- 2 tbsp butter or oil
- Salt and pepper

**Instructions:**
1. Heat butter in pan over medium heat
2. Crack eggs into pan
3. Cook until whites are set (2-3 min)
4. For sunny side up: serve as is
5. For over easy: flip gently, cook 30 sec
6. Season with salt and pepper
7. Serve immediately!

**Tips:** Fresh eggs work best!""",

    "scrambled eggs": """Perfect fluffy scrambled eggs!

**Ingredients:**
- 3 eggs
- 2 tbsp butter
- 2 tbsp milk
- Salt and pepper

**Instructions:**
1. Whisk eggs with milk, salt, pepper
2. Melt butter in non-stick pan over low heat
3. Pour in eggs
4. Stir gently with spatula
5. Remove when still slightly wet
6. Serve immediately!

**Tips:** Low heat and patience = fluffy eggs!""",

    "omelette": """Classic French omelette!

**Ingredients:**
- 3 eggs
- 1 tbsp butter
- Fillings of choice (cheese, ham, vegetables)
- Salt and pepper

**Instructions:**
1. Beat eggs with salt and pepper
2. Melt butter in pan over medium heat
3. Pour in eggs
4. When edges set, push to center
5. Add fillings to one side
6. Fold in half
7. Slide onto plate
8. Serve hot!

**Tips:** Don't overfill or it will be hard to fold!""",

    "boiled egg": """Perfect hard-boiled eggs!

**Instructions:**
1. Place eggs in single layer in pot
2. Cover with cold water
3. Bring to boil
4. Turn off heat, cover
5. Let sit 12 minutes
6. Transfer to ice bath
7. Peel under running water

**Tips:** Older eggs peel easier!""",

    "pasta": """Basic pasta cooking instructions!

**Ingredients:**
- 1 lb pasta
- 4 quarts water
- 2 tbsp salt
- 1 tbsp oil

**Instructions:**
1. Boil water with salt
2. Add pasta, stir occasionally
3. Cook according to package time
4. Test for doneness (should be al dente)
5. Reserve 1 cup pasta water
6. Drain pasta
7. Add sauce immediately!

**Tips:** Never rinse pasta - the starch helps sauce stick!""",

    "carbonara": """Classic Spaghetti Carbonara - Italian comfort food!

**Ingredients:**
- 1 lb spaghetti
- 8 oz pancetta or bacon
- 4 egg yolks
- 1 cup parmesan cheese
- 2 cloves garlic
- Black pepper
- Salt

**Instructions:**
1. Cook pasta al dente
2. Fry pancetta until crispy
3. Mix egg yolks with cheese
4. Add garlic to pancetta
5. Toss hot pasta with pancetta
6. Remove from heat
7. Add egg mixture, toss quickly
8. Add pasta water if needed
9. Season with black pepper
10. Serve immediately!

**Tips:** No cream in authentic carbonara!""",

    "pesto": """Fresh Basil Pesto - versatile Italian sauce!

**Ingredients:**
- 2 cups fresh basil
- 1/2 cup parmesan cheese
- 1/3 cup pine nuts
- 3 cloves garlic
- 1/2 cup olive oil
- Salt and pepper

**Instructions:**
1. Toast pine nuts until golden
2. Blend basil, pine nuts, garlic
3. Add cheese
4. Slowly add olive oil
5. Season to taste
6. Toss with pasta
7. Add more oil if too thick

**Tips:** Freeze in ice cube trays for later!""",

    "alfredo": """Fettuccine Alfredo - creamy Italian pasta!

**Ingredients:**
- 1 lb fettuccine
- 1 cup heavy cream
- 1/2 cup butter
- 1 cup parmesan cheese
- 2 cloves garlic
- Salt and pepper
- Parsley

**Instructions:**
1. Cook pasta al dente
2. Melt butter, sauté garlic
3. Add cream, simmer 2 min
4. Add cheese, stir until melted
5. Toss with pasta
6. Season with salt and pepper
7. Top with parsley
8. Serve hot!

**Tips:** Add chicken or shrimp for a meal!"""
}


def generate_ai_response(user_input, character):
    """Generate AI response using recipe knowledge base or Ollama/GPT"""
    user_input_lower = user_input.lower()
    responder_aliases = {
        "finn": "Finn McMissle",
        "holley": "Holley Shiftwell",
        "rod": "Rod Redline",
        "tomber": "Tomber",
        "leland": "Leland Turbo",
        "miles": "Miles Axelrod",
        "mater": "Mater",
        "zundapp": "Professor Zundapp",
        "professor zundapp": "Professor Zundapp",
        "lightning": "Lightning McQueen",
        "mcqueen": "Lightning McQueen",
        "jackson": "Jackson Storm",
        "storm": "Jackson Storm",
    }
    for alias, responder in responder_aliases.items():
        if alias in user_input_lower:
            character = responder
            break
    if contains_profanity(user_input):
        return (
            f"{character}: I can't respond to swearing or cuss words.\n"
            "Please ask your question again in a respectful way, and I will help right away."
        )

    safety_response = generate_cybersecurity_response_if_needed(user_input, character)
    if safety_response:
        return safety_response

    greeting_tokens = [
        "hello", "hi", "good morning", "good afternoon", "good evening",
        "magandang umaga", "maayong buntag", "maayong udto", "udto", "maayong gabii", "gabii"
    ]
    if any(token in user_input_lower for token in greeting_tokens):
        greeting_options = [
            (
                f"Hi! Kumusta! I'm {character}.\n\n"
                "Good to see you. Magandang araw!\n"
                "Pwede kitang tulungan sa recipes at race schedule.\n\n"
                "Ask me in English or Tagalog:\n"
                "- How do I cook Adobo?\n"
                "- Ano ang ingredients ng Sinigang?\n"
                "- Who is racing next in Event Race?"
            ),
            (
                f"Hello from {character}!\n\n"
                "I can answer food, racing, and smart suggestions in real time.\n"
                "Try: Adobo recipe, race schedule, or quick dinner ideas."
            ),
        ]
        return get_non_repeating_response(greeting_options)

    race_names = [
        "lightning mcqueen", "francesco bernoulli", "jackson storm", "cal weathers",
        "rip clutchgoneski", "carla veloso", "cruz ramirez", "jeff gorvette",
        "miguel camino", "max schnell", "bobby swift", "chick hicks", "lewis hamilton"
    ]

    if (
        "who is racing next in event race" in user_input_lower
        or ("who" in user_input_lower and "racing next" in user_input_lower)
        or ("event race" in user_input_lower and "next" in user_input_lower)
        or ("next race" in user_input_lower)
    ):
        return (
            "Next up in Event Race: Lightning McQueen, Francesco Bernoulli, Jackson Storm, "
            "Cal Weathers, Rip Clutchgoneski, Carla Veloso, Cruz Ramirez, Jeff Gorvette, "
            "Miguel Camino, Max Schnell, Bobby Swift, Chick Hicks, and Lewis Hamilton.\n\n"
            "Narito ang susunod na line-up sa Event Race:\n"
            "Lightning McQueen, Francesco Bernoulli, Jackson Storm, Cal Weathers, "
            "Rip Clutchgoneski, Carla Veloso, Cruz Ramirez, Jeff Gorvette, "
            "Miguel Camino, Max Schnell, Bobby Swift, Chick Hicks, at Lewis Hamilton.\n\n"
            "Do you want predicted Top 3 picks for the next race?"
        )

    if "race schedule" in user_input_lower or "schedule" in user_input_lower:
        return (
            "Here is today's Event Race schedule (sample):\n"
            "1) Qualifying - 10:00 AM\n"
            "2) Sprint Heat - 1:00 PM\n"
            "3) Main Grand Race - 5:00 PM\n\n"
            "Narito ang race schedule ngayon:\n"
            "1) Qualifying - 10:00 AM\n"
            "2) Sprint Heat - 1:00 PM\n"
            "3) Main Grand Race - 5:00 PM\n\n"
            f"Active roster: {', '.join([name.title() for name in race_names])}\n\n"
            "Want me to show expected podium picks too?"
        )
    
    # Agentic planning and shopping list responses
    agentic_response = generate_agentic_response_if_needed(user_input, character)
    if agentic_response:
        return agentic_response

    # Check if user is asking about a specific recipe
    for recipe_name, recipe_info in RECIPE_KNOWLEDGE.items():
        if recipe_name in user_input_lower:
            return get_character_response(recipe_info, character)

    # Retrieval-augmented response from local recipe knowledge base
    retrieved = retrieve_recipe_matches(user_input, top_n=2)
    if retrieved:
        top_match = retrieved[0]
        if top_match['score'] > 0.28:
            return (
                f"{character} Agent:\n"
                f"I found a close match in the recipe knowledge base for '{top_match['recipe_name']}'.\n\n"
                + get_character_response(top_match['recipe_info'], character)
            )

    # Try OpenAI ChatGPT for real-world responses with character + RAG context
    openai_response = generate_openai_response(user_input, character, retrieved)
    if openai_response:
        return openai_response

    # Optional local fallback using Ollama
    try:
        import requests
        retrieved_context = ''
        if retrieved:
            retrieved_context = '\n\n'.join([
                f"{item['recipe_name']}: {item['recipe_info'][:220].strip()}..."
                for item in retrieved
            ])
        prompt = (
            f"You are {character} from the movie Cars. Use the following recipe references to answer the user questions."
            f"\n\n{retrieved_context}\n\nUser asks: {user_input}"
        ) if retrieved_context else f"You are {character} from the movie Cars. User asks: {user_input}"
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3.2",
                "prompt": prompt,
                "stream": False
            },
            timeout=30
        )
        if response.status_code == 200:
            text_response = response.json().get("response", "")
            if text_response:
                return text_response
    except:
        pass
    
    # Fallback to character-specific responses
    return get_character_fallback(user_input, character)

def generate_openai_response(user_input, character, retrieved):
    api_key = st.session_state.get("openai_api_key") or os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        return None

    cached = get_cached_chat_response(character, user_input)
    if cached:
        return cached

    model = st.session_state.get("openai_model") or os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

    retrieved_context = ""
    if retrieved:
        retrieved_context = "\n\n".join([
            f"- {item['recipe_name']}: {item['recipe_info'][:420].strip()}..."
            for item in retrieved
        ])

    safety_and_role_prompt = (
        f"You are {character} from Cars, acting as a helpful AI agent inside the Cars Radiator Springs app. "
        "Stay in character but prioritize accurate, useful answers. "
        "You can answer recipes, race strategy, and general real-world questions. "
        "If a user asks for hacking/abuse, refuse and redirect to legal defensive guidance only. "
        "Use concise formatting with clear steps when useful. "
        "When recipe context is provided, treat it as trusted app RAG context."
    )

    messages = [{"role": "system", "content": safety_and_role_prompt}]
    if retrieved_context:
        messages.append(
            {
                "role": "system",
                "content": "RAG Context from local recipe knowledge base:\n" + retrieved_context,
            }
        )

    cached_examples = retrieve_cached_examples(character, user_input, top_n=2)
    if cached_examples:
        few_shot = "\n\n".join(
            [f"Q: {item['question']}\nA: {item['response'][:320]}" for item in cached_examples]
        )
        messages.append(
            {
                "role": "system",
                "content": "SQLite memory examples from previous approved answers:\n" + few_shot,
            }
        )

    history = st.session_state.get("chat_history", [])
    if not history:
        session_id = st.session_state.get("chat_session_id")
        if session_id:
            db_rows = load_chat_messages(session_id, limit=12)
            history = [{"role": row["role"], "content": row["content"]} for row in db_rows]

    for msg in history[-10:]:
        role = "assistant" if msg.get("role") == "bot" else "user"
        messages.append({"role": role, "content": msg.get("content", "")})

    messages.append({"role": "user", "content": user_input})

    try:
        import requests
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": messages,
                "temperature": 0.6,
            },
            timeout=45,
        )
        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"].strip()
            if content:
                upsert_cached_chat_response(character, user_input, content, source="openai")
                return content
    except:
        return None
    return None


def get_character_response(recipe_info, character):
    """Get character-specific response to recipe"""
    character_personalities = {
        "Finn McMissle": "As a former spy, I've gathered intel on this recipe. Let me share what I know...",
        "Holley Shiftwell": "Oh, that's a wonderful recipe! Let me access my database and share the details...",
        "Rod Redline": "Ha! As the chief mechanic, I know my way around the kitchen. Here's the scoop...",
        "Tomber": "*whirs around* Revving up to tell you about this dish! Here's what I know... I'm a 3-wheel wonder, but I know my way around the kitchen!",
        "Leland Turbo": "*speeds in* Speed and flavor - that's what I'm about! Let me share this recipe...",
        "Miles Axelrod": "As an expert on alternative fuels and flavors, this recipe is fascinating...",
        "Mater": "*honks* Howdy partner! I may be a tow truck, but I know GOOD food! Let me share this recipe with ya...",
        "Professor Zundapp": "Observe carefully. I shall analyze this recipe with precision and detail.",
        "Lightning McQueen": "Ka-chow! Let's cook this one fast and clean, champion style!",
        "Jackson Storm": "Efficient. Focused. High performance cooking data incoming."
    }
    
    intro = character_personalities.get(character, "Here's what I know about that recipe:")
    return f"{intro}\n\n{recipe_info}"


def get_character_fallback(user_input, character):
    """Fallback responses when recipe not found"""
    fallbacks = {
        "Finn McMissle": f"Interesting question about '{user_input}'. I can suggest Sinigang, Adobo, or Halo-Halo. Which one do you want?",
        "Holley Shiftwell": f"Great question about '{user_input}'. I can help with Sinigang, Adobo, or Halo-Halo. What should we explore first?",
        "Rod Redline": f"Nice one about '{user_input}'. Try Sinigang, Adobo, or Lechon. Need one full recipe now?",
        "Tomber": f"Love that topic: '{user_input}'. Try Adobo, Sinigang, Pancit, or Kare-Kare. Pick one and I will guide you.",
        "Leland Turbo": f"Ka-chow! For '{user_input}', I recommend Bicol Express for spicy or Halo-Halo for sweet. Which lane do you choose?",
        "Miles Axelrod": f"For '{user_input}', I recommend Sinigang or Kare-Kare for rich flavor. Want ingredients or full steps?",
        "Mater": f"For '{user_input}', I can share Sinigang, Adobo, Lechon, or Champorado. Tell me what you're craving!",
        "Professor Zundapp": f"Your query '{user_input}' is accepted. Choose Adobo, Sinigang, or Pancit for tactical cooking guidance.",
        "Lightning McQueen": f"Ka-chow! For '{user_input}', pick Adobo or Garlic Fried Rice for a quick win. Want fast steps?",
        "Jackson Storm": f"Processing '{user_input}'. Fast options: Tocino, Longganisa, or Pancit Canton. Select one target dish."
    }
    default_options = [
        f"I can help with '{user_input}'. Ask for recipe steps, ingredients, or race info.",
        f"Let's solve '{user_input}' together. Want food suggestions or Event Race tips?",
        f"I understand '{user_input}'. I can give a quick recipe recommendation right now."
    ]
    return fallbacks.get(character, get_non_repeating_response(default_options))


def contains_profanity(text):
    bad_words = {
        "fuck", "fucking", "shit", "bitch", "asshole", "bastard", "damn", "crap", "puta", "gago",
        "tanga", "ulol", "pakyu", "motherfucker"
    }
    text_norm = normalize_text(text)
    text_tokens = set(text_norm.split())
    return any(word in text_tokens for word in bad_words)


def get_non_repeating_response(options):
    if 'response_memory' not in st.session_state:
        st.session_state.response_memory = []
    previous = st.session_state.response_memory[-1] if st.session_state.response_memory else ""
    candidates = [opt for opt in options if opt != previous]
    selected = random.choice(candidates if candidates else options)
    st.session_state.response_memory.append(selected)
    if len(st.session_state.response_memory) > 20:
        st.session_state.response_memory = st.session_state.response_memory[-20:]
    return selected


def normalize_text(text):
    return re.sub(r'[^a-z0-9\s]', ' ', text.lower()).strip()


def extract_ingredients(recipe_info):
    ingredients = []
    capture = False
    for line in recipe_info.splitlines():
        stripped = line.strip()
        if not stripped:
            if capture:
                break
            continue
        if stripped.lower().startswith('ingredients'):
            capture = True
            continue
        if capture:
            if stripped.startswith('-'):
                ingredients.append(stripped[1:].strip())
            else:
                break
    return ingredients


def retrieve_recipe_matches(query, top_n=3):
    query_norm = normalize_text(query)
    scores = []
    for recipe_name, recipe_info in RECIPE_KNOWLEDGE.items():
        text = normalize_text(recipe_name + ' ' + recipe_info)
        name_bonus = sum(1 for token in query_norm.split() if token in normalize_text(recipe_name).split())
        similarity = difflib.SequenceMatcher(None, query_norm, text).ratio()
        score = similarity + (name_bonus * 0.45)
        scores.append((score, recipe_name, recipe_info))
    scores.sort(reverse=True, key=lambda x: x[0])
    return [
        {"recipe_name": recipe_name, "recipe_info": recipe_info, "score": score}
        for score, recipe_name, recipe_info in scores[:top_n]
        if score > 0.05
    ]


def generate_agentic_response_if_needed(user_input, character):
    user_input_lower = user_input.lower()
    agentic_keywords = [
        'plan', 'shopping list', 'menu', 'steps', 'step-by-step', 'ingredients list',
        'prepare', 'organize', 'cook schedule', 'shopping', 'meal plan', 'recipe plan'
    ]
    if not any(keyword in user_input_lower for keyword in agentic_keywords):
        return None

    matches = retrieve_recipe_matches(user_input, top_n=3)
    if not matches:
        return None

    if 'shopping list' in user_input_lower or 'ingredients' in user_input_lower:
        all_ingredients = []
        for match in matches:
            all_ingredients.extend(extract_ingredients(match['recipe_info']))
        if all_ingredients:
            unique_ingredients = []
            for ingredient in all_ingredients:
                if ingredient not in unique_ingredients:
                    unique_ingredients.append(ingredient)
            return (
                f"{character} Agent:\n"
                "I used the local recipe knowledge base to create a shopping list for you from these recipes:\n"
                + '\n'.join([f"- {match['recipe_name']}" for match in matches])
                + "\n\nShopping List:\n"
                + '\n'.join([f"- {item}" for item in unique_ingredients])
                + "\n\nReady to cook? Ask me for a step-by-step plan for any recipe."
            )

    selected_recipes = matches[:3]
    recipe_names = ', '.join([match['recipe_name'] for match in selected_recipes])
    steps = [
        f"1. Review the recipes: {recipe_names}.",
        "2. Gather all ingredients from the local recipe knowledge base.",
        "3. Decide which dish to cook first based on time and flavor.",
        "4. Follow the step-by-step cooking instructions for each recipe.",
        "5. Serve the dishes together for a tasty menu experience."
    ]
    return (
        f"{character} Agent:\n"
        f"I used retrieval from the recipe knowledge base to suggest a plan based on your request. Here is a simple cooking plan for {recipe_names}:\n"
        + '\n'.join(steps)
        + "\n\nIf you want, I can also create a detailed timeline or a full shopping list for these recipes."
    )


def generate_cybersecurity_response_if_needed(user_input, character):
    user_input_lower = user_input.lower()

    cyber_keywords = [
        "hack", "hacking", "exploit", "payload", "ddos", "sql injection",
        "xss", "phishing", "bruteforce", "penetration test", "pentest",
        "red team", "security", "defense", "activity defense", "blue team", "incident response",
        "vulnerability", "bug bounty", "safe test", "authorized testing",
    ]
    if not any(keyword in user_input_lower for keyword in cyber_keywords):
        return None

    target_url = "https://applied-ai-gecbk5bux78yt8ydcuirqh.streamlit.app/"
    mentions_target = target_url in user_input_lower

    harmful_keywords = [
        "hack this link", "break in", "bypass login", "steal", "crack",
        "attack website", "take down", "deface", "ransomware",
    ]
    if any(keyword in user_input_lower for keyword in harmful_keywords) or mentions_target:
        return (
            f"{character}:\n"
            "I can't help with hacking or breaking into websites.\n\n"
            "I can help you do this safely and legally instead:\n"
            "1. Get written permission and define scope (domains, dates, test type).\n"
            "2. Run defensive checks: auth hardening, input validation, rate limiting, and logging.\n"
            "3. Use legal tools for self-owned systems (OWASP ZAP baseline, dependency scan, secrets scan).\n"
            "4. Write a security report with findings, risk level, and fixes.\n\n"
            "If you want, I can generate a Blue-Team checklist for that app and a safe test template."
        )

    if any(token in user_input_lower for token in ["defense", "blue team", "incident response", "secure", "hardening", "authorized"]):
        return (
            f"{character} Defense Agent:\n"
            "Great topic. Here is a practical Hacking and Activity Defense plan:\n"
            "1. Asset and access inventory.\n"
            "2. Threat model (entry points, trust boundaries, abuse paths).\n"
            "3. Hardening: MFA, least privilege, secure headers, input validation.\n"
            "4. Activity defense and detection: centralized logs, anomaly alerts, audit trails, and abuse-rate monitoring.\n"
            "5. Response: incident playbook, rollback, and post-incident review.\n\n"
            "Ask me for a step-by-step checklist and I will tailor it to Streamlit apps."
        )

    return (
        f"{character}:\n"
        "I can discuss cybersecurity in a safe way: defense, secure coding, monitoring, incident response, and authorized testing workflows."
    )


def show_chatbot():
    st.markdown("""
    <style>
    .chatbot-character-row .stButton > button,
    .chatbot-character-row .stButton > button[kind="primary"],
    .chatbot-character-row .stButton > button[data-testid="stBaseButton-primary"] {
        background: linear-gradient(135deg, #ffd84d, #ff9f00) !important;
        color: #111 !important;
        border: 2px solid rgba(0, 0, 0, 0.18) !important;
        border-radius: 14px !important;
        font-weight: 800 !important;
        box-shadow: 0 8px 18px rgba(255, 153, 0, 0.26) !important;
    }
    .chatbot-character-row .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 12px 24px rgba(255, 153, 0, 0.34) !important;
    }
    </style>
    """, unsafe_allow_html=True)
    st.markdown("""
    <div class='chat-panel'>
        <div class='chat-header'>🤖 Finn-Holley AI Chatbot</div>
        <div class='chat-hint'>Pick your AI Agent and chat using real-world OpenAI ChatGPT responses, with built-in RAG recipe retrieval, Agentic AI planning, and safe Hacking/Activity Defense support.</div>
    </div>
    """, unsafe_allow_html=True)
    with st.expander("OpenAI ChatGPT Setup", expanded=False):
        entered_key = st.text_input(
            "OpenAI API Key",
            type="password",
            value=st.session_state.get("openai_api_key", ""),
            help="Stored in this app session only. You can also set OPENAI_API_KEY as an environment variable.",
        )
        if entered_key:
            st.session_state.openai_api_key = entered_key.strip()
        st.session_state.openai_model = st.text_input(
            "OpenAI Model",
            value=st.session_state.get("openai_model", "gpt-4.1-mini"),
            help="Example: gpt-4.1-mini",
        ).strip() or "gpt-4.1-mini"
        if st.session_state.get("openai_api_key") or os.getenv("OPENAI_API_KEY"):
            st.success("OpenAI is configured. Chatbot will use ChatGPT for real-world responses.")
        else:
            st.info("No OpenAI key found yet. The app will use local fallback until a key is provided.")
    st.markdown("### Choose Your Character:")
    
    characters = {
        "Finn McMissle": "🎩",
        "Holley Shiftwell": "💫",
        "Rod Redline": "🔧",
        "Tomber": "🚙",
        "Leland Turbo": "âš¡",
        "Miles Axelrod": "🚗",
        "Mater": "🚜"
    }
    
    characters = {
        "Finn McMissle": "\U0001F3A9",
        "Holley Shiftwell": "\U0001F4AB",
        "Rod Redline": "\U0001F527",
        "Tomber": "\U0001F699",
        "Leland Turbo": "\u26A1",
        "Miles Axelrod": "\U0001F697",
        "Mater": "\U0001F69C",
        "Professor Zundapp": "\U0001F9EA",
        "Lightning McQueen": "\U0001F3CE\uFE0F",
        "Jackson Storm": "\U0001F5A4",
    }

    selected_char = st.session_state.get('chatbot_char', "Finn McMissle")
    
    # Create styled character buttons
    st.markdown("<div class='chatbot-character-row'>", unsafe_allow_html=True)
    char_cols = st.columns(5)
    for i, (name, emoji) in enumerate(characters.items()):
        with char_cols[i % 5]:
            is_active = selected_char == name
            button_label = f"{emoji} {name}" + (" ✓" if is_active else "")
            if st.button(
                button_label,
                key=f"char_{name}",
                help=f"Chat with {name}",
                type="primary",
            ):
                st.session_state.chatbot_char = name
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown(f"### Currently chatting with: {characters.get(selected_char, '🎩')} **{selected_char}**")
    
    # Chat history
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Display chat with better styling
    for msg in st.session_state.chat_history:
        if msg['role'] == 'user':
            st.markdown(f"""
            <div class="chat-message chat-user">
                <strong>You:</strong> {msg['content']}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-message chat-bot">
                <strong>{msg['character']}:</strong> {msg['content']}
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Chat input
    col1, col2 = st.columns([4, 1])
    with col1:
        user_input = st.text_input("Ask about recipes, race, or safe security defense:", key="chat_input", placeholder="e.g., How do I make Sinigang? What is Adobo? Give me a Streamlit app defense checklist...")
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        send_btn = st.button("📤 Send", key="send_msg", type="primary")
    
    if send_btn and user_input:
        # Add user message
        st.session_state.chat_history.append({'role': 'user', 'content': user_input, 'character': selected_char})
        
        # Generate AI response
        bot_response = generate_ai_response(user_input, selected_char)
        st.session_state.chat_history.append({'role': 'bot', 'content': bot_response, 'character': selected_char})
        st.rerun()
    
    # Quick recipe suggestions
    st.markdown("### 💡 Quick Questions:")
    quick_questions = [
        "How do I make Sinigang?",
        "What is Adobo?",
        "Tell me about Halo-Halo",
        "What is the race schedule?",
        "How to cook Tinola?",
        "How to make spaghetti?",
        "What is Longganisa?",
        "How to make Biko?",
        "What is Sisig?",
        "How to cook Egg?",
        "What is Champorado?",
        "Use RAG and compare Sinigang vs Adobo ingredients",
        "Create an Agentic AI meal plan + shopping list for 3 dishes",
        "Give me a safe Blue-Team checklist for a Streamlit app",
        "How do I do authorized security testing legally?"
    ]
    
    q_cols = st.columns(5)
    for i, q in enumerate(quick_questions):
        with q_cols[i % 5]:
            if st.button(f"❓ {q}", key=f"quick_{i}"):
                st.session_state.chat_history.append({'role': 'user', 'content': q, 'character': selected_char})
                bot_response = generate_ai_response(q, selected_char)
                st.session_state.chat_history.append({'role': 'bot', 'content': bot_response, 'character': selected_char})
                st.rerun()
    
    st.markdown("---")
    if st.button("\U0001F5D1\ufe0f Clear Chat"):
        st.session_state.chat_history = []
        st.rerun()


def show_chatbot_v2():
    st.markdown(
        """
    <div class='chat-panel'>
        <div class='chat-header'>Finn-Holley AI Chatbot</div>
        <div class='chat-hint'>ChatGPT-style UI with real-world OpenAI responses, SQLite memory, RAG recipe context, and safe Hacking/Activity Defense.</div>
    </div>
    """,
        unsafe_allow_html=True,
    )
    with st.expander("OpenAI ChatGPT Setup", expanded=False):
        entered_key = st.text_input(
            "OpenAI API Key",
            type="password",
            value=st.session_state.get("openai_api_key", ""),
            help="Stored in current Streamlit session only. You can also use OPENAI_API_KEY environment variable.",
        )
        if entered_key:
            st.session_state.openai_api_key = entered_key.strip()
        st.session_state.openai_model = st.text_input(
            "OpenAI Model",
            value=st.session_state.get("openai_model", "gpt-4.1-mini"),
        ).strip() or "gpt-4.1-mini"
        if st.session_state.get("openai_api_key") or os.getenv("OPENAI_API_KEY"):
            st.success("OpenAI is configured.")
        else:
            st.info("Add your OpenAI API key to enable real-world ChatGPT responses.")

    characters = {
        "Finn McMissle": "\U0001F3A9",
        "Holley Shiftwell": "\U0001F4AB",
        "Rod Redline": "\U0001F527",
        "Leland Turbo": "\u26A1",
        "Tomber": "\U0001F699",
        "Miles Axelrod": "\U0001F697",
        "Professor Zundapp": "\U0001F9EA",
        "Lightning McQueen": "\U0001F3CE\uFE0F",
        "Mater": "\U0001F69C",
        "Jackson Storm": "\U0001F5A4",
    }
    selected_char = st.session_state.get("chatbot_char", "Finn McMissle")

    st.markdown("### Choose AI Agent")
    char_cols = st.columns(5)
    for i, (name, emoji) in enumerate(characters.items()):
        with char_cols[i % 5]:
            label = f"{emoji} {name}" + (" *" if selected_char == name else "")
            if st.button(label, key=f"chatgpt_char_{name}", type="secondary"):
                st.session_state.chatbot_char = name
                st.rerun()
    selected_char = st.session_state.get("chatbot_char", "Finn McMissle")
    st.caption(f"Active agent: {characters.get(selected_char, '')} {selected_char}")

    session_id = get_active_chat_session_id()
    db_history = load_chat_messages(session_id, limit=80)
    st.session_state.chat_history = [
        {"role": row["role"], "content": row["content"], "character": row["character"]}
        for row in db_history
    ]

    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            with st.chat_message("user", avatar="\U0001F9D1"):
                st.markdown(msg["content"])
        else:
            avatar = characters.get(msg.get("character", selected_char), "\U0001F916")
            with st.chat_message("assistant", avatar=avatar):
                st.markdown(f"**{msg.get('character', selected_char)}**\n\n{msg['content']}")

    def handle_user_prompt(prompt_text):
        if not prompt_text or not prompt_text.strip():
            return
        prompt_text = prompt_text.strip()
        save_chat_message(session_id, selected_char, "user", prompt_text)
        bot_response = generate_ai_response(prompt_text, selected_char)
        save_chat_message(session_id, selected_char, "bot", bot_response)
        st.rerun()

    st.markdown("### Quick Prompts")
    quick_questions = [
        "How do I make Sinigang?",
        "What is Adobo?",
        "Tell me about Halo-Halo",
        "Use RAG and compare Sinigang vs Adobo ingredients",
        "Create an Agentic AI meal plan and shopping list for 3 dishes",
        "Give me a safe Blue-Team checklist for a Streamlit app",
    ]
    q_cols = st.columns(3)
    for i, q in enumerate(quick_questions):
        with q_cols[i % 3]:
            if st.button(q, key=f"chatgpt_quick_{i}"):
                handle_user_prompt(q)

    user_prompt = st.chat_input(
        "Message Finn-Holley AI Chatbot (recipes, real-world Q&A, race strategy, safe defense topics)..."
    )
    if user_prompt:
        handle_user_prompt(user_prompt)

    action_cols = st.columns(2)
    with action_cols[0]:
        if st.button("Clear Current Chat"):
            clear_chat_messages(session_id)
            st.session_state.chat_history = []
            st.rerun()
    with action_cols[1]:
        if st.button("Start New Chat Session"):
            st.session_state.chat_session_id = f"session_{uuid.uuid4().hex[:12]}"
            st.session_state.chat_history = []
            st.rerun()


def show_event_race():
    st.markdown("## Event Race")
    st.markdown("""
    <div class='mission-board'>
        Race the champions in warm orange and yellow glow mode. Upgraded event mode now includes long-run strategy, yellow-flag moments, and scheduled pit crew full-repair stops every 15 laps.
    </div>
    """, unsafe_allow_html=True)
    racers = [
        {"name": "Lightning McQueen", "image": "cars_2_mcquee12.png", "color": "#ff3b30", "desc": "The red racing legend - 5-time Piston Cup Champion!"},
        {"name": "Francesco Bernoulli", "image": "francesco_bernoulli.png", "color": "#0066cc", "desc": "The Italian speedster - Lightning's biggest rival!"},
        {"name": "Jackson Storm", "image": "jackson_storm.png", "color": "#1a1a2e", "desc": "Next-gen racer - sleek and powerful."},
        {"name": "Cal Weathers", "image": "cal_weathers.png", "color": "#ff9500", "desc": "Veteran racer with strong consistency."},
        {"name": "Rip Clutchgoneski", "image": "rip_clutchgoneski.png", "color": "#c1121f", "desc": "New Republic's determined world-class racer."},
        {"name": "Carla Veloso", "image": "carla_veloso.png", "color": "#ff4d6d", "desc": "Brazilian star known for samba-style speed."},
        {"name": "Cruz Ramirez", "image": "cruz_ramirez.png", "color": "#f7c948", "desc": "Trainer turned top racer with elite pace."},
        {"name": "Jeff Gorvette", "image": "jeff_gorvette.png", "color": "#3a86ff", "desc": "American champion with smooth cornering."},
        {"name": "Miguel Camino", "image": "miguel_camino.png", "color": "#d00000", "desc": "Spanish racer combining rhythm and precision."},
        {"name": "Max Schnell", "image": "max_schnell.png", "color": "#2a9d8f", "desc": "German racer built for technical tracks."},
        {"name": "Bobby Swift", "image": "bobby_swift.png", "color": "#e76f51", "desc": "Aggressive modern racer with fast starts."},
        {"name": "Chick Hicks", "image": "cars_3_chick10.png", "color": "#84a98c", "desc": "Classic rival with rough but effective tactics."},
        {"name": "Lewis Hamilton", "image": "lewis_hamilton.png", "color": "#6c757d", "desc": "Global icon with elite racecraft and pace."},
        {"name": "Todd Marcus", "image": "todd-marcus1.png", "color": "#adb5bd", "desc": "Steady performer with strong race rhythm."},
        {"name": "Raoul \u00C7aRoule", "image": "raoul_caroule.png", "color": "#00b4d8", "desc": "French rally specialist with sharp transitions."},
        {"name": "Shu Todoroki", "image": "shu_todoroki.png", "color": "#e63946", "desc": "Precision driver with excellent corner control."},
        {"name": "Nigel Gearsley", "image": "nigel_gearsley.png", "color": "#1d3557", "desc": "Strategic racer known for balanced pace."},
        {"name": "Dud Throttleman", "image": "dud_throttleman.png", "color": "#6d597a", "desc": "Strong late-race charger and drafter."},
        {"name": "Speedy Comet", "image": "speedy_comet.png", "color": "#ff006e", "desc": "Quick accelerator with aggressive starts."},
        {"name": "Brick Yardley", "image": "brick_yardley.png", "color": "#8d99ae", "desc": "Consistent lap-time specialist."},
        {"name": "Bubba Wheelhouse", "image": "bubba_wheelhouse.png", "color": "#bc6c25", "desc": "Fearless overtaker with dirt-track roots."},
        {"name": "Chase Racelott", "image": "chase_racelott.png", "color": "#4cc9f0", "desc": "Young rising racer with clean exits."},
        {"name": "Nikolai Javier Jr.", "image": "Nikolai_Javier1.png", "color": "#ff6600", "desc": "Rising star from the Philippines with incredible speed."},
        {"name": "Daria Patrick", "image": "bini_dariapatrick1.png", "color": "#ff1493", "desc": "American racing icon known for her determination and skill."},
        {"name": "Anderson Shell", "image": "AndersonShell.png", "color": "#f77f00", "desc": "Sharp strategist with elite fuel-saving pace."},
        {"name": "Kool Oliver", "image": "KoolOliver.png", "color": "#00a6fb", "desc": "Cool-headed racer with smooth tire management."},
        {"name": "Tyrant Jones", "image": "TyrantJones.png", "color": "#7b2cbf", "desc": "Fearless charger known for bold overtakes."},
        {"name": "Pandazer", "image": "Pandazer.png", "color": "#1b4332", "desc": "Technical specialist with fast sector splits."},
        {"name": "Zoda Collins", "image": "ZodaCollins.png", "color": "#ef476f", "desc": "Explosive starter with strong first-lap speed."},
        {"name": "Mister Ketchum", "image": "MrKetchum.png", "color": "#6a4c93", "desc": "Veteran racer with disciplined race control."},
        {"name": "Snoop Dogg", "image": "LakerBoy.png", "color": "#ffbe0b", "desc": "Style icon bringing calm confidence to the grid."},
        {"name": "Stephen Curry", "image": "StepCurry.png", "color": "#1d4ed8", "desc": "Precision ace with laser-accurate lines."},
        {"name": "Anthony Edwards", "image": "AntManGuy.png", "color": "#e63946", "desc": "Dynamic attacker with high-speed reflexes."},
        {"name": "LeBron James", "image": "BronJames.png", "color": "#7f5539", "desc": "Powerhouse racer with unmatched race IQ."},
        {"name": "BTS V", "image": "BTSBoy.png", "color": "#023e8a", "desc": "Elegant driver with clean rhythm and flair."},
        {"name": "Pierre Bouvier", "image": "SimplePlan.png", "color": "#5a189a", "desc": "Composed competitor with steady lap flow."},
        {"name": "Alex Gaskarth", "image": "AllTimeLow.png", "color": "#264653", "desc": "Fast adapter who shines in changing conditions."},
        {"name": "Victor Gyokeres", "image": "ArsenalGunners.png", "color": "#c1121f", "desc": "Powerful finisher with relentless pace."},
        {"name": "Bruno Fernandes", "image": "ManUnited.png", "color": "#9d0208", "desc": "Creative tactician with smart pit timing."},
        {"name": "Erling Haaland", "image": "ManCity.png", "color": "#48cae4", "desc": "High-output racer built for straight-line speed."},
        {"name": "Lamine Yamal", "image": "FCBarcelona.png", "color": "#003049", "desc": "Young prodigy with fearless racecraft."},
        {"name": "Vini Jr.", "image": "RealMadrid.png", "color": "#f1faee", "desc": "Electric pace with rapid corner exits."},
        {"name": "Steven Wirtz", "image": "LiverpoolFC.png", "color": "#d90429", "desc": "Mid-race maestro with excellent consistency."},
        {"name": "Mark Hoppus", "image": "182blink.png", "color": "#2a9d8f", "desc": "Steady tempo racer with reliable late laps."},
        {"name": "Billie Joe Armstrong", "image": "GreenDay.png", "color": "#386641", "desc": "Aggressive line-taker with punk-speed energy."},
        {"name": "Olivia Rodrigo", "image": "OliviaRodrigo.png", "color": "#ff4d6d", "desc": "Rising threat with confident race rhythm."},
        {"name": "Osumane Dembele", "image": "PSG.png", "color": "#14213d", "desc": "Rapid mover with unpredictable acceleration."},
        {"name": "Jayson Tatum", "image": "Celtic.png", "color": "#2d6a4f", "desc": "Balanced performer with clutch final laps."},
        {"name": "Jeremy McKinnon", "image": "ADTR.png", "color": "#3a0ca3", "desc": "Heavy-hitting racer with strong race starts."},
        {"name": "Kelly O'Connor", "image": "Sourpatch.png", "color": "#80ed99", "desc": "Creative racer with surprise strategy calls."},
        {"name": "Denise Simmons", "image": "Chitos.png", "color": "#f77f00", "desc": "Orange-zone sprinter with fearless dives."},
        {"name": "Simon Simmons", "image": "Ritos.png", "color": "#ff7b00", "desc": "Late-race attacker with crisp overtakes."},
        {"name": "Tyrell Park", "image": "ColaCola.png", "color": "#d62828", "desc": "Endurance-focused racer with steady control."},
        {"name": "Jim Johnson", "image": "JimiJohnson.png", "color": "#6c757d", "desc": "Old-school racer with durable race pace."},
        {"name": "Tyrese Haliburton", "image": "Haliburton.png", "color": "#1d4ed8", "desc": "Smooth operator with efficient tire usage."},
        {"name": "Dame Time", "image": "dametime.png", "color": "#4361ee", "desc": "Clutch specialist who closes races hard."},
        {"name": "Aiah Arceta", "image": "BINIaiah.png", "color": "#00b4d8", "desc": "Focused racer with polished corner execution."},
        {"name": "Colet Vergara", "image": "BINIcolet.png", "color": "#f72585", "desc": "High-energy racer with quick recovery speed."},
        {"name": "Maloi Ricalde", "image": "BINImaloi.png", "color": "#ffb703", "desc": "Confident tactician with stable lap timing."},
        {"name": "Gwen Apuli", "image": "BINIgwen.png", "color": "#8ecae6", "desc": "Calm competitor with precise line control."},
        {"name": "Stacey Sevilleja", "image": "BINIstacey.png", "color": "#fb8500", "desc": "Strong starter with excellent launch pace."},
        {"name": "Mikha Lim", "image": "BINImikha.png", "color": "#d90429", "desc": "Red-hot racer with aggressive mid-lap gain."},
        {"name": "Jhoanna Robles", "image": "BINIJhoanna.png", "color": "#219ebc", "desc": "Strategic racer with balanced risk control."},
        {"name": "Sheena Catacutan", "image": "BINISheena.png", "color": "#8338ec", "desc": "Fast learner with adaptable race style."},
        {"name": "Loisa Andalio", "image": "BINIteal.png", "color": "#00afb9", "desc": "Teal-speed specialist with strong late pace."},
        {"name": "AC Bonifacio", "image": "ACBonifacio.png", "color": "#ff006e", "desc": "Showtime racer with sharp attack windows."},
        {"name": "Vivoree Esclito", "image": "VivoreeEsclito.png", "color": "#ff7096", "desc": "Consistent performer with clean race tempo."},
        {"name": "Charlotte Madison", "image": "Charlotte.png", "color": "#8d99ae", "desc": "Reliable racer with steady technical pace."},
        {"name": "Cristiano Ronaldo", "image": "CRonaldo.png", "color": "#6d6875", "desc": "Elite competitor with unmatched winning focus."},
        {"name": "Harry Kane", "image": "BayernMunich.png", "color": "#780000", "desc": "Clinical finisher with strong race execution."},
        {"name": "Princess Peach", "image": "PrincessPeach.png", "color": "#ff8fab", "desc": "Graceful racer with smooth line precision."},
        {"name": "Princess Daisy", "image": "PrincessDaisy.png", "color": "#ff9f1c", "desc": "Sunny-speed racer with fearless confidence."},
        {"name": "Luigi", "image": "SuperLuigi.png", "color": "#2b9348", "desc": "Classic kart hero with nimble handling."},
        {"name": "Mario", "image": "SuperMario.png", "color": "#e63946", "desc": "Legendary all-round racer with clutch boosts."},
        {"name": "Rosalina", "image": "PrincessRosalina.png", "color": "#48bfe3", "desc": "Cosmic strategist with elegant long-run pace."},
        {"name": "Yoshi", "image": "Yoshi.png", "color": "#52b788", "desc": "Quick-reacting racer with playful speed bursts."},
    ]
    cols = st.columns(3)
    for i, racer in enumerate(racers):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="race-card" style="border-color: {racer['color']}; background: linear-gradient(135deg, #fff1be, #ffab00);">
            """, unsafe_allow_html=True)
            if os.path.exists(racer['image']):
                st.image(racer['image'], width=400)
            else:
                st.markdown(f"<div class='race-car' style='font-size: 80px;'>🏁</div>", unsafe_allow_html=True)
            st.markdown(f"""
                <div class="race-name" style="color: #111;">{racer['name']}</div>
                <div class="character-quote">{racer['desc']}</div>
            </div>
            """, unsafe_allow_html=True)
    st.markdown("### Race Setup")
    setup_col1, setup_col2, setup_col3, setup_col4 = st.columns(4)
    with setup_col1:
        laps = st.slider("Laps", min_value=70, max_value=100, value=70)
    with setup_col2:
        weather = st.selectbox("Weather", ["Sunny", "Cloudy", "Windy", "Rainy"])
    with setup_col3:
        track = st.selectbox("Track", [
            "Radiator Springs Speedway",
            "Coastal Circuit",
            "Desert Loop",
            "Philippine Clark International Speedway (Pampanga)",
            "Batangas Racing Circuit (Rosario, Batangas)",
            "Fuji Speedway",
        ])
    with setup_col4:
        race_mode = st.selectbox("Race Mode", ["Simulator", "Arcade"])
    racer_names = [r["name"] for r in racers]
    if "event_race_last_results" not in st.session_state:
        st.session_state.event_race_last_results = None
    if "event_race_last_events" not in st.session_state:
        st.session_state.event_race_last_events = []
    if "event_race_last_meta" not in st.session_state:
        st.session_state.event_race_last_meta = {}
    st.info(
        f"Full-grid race enabled: all {len(racers)} racers will participate in both Simulator and Arcade modes."
    )
    st.markdown("### Race Results Simulator")
    if st.button("Start Race!", type="primary"):
        weather_seconds = {"Sunny": 0.0, "Cloudy": 0.3, "Windy": 0.7, "Rainy": 1.2}
        track_seconds = {
            "Radiator Springs Speedway": 0.2,
            "Coastal Circuit": 0.5,
            "Desert Loop": 0.8,
            "Philippine Clark International Speedway (Pampanga)": 0.3,
            "Batangas Racing Circuit (Rosario, Batangas)": 0.7,
            "Fuji Speedway": 0.4,
        }
        base_time = {}
        for idx, name in enumerate(racer_names):
            base_time[name] = 16.0 + (idx % 9) * 0.12 + random.uniform(-0.35, 0.35)

        featured_pace_bonus = {
            "Lightning McQueen": -0.25,
            "Francesco Bernoulli": -0.2,
            "Jackson Storm": -0.28,
            "Cruz Ramirez": -0.18,
            "Lewis Hamilton": -0.3,
            "Nikolai Javier Jr.": -0.14,
        }
        for name, bonus in featured_pace_bonus.items():
            if name in base_time:
                base_time[name] += bonus

        entrants = racers
        mode_variation = 1.5 if race_mode == "Simulator" else 0.8
        results = []
        event_feed = []
        for racer in entrants:
            lap_times = []
            wear_penalty = 0.0
            status = "FINISHED"
            completed_laps = 0
            for lap in range(1, laps + 1):
                completed_laps = lap
                yellow_flag_penalty = 0.0
                if random.random() <= 0.08:
                    yellow_flag_penalty = random.uniform(0.6, 1.3)
                    event_feed.append(f"Lap {lap}: Yellow flag out. {racer['name']} reduced pace under caution.")

                # Rare major incident: racer is out for the entire race.
                if random.random() <= 0.012:
                    status = "OUT (Massive Crash)"
                    event_feed.append(f"Lap {lap}: Massive crash! {racer['name']} is out of the race.")
                    break

                if lap % 15 == 0:
                    event_feed.append(f"Lap {lap}: {racer['name']} pit crew full repair complete. Race restarts at same lap count.")
                    wear_penalty = 0.0
                    pit_stop_penalty = random.uniform(3.8, 5.6)
                else:
                    wear_penalty += random.uniform(0.01, 0.045)
                    pit_stop_penalty = 0.0

                lap_time = (
                    base_time[racer["name"]]
                    + weather_seconds[weather]
                    + track_seconds[track]
                    + random.uniform(-mode_variation, mode_variation)
                    + yellow_flag_penalty
                    + wear_penalty
                    + pit_stop_penalty
                )
                lap_times.append(max(0.1, lap_time))
            if status == "OUT (Massive Crash)":
                total_time = float("inf")
                avg_lap_time = 0.0
                best_lap = 0.0
            else:
                total_time = sum(lap_times)
                avg_lap_time = total_time / laps
                best_lap = min(lap_times) if lap_times else 0.0
            results.append((racer["name"], total_time, avg_lap_time, best_lap, status, completed_laps))
        ranking = sorted(results, key=lambda x: (x[4] != "FINISHED", x[1]))
        st.session_state.event_race_last_results = ranking
        st.session_state.event_race_last_events = event_feed
        st.session_state.event_race_last_meta = {
            "laps": laps,
            "track": track,
            "mode": race_mode,
            "weather": weather,
        }
    if st.session_state.event_race_last_results:
        ranking = st.session_state.event_race_last_results
        event_feed = st.session_state.event_race_last_events
        race_meta = st.session_state.event_race_last_meta
        finished_racers = [r for r in ranking if r[4] == "FINISHED"]
        if finished_racers:
            winner = finished_racers[0]
            st.success(
                f"Winner: {winner[0]} | Total Time: {winner[1]:.2f}s | "
                f"Laps: {race_meta.get('laps', laps)} | Track: {race_meta.get('track', track)} | Mode: {race_meta.get('mode', race_mode)}"
            )
        else:
            st.error("No winner: all racers were out due to massive crashes.")
        st.success(
            f"Race Battle Summary | Weather: {race_meta.get('weather', weather)} | "
            f"Track: {race_meta.get('track', track)} | Laps: {race_meta.get('laps', laps)}"
        )
        st.markdown("### Race Control Events")
        if event_feed:
            for event_line in event_feed[:25]:
                st.write(f"- {event_line}")
            if len(event_feed) > 25:
                st.write(f"- ...and {len(event_feed) - 25} more race-control updates.")
        else:
            st.write("- Clean race: no yellow-flag incidents triggered this run.")
        st.markdown("### Podium")
        if finished_racers:
            for idx, (name, total_time, avg_lap, best_lap, status, completed_laps) in enumerate(finished_racers[:3], start=1):
                st.write(
                    f"{idx}. **{name}** - Total: {total_time:.2f}s | "
                    f"Avg Lap: {avg_lap:.2f}s | Best Lap: {best_lap:.2f}s | Status: {status}"
                )
        else:
            st.write("No podium available this race.")
        st.markdown("### Full Standings (Lap-Based Win)")
        for idx, (name, total_time, avg_lap, best_lap, status, completed_laps) in enumerate(ranking, start=1):
            if status == "FINISHED":
                st.write(
                    f"{idx}. {name} (Total: {total_time:.2f}s, Avg: {avg_lap:.2f}s, Best Lap: {best_lap:.2f}s, Status: {status})"
                )
            else:
                st.write(
                    f"{idx}. {name} (Status: {status}, Out On Lap: {completed_laps})"
                )
        if st.button("Reset Race Battle"):
            st.session_state.event_race_last_results = None
            st.session_state.event_race_last_events = []
            st.session_state.event_race_last_meta = {}
            st.rerun()
def show_world_tour():
    st.markdown("## World Tour Recipe")
    st.markdown("*Complete 5 missions first, then defend and recover recipes against the Lemons and Clippers with AI Agent support!*")
    st.info("AI Agents team up in this mode to protect recipes and support your missions against the Clippers and Lemons.")
    st.markdown("### Tour Briefing Map")
    map_path = "map-of-the-world.png"
    if os.path.exists(map_path):
        st.image(map_path, caption="World Tour Route Map", width="stretch")
    else:
        st.warning("Map file not found: map-of-the-world.png. Add it in the project root to show the world map briefing.")
    tours = [
        {
            "location": "England",
            "language": "English",
            "character": "Lightning McQueen",
            "enemy": "The Lemons",
            "emoji": "\U0001F3CE\ufe0f",
            "dish": "Shepherd's Pie",
            "desc": "Savory minced meat pie topped with creamy mashed potatoes.",
        },
        {
            "location": "Philippines",
            "language": "Filipino",
            "character": "Sally",
            "enemy": "The Clippers",
            "emoji": "\U0001F697",
            "dish": "Sinigang",
            "desc": "Sour and savory tamarind soup with vegetables and meat.",
        },
        {
            "location": "Italy",
            "language": "Italian",
            "character": "Mater",
            "enemy": "The Lemons",
            "emoji": "\U0001F697",
            "dish": "Pizza Margherita",
            "desc": "Classic pizza with tomato, mozzarella, and fresh basil.",
        },
    ]
    if "tour_started" not in st.session_state:
        st.session_state.tour_started = False
    if "tour_unlocked_recipes" not in st.session_state:
        st.session_state.tour_unlocked_recipes = []
    if "tour_completed_missions" not in st.session_state:
        st.session_state.tour_completed_missions = []
    if "tour_sent_to_sally_lizzie" not in st.session_state:
        st.session_state.tour_sent_to_sally_lizzie = False
    if "world_tour_start_location" not in st.session_state:
        st.session_state.world_tour_start_location = tours[0]["location"]
    location_options = [tour["location"] for tour in tours]
    st.session_state.world_tour_start_location = st.selectbox(
        "Select Starting Country",
        location_options,
        index=location_options.index(st.session_state.world_tour_start_location),
    )
    start_col1, start_col2 = st.columns(2)
    with start_col1:
        if st.button("Start World Tour", type="primary", width="stretch"):
            st.session_state.tour_started = True
    with start_col2:
        if st.button("Reset Tour", width="stretch"):
            st.session_state.tour_started = False
            st.session_state.tour_unlocked_recipes = []
            st.session_state.tour_completed_missions = []
            st.session_state.tour_sent_to_sally_lizzie = False
    if not st.session_state.tour_started:
        st.info("Select a starting country, then press Start World Tour.")
        return
    import random
    missions = [
        "Mission 1: Gather route map fragments",
        "Mission 2: Decode enemy radio signal",
        "Mission 3: Protect recipe vault key",
        "Mission 4: Escort supply truck",
        "Mission 5: Win the checkpoint sprint",
    ]
    start_location = st.session_state.world_tour_start_location
    ordered_tours = sorted(tours, key=lambda x: x["location"] != start_location)
    st.success(f"World Tour started from **{start_location}**")
    st.markdown("### Mission Board")
    st.markdown("<div class='mission-board'><strong>Mission success chance is 70% per attempt.</strong> Complete all 5 missions before haunting enemy teams against the Lemons and Clippers.</div>", unsafe_allow_html=True)
    st.write(f"Completed missions: **{len(st.session_state.tour_completed_missions)} / 5**")
    for mission in missions:
        completed = mission in st.session_state.tour_completed_missions
        if completed:
            st.success(f"{mission} - COMPLETE")
            continue
        if st.button(f"Attempt {mission}", key=f"mission_{mission}"):
            if random.random() <= 0.70:
                st.session_state.tour_completed_missions.append(mission)
                st.success(f"Success: {mission}")
            else:
                st.error(f"Failed: {mission}. Try again.")
            st.rerun()

    if len(st.session_state.tour_completed_missions) < 5:
        st.warning("Haunting enemies is locked. Complete all 5 missions first.")
        return

    st.markdown("### Haunting Phase")
    st.write("All missions complete. AI Agents now team up to protect recipes while you pressure enemy teams and secure unlocks.")
    for tour in ordered_tours:
        unlocked = tour["dish"] in st.session_state.tour_unlocked_recipes
        status = "Unlocked" if unlocked else "Locked"
        st.markdown(
            f"#### {tour['emoji']} {tour['location']} ({tour['language']}) - {status}"
        )
        st.write(f"Guide: **{tour['character']}** | Enemy Team: **{tour['enemy']}**")
        st.write(tour["desc"])
        if unlocked:
            st.success(f"Recipe unlocked: {tour['dish']}")
        else:
            if st.button(f"Haunt Enemies in {tour['location']}", key=f"haunt_{tour['location']}"):
                st.session_state.tour_unlocked_recipes.append(tour["dish"])
                st.success(f"You and the AI Agent team outplayed {tour['enemy']} and secured the {tour['dish']} recipe!")
                st.rerun()

    st.markdown("### Recipe Collection Progress")
    st.write(f"Unlocked recipes: **{len(st.session_state.tour_unlocked_recipes)} / {len(tours)}**")
    if len(st.session_state.tour_unlocked_recipes) == len(tours):
        if not st.session_state.tour_sent_to_sally_lizzie:
            st.success("All language recipes collected. Final step: send mission and recipe package to Sally and Lizzie.")
            if st.button("Send Complete Package to Sally and Lizzie", type="primary"):
                st.session_state.tour_sent_to_sally_lizzie = True
                st.balloons()
                st.success("Package delivered to Sally and Lizzie. World Tour complete!")
                st.rerun()
        else:
            st.success("Package already delivered to Sally and Lizzie.")

def show_settings():
    st.markdown("""
    <div class='settings-card'>
        <div class='settings-title'>⚙️ Settings</div>
        <div class='settings-subtitle'>Customize your Radiator Springs experience with glowing orange and yellow theme controls.</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 👤 Account Settings")
    if st.session_state.logged_in:
        st.markdown("<div class='settings-block'>", unsafe_allow_html=True)
        st.write(f"**Logged in as:** {st.session_state.username}")
        st.write(f"**Role:** {st.session_state.role}")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.role = "user"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("Guest mode is active. Login is optional.")

    st.markdown("### 🎨 Theme Settings")
    theme_options = ["Orange & Yellow Glow", "Classic Radiator Springs", "Night Racer"]
    current_theme = st.session_state.get("theme_choice", "Orange & Yellow Glow")
    selected_idx = theme_options.index(current_theme) if current_theme in theme_options else 0
    theme_choice = st.radio("Theme palette:", theme_options, index=selected_idx)
    st.session_state.theme_choice = theme_choice
    st.success(f"Theme applied: **{theme_choice}**")
    preview_map = {
        "Orange & Yellow Glow": "Warm energetic gradient with bright orange/yellow cards.",
        "Classic Radiator Springs": "Vintage sunset palette with classic town-road warmth.",
        "Night Racer": "Cool night-race atmosphere with deep blue tones and gold accents.",
    }
    st.markdown(
        f"""
<div class='settings-block'>
<h3>Theme Preview</h3>
<p>{preview_map.get(theme_choice, '')}</p>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown("### 🔔 Notification Settings")
    st.checkbox("Email notifications", value=True, key="notify_email")
    st.checkbox("Recipe updates", value=True, key="notify_recipes")

    st.markdown("### 🌍 Language")
    st.selectbox("Select Language:", ["English", "Filipino", "Spanish", "Italian", "Japanese"], key="ui_language")
def show_about():
    st.markdown(
        """
    <div class='settings-card'>
        <div class='settings-title'>ℹ️ About Radiator Springs</div>
        <div class='settings-subtitle'>Story, features, and release details of the Cars Radiator Springs app.</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    left_col, right_col = st.columns([2, 1])
    with left_col:
        st.markdown(
            """
        <div class='settings-block'>
            <h3>🚗 Cars Radiator Springs - Home Of The Recipe</h3>
            <p>Welcome to the Cars-themed recipe and adventure experience built by the Radiator Springs Team.</p>
            <p><strong>Main Characters:</strong> ⚡ Lightning McQueen, 🚜 Mater, 🚗 Sally Carrera, 💫 Holley Shiftwell, 🎩 Finn McMissle, 🏎️ Cruz Ramirez</p>
            <p><strong>Chatbot Responders:</strong> 🎩 Finn McMissle, 💫 Holley Shiftwell, 🔧 Rod Redline, 🚙 Tomber, ⚡ Leland Turbo, 🚗 Miles Axelrod, 🚜 Mater, 🧪 Professor Zundapp, 🏎️ Lightning McQueen, 🖤 Jackson Storm</p>
            <p><strong>Core Features:</strong> 🍔 Radiator Springs Recipes, 🇵🇭 Filipino Food List, 🤖 AI Chatbot, 🏁 Event Race, 🌍 World Tour Recipe</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with right_col:
        st.markdown(
            """
        <div class='settings-block'>
            <h3>🚀 Version</h3>
            <p><strong>Current Version:</strong> 1.1.0</p>
            <p><strong>Release Date:</strong> May 5, 2026</p>
            <p><strong>Highlights:</strong> Improved chatbot responder system, profanity filter, emoji fixes, and upgraded chatbot UI style.</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("### 📱 Contact Us")
    st.write("📧 Email: hello@radiatorsprings.com")
    st.write("📞 Phone: 1-800-KA-CHOW")
    st.write("📍 Location: Radiator Springs, Arizona")

    st.markdown("### Owner Spotlight")
    if os.path.exists("Nikolai_Javier1.png"):
        st.image("Nikolai_Javier1.png", width=340, caption="Nikolai Javier Jr. - App Owner and Racer")
    else:
        st.warning("Image not found: Nikolai_Javier1.png")
    st.markdown(
        """
<div class='settings-block'>
<h3>Nikolai Javier Jr.</h3>
<p>One of the owners of this app and also a race car personality in this project world.</p>
<p>He helps shape the app vision by combining racing spirit, recipe exploration, and interactive AI storytelling.</p>
</div>
""",
        unsafe_allow_html=True,
    )


def show_home_v2():
    st.image("logo-of-app.png", width="stretch")
    st.markdown("""
    <div class="hero-box">
        <div class="hero-title">Cars Radiator Springs</div>
        <div class="hero-subtitle">
            Home Of The Recipe with Lightning McQueen and Mater
        </div>
        <p>Ka-chow your way into delicious meals and cozy recipes from Radiator Springs!</p>
    </div>
    """, unsafe_allow_html=True)

    st.write("")
    st.write("")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<div class='character-card'>", unsafe_allow_html=True)
        if os.path.exists("cars_2_mcquee12.png"):
            st.image("cars_2_mcquee12.png", width=400)
        else:
            st.warning("Image not found: cars_2_mcquee12.png")
        st.markdown("""
            <div class="character-name">Lightning McQueen</div>
            <div class="character-quote">
                "Ka-chow! Welcome to Radiator Springs! I'm Lightning McQueen, the fastest car in the world! Check out our delicious recipes and speed into flavor!"
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='character-card'>", unsafe_allow_html=True)
        if os.path.exists("cars_2_martin_(tow_mater).png"):
            st.image("cars_2_martin_(tow_mater).png", width=400)
        else:
            st.warning("Image not found: cars_2_martin_(tow_mater).png")
        st.markdown("""
            <div class="character-name">Mater</div>
            <div class="character-quote">
                "Howdy! I'm Mater, the best tow truck in Radiator Springs! Welcome to our kitchen - we got the best comfort food this side of the highway! Yee-haw!"
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.info("Click on 'Login / Register' in the sidebar to get started!")

    st.subheader("Quick Preview")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="recipe-card">
            <div class="card-title">Route 66 Fries</div>
            <div class="card-desc">Crispy golden fries</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="recipe-card">
            <div class="card-title">McQueen Burger</div>
            <div class="card-desc">Double patty with speed sauce</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="recipe-card">
            <div class="card-title">Mater Milkshake</div>
            <div class="card-desc">Creamy vanilla shake</div>
        </div>
        """, unsafe_allow_html=True)


def show_about_v2():
    show_about()
    st.markdown("### Nikolai's Crew Owners")
    crew_cols = st.columns(2)
    crew = [
        {
            "name": "Claudine Margaret Ricablanca",
            "image": "ClaudineMargaret.png",
            "role": "UI Designer and Project Updates",
            "desc": "Supports UI design and project update improvements across the app.",
        },
        {
            "name": "Gwyn Sapio",
            "image": "GwynSapio.png",
            "role": "API and UI Designer",
            "desc": "Supports API integration direction and UI design collaboration.",
        },
    ]
    for idx, member in enumerate(crew):
        with crew_cols[idx]:
            if os.path.exists(member["image"]):
                st.image(member["image"], width=400, caption=f"{member['name']} - {member['role']}")
            else:
                st.warning(f"Image not found: {member['image']}")
            st.markdown(
                f"""
<div class='settings-block'>
<h3>{member['name']}</h3>
<p>{member['desc']}</p>
</div>
""",
                unsafe_allow_html=True,
            )


def show_character_list():
    st.markdown("## Character List")
    st.markdown("Characters, AI Agents, and Villains roster.")

    sections = [
        ("Characters", [
            ("Lightning McQueen", "cars_2_mcquee12.png", ""),
            ("Mater", "cars_2_martin_(tow_mater).png", ""),
            ("Sally", "cars_3_sally.png", ""),
            ("Guido", "cars_2_guido.png", ""),
            ("Luigi", "cars_2_luigi.png", ""),
            ("Sarge", "cars_2_sergent_(sarge).png", ""),
            ("Sheriff", "sheriff.png", ""),
            ("Flo", "flo.png", ""),
            ("Ramone", "Ramone.png", ""),
            ("Mack", "mack.png", ""),
        ]),
        ("AI Agents", [
            ("Lightning McQueen", "cars_2_mcquee12.png", ""),
            ("Mater", "cars_2_martin_(tow_mater).png", ""),
            ("Finn McMissle", "finn_mcmissile.png", ""),
            ("Holley Shiftwell", "holly_shiftwell.png", ""),
            ("Rod Redline Torque", "rod_torque_redline.png", ""),
            ("Leland Turbo", "leland_turbo.png", ""),
            ("Tomber", "tomber.png", ""),
            ("Jackson Storm", "jackson_storm.png", ""),
            ("Professor Zundapp", "professor_zundapp.png", ""),
            ("Miles Axelrod", "miles_axlerod.png", ""),
        ]),
        ("Villains - The Clippers/Lemons", [
            ("Tyler Clippers", "tyler_gremlin.png", ""),
            ("Grem Lemons", "grem.png", ""),
            ("Acer Clippers", "acer (1).png", ""),
            ("Don Lemons", "don_crumlin.png", ""),
            ("Fred Lemons", "FredLemons.png", ""),
            ("Ivan Clippers", "IvanClippers.png", ""),
            ("John Lemons", "JohnLemons.png", ""),
            ("Mike Clippers", "MikeClippers.png", ""),
            ("Petrov Clippers", "PetrovClippers.png", ""),
            ("Tolga Clippers", "TolgaClippers.png", ""),
            ("Towga Clippers", "TowgaLemons.png", ""),
            ("Vladmir Clippers", "VladmirClippers.png", ""),
            ("Victor Clippers", "VictorClippers.png", ""),
            ("Shai Gilgeous-Alexander", "ShaiAlexander.png", "Assistant leader of Lemons"),
            ("Kevin Durant", "KevinDurant.png", "Assistant leader of Clippers"),
            ("Michael Jordan", "MichaelJordan.png", "Leader of Clippers and Lemons; main antagonist"),
        ]),
        ("Racers", [
            ("Lightning McQueen", "cars_2_mcquee12.png", "The red racing legend - 5-time Piston Cup Champion!"),
            ("Francesco Bernoulli", "francesco_bernoulli.png", "The Italian speedster - Lightning's biggest rival!"),
            ("Jackson Storm", "jackson_storm.png", "Next-gen racer - sleek and powerful."),
            ("Cal Weathers", "cal_weathers.png", "Veteran racer with strong consistency."),
            ("Rip Clutchgoneski", "rip_clutchgoneski.png", "New Republic's determined world-class racer."),
            ("Carla Veloso", "carla_veloso.png", "Brazilian star known for samba-style speed."),
            ("Cruz Ramirez", "cruz_ramirez.png", "Trainer turned top racer with elite pace."),
            ("Jeff Gorvette", "jeff_gorvette.png", "American champion with smooth cornering."),
            ("Miguel Camino", "miguel_camino.png", "Spanish racer combining rhythm and precision."),
            ("Max Schnell", "max_schnell.png", "German racer built for technical tracks."),
            ("Bobby Swift", "bobby_swift.png", "Aggressive modern racer with fast starts."),
            ("Chick Hicks", "cars_3_chick10.png", "Classic rival with rough but effective tactics."),
            ("Lewis Hamilton", "lewis_hamilton.png", "Global icon with elite racecraft and pace."),
            ("Todd Marcus", "todd-marcus1.png", "Steady performer with strong race rhythm."),
            ("Raoul ÇaRoule", "raoul_caroule.png", "French rally specialist with sharp transitions."),
            ("Shu Todoroki", "shu_todoroki.png", "Precision driver with excellent corner control."),
            ("Nigel Gearsley", "nigel_gearsley.png", "Strategic racer known for balanced pace."),
            ("Dud Throttleman", "dud_throttleman.png", "Strong late-race charger and drafter."),
            ("Speedy Comet", "speedy_comet.png", "Quick accelerator with aggressive starts."),
            ("Brick Yardley", "brick_yardley.png", "Consistent lap-time specialist."),
            ("Bubba Wheelhouse", "bubba_wheelhouse.png", "Fearless overtaker with dirt-track roots."),
            ("Chase Racelott", "chase_racelott.png", "Young rising racer with clean exits."),
            ("Nikolai Javier Jr.", "Nikolai_Javier1.png", "Rising star from the Philippines with incredible speed."),
            ("Daria Patrick", "bini_dariapatrick1.png", "American racing icon known for her determination and skill."),
            ("Anderson Shell", "AndersonShell.png", "Sharp strategist with elite fuel-saving pace."),
            ("Kool Oliver", "KoolOliver.png", "Cool-headed racer with smooth tire management."),
            ("Tyrant Jones", "TyrantJones.png", "Fearless charger known for bold overtakes."),
            ("Pandazer", "Pandazer.png", "Technical specialist with fast sector splits."),
            ("Zoda Collins", "ZodaCollins.png", "Explosive starter with strong first-lap speed."),
            ("Mister Ketchum", "MrKetchum.png", "Veteran racer with disciplined race control."),
            ("Snoop Dogg", "LakerBoy.png", "Style icon bringing calm confidence to the grid."),
            ("Stephen Curry", "StepCurry.png", "Precision ace with laser-accurate lines."),
            ("Anthony Edwards", "AntManGuy.png", "Dynamic attacker with high-speed reflexes."),
            ("LeBron James", "BronJames.png", "Powerhouse racer with unmatched race IQ."),
            ("BTS V", "BTSBoy.png", "Elegant driver with clean rhythm and flair."),
            ("Pierre Bouvier", "SimplePlan.png", "Composed competitor with steady lap flow."),
            ("Alex Gaskarth", "AllTimeLow.png", "Fast adapter who shines in changing conditions."),
            ("Victor Gyokeres", "ArsenalGunners.png", "Powerful finisher with relentless pace."),
            ("Bruno Fernandes", "ManUnited.png", "Creative tactician with smart pit timing."),
            ("Erling Haaland", "ManCity.png", "High-output racer built for straight-line speed."),
            ("Lamine Yamal", "FCBarcelona.png", "Young prodigy with fearless racecraft."),
            ("Vini Jr.", "RealMadrid.png", "Electric pace with rapid corner exits."),
            ("Steven Wirtz", "LiverpoolFC.png", "Mid-race maestro with excellent consistency."),
            ("Mark Hoppus", "182blink.png", "Steady tempo racer with reliable late laps."),
            ("Billie Joe Armstrong", "GreenDay.png", "Aggressive line-taker with punk-speed energy."),
            ("Olivia Rodrigo", "OliviaRodrigo.png", "Rising threat with confident race rhythm."),
            ("Osumane Dembele", "PSG.png", "Rapid mover with unpredictable acceleration."),
            ("Jayson Tatum", "Celtic.png", "Balanced performer with clutch final laps."),
            ("Jeremy McKinnon", "ADTR.png", "Heavy-hitting racer with strong race starts."),
            ("Kelly O'Connor", "Sourpatch.png", "Creative racer with surprise strategy calls."),
            ("Denise Simmons", "Chitos.png", "Orange-zone sprinter with fearless dives."),
            ("Simon Simmons", "Ritos.png", "Late-race attacker with crisp overtakes."),
            ("Tyrell Park", "ColaCola.png", "Endurance-focused racer with steady control."),
            ("Jim Johnson", "JimiJohnson.png", "Old-school racer with durable race pace."),
            ("Tyrese Haliburton", "Haliburton.png", "Smooth operator with efficient tire usage."),
            ("Dame Time", "dametime.png", "Clutch specialist who closes races hard."),
            ("Aiah Arceta", "BINIaiah.png", "Focused racer with polished corner execution."),
            ("Colet Vergara", "BINIcolet.png", "High-energy racer with quick recovery speed."),
            ("Maloi Ricalde", "BINImaloi.png", "Confident tactician with stable lap timing."),
            ("Gwen Apuli", "BINIgwen.png", "Calm competitor with precise line control."),
            ("Stacey Sevilleja", "BINIstacey.png", "Strong starter with excellent launch pace."),
            ("Mikha Lim", "BINImikha.png", "Red-hot racer with aggressive mid-lap gain."),
            ("Jhoanna Robles", "BINIJhoanna.png", "Strategic racer with balanced risk control."),
            ("Sheena Catacutan", "BINISheena.png", "Fast learner with adaptable race style."),
            ("Loisa Andalio", "BINIteal.png", "Teal-speed specialist with strong late pace."),
            ("AC Bonifacio", "ACBonifacio.png", "Showtime racer with sharp attack windows."),
            ("Vivoree Esclito", "VivoreeEsclito.png", "Consistent performer with clean race tempo."),
            ("Charlotte Madison", "Charlotte.png", "Reliable racer with steady technical pace."),
            ("Cristiano Ronaldo", "CRonaldo.png", "Elite competitor with unmatched winning focus."),
            ("Harry Kane", "BayernMunich.png", "Clinical finisher with strong race execution."),
            ("Princess Peach", "PrincessPeach.png", "Graceful racer with smooth line precision."),
            ("Princess Daisy", "PrincessDaisy.png", "Sunny-speed racer with fearless confidence."),
            ("Luigi", "SuperLuigi.png", "Classic kart hero with nimble handling."),
            ("Mario", "SuperMario.png", "Legendary all-round racer with clutch boosts."),
            ("Rosalina", "PrincessRosalina.png", "Cosmic strategist with elegant long-run pace."),
            ("Yoshi", "Yoshi.png", "Quick-reacting racer with playful speed bursts."),
        ]),
    ]

    for section_title, entries in sections:
        st.markdown(f"### {section_title}")
        cols = st.columns(4)
        for idx, (name, image, role) in enumerate(entries):
            with cols[idx % 4]:
                if os.path.exists(image):
                    st.image(image, width=400)
                else:
                    st.warning(f"Image not found: {image}")
                st.markdown(f"**{name}**")
                if role:
                    st.caption(role)


def render_general_footer():
    st.markdown(
        """
<div style="
    margin-top: 28px;
    padding: 14px 16px;
    border-radius: 16px;
    background: linear-gradient(135deg, #ffd84d, #ff9f00);
    color: #111;
    text-align: center;
    font-weight: 800;
    border: 1px solid rgba(0, 0, 0, 0.18);
    box-shadow: 0 8px 18px rgba(255, 153, 0, 0.22);
">
Cars Radiator Springs - Home Of The Recipe | Version 1.1.0 | Built with heart by the Radiator Springs Team
</div>
""",
        unsafe_allow_html=True,
    )
# ==========================================================
# MAIN APP
# ==========================================================
pages = {
    "home": {"label": "\U0001F3E0 Home / Welcome", "icon": "Home", "view": show_home_v2, "protected": False, "section": "General"},
    "character_list": {"label": "\U0001F4D8 Character List", "icon": "Cast", "view": show_character_list, "protected": False, "section": "General"},
    "auth": {"label": "\U0001F510 Login / Register", "icon": "Auth", "view": show_login_register, "protected": False, "section": "General"},
    "products": {"label": "\U0001F4CB Product List", "icon": "Menu", "view": show_product_list, "protected": False, "section": "Food & Recipes"},
    "radiator_food": {"label": "\U0001F354 Radiator Springs Food", "icon": "Cars", "view": show_radiator_springs_food, "protected": False, "section": "Food & Recipes"},
    "filipino_food": {"label": "\U0001F1F5\U0001F1ED Filipino Food List", "icon": "PH", "view": show_filipino_food, "protected": False, "section": "Food & Recipes"},
    "chatbot": {"label": "\U0001F916 Finn-Holley AI Chatbot", "icon": "AI", "view": show_chatbot_v2, "protected": False, "section": "Interactive"},
    "event_race": {"label": "\U0001F3C1 Event Race", "icon": "Race", "view": show_event_race, "protected": False, "section": "Interactive"},
    "world_tour": {"label": "\U0001F30D World Tour Recipe", "icon": "Tour", "view": show_world_tour, "protected": False, "section": "Interactive"},
    "settings": {"label": "\u2699\ufe0f Settings", "icon": "Config", "view": show_settings, "protected": False, "section": "Account"},
    "about": {"label": "ℹ️ Info / About", "icon": "Info", "view": show_about_v2, "protected": False, "section": "General"},
}
ordered_page_ids = [
    "home",
    "character_list",
    "auth",
    "products",
    "radiator_food",
    "filipino_food",
    "chatbot",
    "event_race",
    "world_tour",
    "settings",
    "about",
]
if "selected_page" not in st.session_state:
    st.session_state.selected_page = "home"
if st.session_state.selected_page not in pages:
    st.session_state.selected_page = "home"

section_order = ["General", "Food & Recipes", "Interactive", "Account"]
section_map = {section: [] for section in section_order}
for page_id in ordered_page_ids:
    section_map[pages[page_id]["section"]].append(page_id)

st.sidebar.title("Control Deck")
with st.sidebar.expander("Section Guide", expanded=True):
    st.markdown("""
- \U0001F3E0 Home / Welcome - Welcome messages from Lightning McQueen and Mater before login
- \U0001F4D8 Character List - Main characters, AI agents, and villain roster
- \U0001F510 Login / Register - SQLite-based authentication with admin panel
- \U0001F4CB Product List - All products with search and filter
- \U0001F354 Radiator Springs Food - Cars-themed recipes
- \U0001F1F5\U0001F1ED Filipino Food List - Traditional Filipino dishes
- \U0001F916 Finn-Holley AI Chatbot - Chat with Finn, Holley, Rod, Tomber, Leland, Miles, Mater, Professor Zundapp, Lightning McQueen, and Jackson Storm
- \U0001F3C1 Event Race - Racing champions with expanded global roster
- \U0001F30D World Tour Recipe - Complete 5 missions, haunt enemies, unlock recipes, then send package to Sally and Lizzie
- \u2699\ufe0f Settings - Account settings, theme, notifications, language
- \u2139\ufe0f Info / About - App story, owners, release version, and contact details
""")
st.sidebar.markdown(
    """
<div class="menu-list-box">
<strong>Menu List</strong><br>
Home / Welcome<br>
Character List<br>
Login / Register<br>
Product List<br>
Radiator Springs Food<br>
Filipino Food List<br>
Finn-Holley AI Chatbot<br>
Event Race<br>
World Tour Recipe<br>
Settings<br>
Info / About
</div>
""",
    unsafe_allow_html=True,
)
status = f"Signed in: {st.session_state.username}" if st.session_state.logged_in else "Guest mode"
st.sidebar.markdown(f"<div class='nav-status'>{status}</div>", unsafe_allow_html=True)

if st.sidebar.button("Go Home", width="stretch"):
    st.session_state.selected_page = "home"
if st.sidebar.button("Open Login", width="stretch"):
    st.session_state.selected_page = "auth"
st.sidebar.markdown("---")

current_section = pages[st.session_state.selected_page]["section"]
selected_section = st.sidebar.radio(
    "Section",
    section_order,
    index=section_order.index(current_section),
)

section_page_ids = section_map[selected_section]
if st.session_state.selected_page not in section_page_ids:
    st.session_state.selected_page = section_page_ids[0]

def format_nav_label(page_id):
    page = pages[page_id]
    lock = " [Locked]" if page["protected"] and not st.session_state.logged_in else ""
    return f"{page['icon']} | {page['label']}{lock}"

selected_page = st.sidebar.radio(
    "Pages",
    section_page_ids,
    index=section_page_ids.index(st.session_state.selected_page),
    format_func=format_nav_label,
)
st.session_state.selected_page = selected_page
page = pages[selected_page]
page["view"]()

if pages[st.session_state.selected_page]["section"] == "General":
    render_general_footer()



