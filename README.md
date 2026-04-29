# 🚗 Cars Radiator Springs: Home Of The Recipe

A Streamlit story app inspired by the *Cars* universe.  
It combines recipes, character interactions, race simulation, and world tour exploration in one experience.

## 🌟 App Story

Radiator Springs is imagined as a food-and-racing town where Lightning McQueen, Mater, and friends welcome players into a journey of:
- local themed dishes
- Filipino food culture
- world food stops
- race events with champions

This app is designed like a light story mode: you start at home, unlock features through login, explore food systems, then move into race and world-tour gameplay.

## 🎬 Story Modes

### 🏠 Home / Welcome
The intro scene. Lightning McQueen and Mater welcome the user and set the theme.

### 📖 The Story of Radiator Springs
Full narrative mode telling how the town became the Home Of The Recipe. Covers McQueen's arrival, the digital kitchen, and the world tour origins.

### 🔐 Login / Register
SQLite-based user login with admin support.

### 📋 Product List
Main recipe board with search/filter.

### 🍔 Radiator Springs Food
Cars-themed recipe section.

### 🇵🇭 Filipino Food List
Traditional Filipino dishes and entries.

### 🤖 Finn-Holley AI Chatbot
Character-style assistant with 7 selectable personalities:
- Finn McMissle, Holley Shiftwell, Rod Redline, Tomber, Leland Turbo, Miles Axelrod, Mater

Handles:
- recipe questions
- greetings (English/Tagalog flow)
- race-related prompts (e.g., schedule / next racers)

### 🏁 Event Race
Expanded race simulation mode with racer rooting, multiple conditions, and lap-based standings.

### 🌍 World Tour Recipe
Mission-first world tour mode with recipe unlock progression.

### ⚙️ Settings
Account/status and app preferences.

### ℹ️ About
App information, version, and contact details.

## 🎮 Gameplay-Like Systems

## 🏁 Event Race Mode
- Large racer roster (22 drivers: classic + added world racers)
- Track selection includes:
  - Radiator Springs Speedway
  - Coastal Circuit
  - Desert Loop
  - Philippine Clark International Speedway (Pampanga)
  - Batangas Racing Circuit (Rosario, Batangas)
  - Fuji Speedway
- Weather + laps affect simulation
- Race mode selection (`Simulator` / `Arcade`)
- Rooting system: choose racers to support before race start
- Lap-based finish model (winner is lowest total race time)
- Podium + full standings output with Total, Avg Lap, and Best Lap

## 🌍 World Tour Mode
- Shows `map-of-the-world.png` before tour begins
- User selects **starting country**
- `Start World Tour` / `Reset Tour` flow
- Requires completing **5 missions** before haunting phase
- Each mission attempt has **70% success chance**
- Haunting phase unlocks language recipes (English, Filipino, Italian)
- Final delivery step: send completed mission package to **Sally and Lizzie**

## 🧩 What The App Includes

- Character-themed UI and storytelling
- Dark navigation/sidebar theme with improved menu visibility
- Recipe browsing and categories
- SQLite authentication
- Admin visibility for user management
- Recipe chatbot experience with 7 characters
- Race mode and world-tour mode
- Expanded Filipino and Radiator Springs recipe knowledge base

## 🛠 Tech Stack

- Python 3.13
- Streamlit
- SQLite (`radiator_springs.db`)

## 📦 Installation

```powershell
python -m venv venv
venv\Scripts\activate
pip install streamlit requests
```

## ▶️ Run

```powershell
streamlit run app.py
```

Open the URL shown in terminal (usually `http://localhost:8501`).

## 🔑 Default Admin

- Username: `admin`
- Password: `admin123`

> ⚠️ For production, replace default credentials and strengthen authentication before deploying. See Security Notes below.

## 🔒 Security Notes

### Audit Findings
The following issues were identified in the current codebase:

- **XSS Vulnerability**: The chatbot renders user messages directly into HTML via `st.markdown(..., unsafe_allow_html=True)` without escaping. Malicious input like `<script>` tags will execute in the browser.
- **Weak Password Hashing**: SHA-256 is used instead of a purpose-built password hash (e.g., `bcrypt`, `argon2-cffi`). Rainbow-table attacks are trivial against SHA-256 hashed passwords.
- **Hardcoded Admin Password**: The default admin account is created with a hardcoded password (`admin123`) and the hint is exposed in the UI login panel.
- **No Rate Limiting**: The login flow has no brute-force protection.
- **No Input Validation**: Registration fields (username, email, password) are not validated or sanitized before storage.

### Recommendations
- Escape user content before injecting into `st.markdown(..., unsafe_allow_html=True)` or switch to `st.write()` / `st.text()` for chat messages.
- Replace SHA-256 with `bcrypt` or `argon2-cffi` for password hashing.
- Remove the default admin hint from the UI and force a password change on first login.
- Add basic rate-limiting or account lockout after repeated failed login attempts.
- Validate username length, email format, and password complexity on registration.

## 📁 Main Files

- `app.py` — main application logic/UI
- `radiator_springs.db` — SQLite data
- `map-of-the-world.png` — world map asset
- `logo-of-app.png` — app logo
- `cars_2_mcquee12.png` — Lightning McQueen character image
- `cars_2_martin_(tow_mater).png` — Mater character image

## 📝 Recent Updates

### 2026-04-29
- Navigation restyled back to dark mode with improved sidebar/menu readability.
- Replaced deprecated Streamlit `use_container_width` usage with `width="stretch"`.
- Event Race updated with racer rooting selection and rooted-racer performance boost.
- Event Race standings now use lap-based total race times (no fixed `14s - 32s` clamp).
- World Tour updated to mission-gated progression: complete 5 missions first (70% success per attempt), then haunt enemies and unlock recipes.
- Added final World Tour completion step: send completed package to Sally and Lizzie.
- Security audit completed; XSS, weak hashing, and hardcoded credential issues documented.
- Chatbot expanded from 2 to 7 selectable characters (Finn, Holley, Rod, Tomber, Leland, Miles, Mater).
- Added "The Story of Radiator Springs" narrative page.
- Added "About" page with version and contact info.
- README updated with full asset list and security recommendations.

### 2026-04-28
- Navigation improved with section-based structure.
- Story modes expanded for Event Race + World Tour.
- Event Race roster expanded and track list updated.
- Time simulation adjusted to `14s - 32s`.
- World Tour now supports start-country selection.
- UI and emoji rendering cleanup/improvements.

Keep entries short and user-facing.

## ⚠️ Notes

- Built for local/demo usage.
- If emoji appears broken (`Ã......` text), ensure UTF-8 encoding and restart Streamlit.

