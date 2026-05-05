# 🚗 Cars Radiator Springs: Home Of The Cooking Recipe

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
Character-style assistant with 10 selectable personalities:

- 🎩 Finn McMissle
- 💫 Holley Shiftwell
- 🔧 Rod Redline
- 🚙 Tomber
- ⚡ Leland Turbo
- 🚗 Miles Axelrod
- 🚜 Mater
- 🧪 Professor Zundapp
- 🏎️ Lightning McQueen
- 🖤 Jackson Storm

Features improved orange/yellow glow design with preserved emojis. Handles:
- recipe questions and cooking guidance
- greetings (English/Tagalog flow)
- race-related prompts (e.g., schedule / next racers)
- retrieval-augmented generation (RAG) using the local recipe knowledge base
- agentic planning for menus, shopping lists, and step-by-step cook plans
- concise answer prompts such as "one-word" responses when requested
- Quick recipe suggestion buttons for fast navigation
- profanity/cuss filtering (chatbot refuses swearing and asks for respectful rephrase)
- non-repeating fallback/greeting style responses
- No Swearings on the AI Chatbot


### 🏁 Event Race
Expanded race simulation mode with racer rooting, multiple conditions, and lap-based standings.

### 🌍 World Tour Recipe
Mission-first world tour mode with recipe unlock progression.

### ⚙️ Settings
Account/status and app preferences.

### ℹ️ About
Redesigned About page with styled info cards, updated version panel, chatbot roster, and contact details.

## 🎮 Gameplay-Like Systems

## 🏁 Event Race Mode
- Large racer roster (24 drivers: classic + added world racers)
- Added new racers: Nikolai Javier Jr. and Daria Patrick
- **New Racer Images**: All racer cards now display character images instead of emojis for a more immersive experience
- **New Orange/Yellow Card Design**: All racer cards now feature warm orange/yellow gradients with glow effects and improved hover animations
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
- Requires completing **5 missions** before haunting enemy teams
- Each mission attempt has **70% success chance**
- **Enemy Teams**: Haunt **The Lemons** and **The Clippers** across different locations
- Haunting phase unlocks language recipes (English, Filipino, Italian)
- Final delivery step: send completed mission package to **Sally and Lizzie**
- All mission boards and tour cards feature warm orange/yellow glow styling

## 🧩 What The App Includes

- **Orange & Yellow Gradient Navigation**: Sidebar now features a vibrant orange-to-yellow gradient with glow effects and black text for clarity
- **Glowing Flex Animations**: Cards and components feature animated glow effects that pulse between orange and yellow
- **Bright Card Designs**: All cards use warm orange/yellow gradients with black text on bright backgrounds for maximum contrast and readability
- Character-themed UI and storytelling
- Recipe browsing and categories
- SQLite authentication with admin support
- Advanced Recipe Chatbot with 10 selectable characters (emojis preserved)
- Enhanced Race mode with orange/yellow themed cards
- World Tour mode with Lemons and Clippers as enemy teams
- Expanded Filipino and Radiator Springs recipe knowledge base
- Improved Settings tab with themed cards and options


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

## 📝 Recent Updates (That McQueen Update)

### 2026-05-05
- Added retrieval-augmented AI chatbot behavior using the local recipe knowledge base
- Added agentic recipe planning support for shopping lists, cooking plans, and menu suggestions
- Improved chatbot prompt handling for concise responses when asked for one-word answers
- Added 3 new chatbot responders: Professor Zundapp, Lightning McQueen, and Jackson Storm
- Added profanity/cuss-word refusal handling in chatbot responses
- Improved chatbot button and response box styling to orange/yellow with black-text readability
- Fixed Leland Turbo emoji mojibake rendering and refreshed responder emoji mapping
- Added new Event Race racers: Nikolai Javier Jr. and Daria Patrick
- Fixed local Event Race racer image loading and updated the app owner spotlight image path
- Replaced deprecated Streamlit `use_column_width` usage with `width` parameter in images
- Redesigned About page and updated version to **1.1.0** (May 5, 2026)

### 2026-05-04
- **Design Overhaul**: Complete transition to orange & yellow gradient theme with glow flex animations
- Navigation sidebar now features orange-to-yellow gradient background with glow shadow effects
- All navigation buttons and radio selectors use bright gradients with black text on light backgrounds
- Updated Event Race cards from navy to orange/yellow gradient with hover glow effects
- Updated Settings tab with polished orange/yellow styled settings cards and improved UI
- Updated Finn-Holley AI Chatbot design with improved styling while preserving all emojis (🤖, 🎩, 💫, 🔧, 🚙, etc.)
- World Tour updated with specific enemy teams: **Lemons** and **Clippers** (vs. generic "enemies")
- All hero boxes, recipe cards, character cards, and product cards now use warm orange/yellow gradients with black text
- Added animated glow effects to hero boxes and cards with pulsing shadow animations
- Tabs and buttons throughout app now styled with orange/yellow gradients and glow effects
- Mission success chance remains **70% per attempt** with improved mission board styling

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
- If emoji appears like Mojibake is a broken (`Ã......` text), ensure UTF-8 encoding and restart Streamlit. (Ask McQueen about that).

## 🚧 Deployment

- Deployment Is Still Under The Build Constructions and Don't Worry, It's Almost Done for It! hahaha!
- Link: 🛠️🏗️🚜👷🚧🏗️ Still On The Works! hahaha
- Mater and McQueen is still on the works hahahaha
