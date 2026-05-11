# Cars Radiator Springs: Home Of The Cooking Recipe

A Streamlit story app inspired by the *Cars* universe.  
It combines recipes, character interactions, race simulation, and world tour exploration in one experience.

## App Story

Radiator Springs is imagined as a food-and-racing town where Lightning McQueen, Mater, and friends welcome players into a journey of:
- local themed dishes
- Filipino food culture
- world food stops
- race events with champions

This app is designed like a light story mode: you start at home, unlock features through login, explore food systems, then move into race and world-tour gameplay.

## Story Modes

### Home / Welcome
The intro scene now uses image-based welcome cards for Lightning McQueen and Mater.

### Character List
New General page with roster sections for:
- Characters
- AI Agents
- Villains (Clippers/Lemons)

### The Story of Radiator Springs
Full narrative mode telling how the town became the Home Of The Recipe.

### Login / Register
SQLite-based user login with admin support.

### Product List
Main recipe board with search/filter.

### Radiator Springs Food
Cars-themed recipe section.

### Filipino Food List
Traditional Filipino dishes and entries.

### Finn-Holley AI Chatbot
Character-style assistant with 10 selectable personalities.

Key capabilities:
- recipe questions and cooking guidance
- greetings (English/Tagalog flow)
- race-related prompts (schedule / next racers)
- retrieval-augmented generation (RAG) from local recipe knowledge
- agentic planning for menus, shopping lists, and step-by-step cooking
- profanity/cuss filtering
- safe cybersecurity-defense guidance for legal/authorized testing workflows
- refuses harmful hacking requests

### Event Race
Expanded race simulation with a large global roster and long-format race logic.

### World Tour Recipe
Mission-first mode with AI-agent team-up narrative versus the Lemons and Clippers.

### Settings
Account/status and app preferences.

### Info / About
Styled info cards, version panel, chatbot roster, contact details, and owner spotlight.

## Gameplay-Like Systems

## Event Race Mode
- Massive racer roster with expanded global lineup
- Racer cards use image assets
- Orange/yellow card glow styling
- Tracks:
  - Radiator Springs Speedway
  - Coastal Circuit
  - Desert Loop
  - Philippine Clark International Speedway (Pampanga)
  - Batangas Racing Circuit (Rosario, Batangas)
  - Fuji Speedway
- Weather + laps affect simulation
- Race mode selection (`Simulator` / `Arcade`)
- Full-grid participation (all racers run in both modes)
- Laps changed from `3-30` to `70-100`
- Yellow-flag race-control events
- Pit crew full-repair cycle every 15 laps (no lap reset)
- Massive crash handling with `OUT (DNF)` status
- Podium + full standings
- Persistent race battle summary + `Reset Race Battle` button

## World Tour Mode
- Shows `map-of-the-world.png` before tour begins
- User selects starting country
- `Start World Tour` / `Reset Tour`
- Complete 5 missions first (70% success per attempt)
- Enemy teams: Lemons and Clippers
- AI Agents team up to protect/recover recipes
- Haunting phase unlocks language recipes
- Final delivery step to Sally and Lizzie

## What The App Includes

- Orange & yellow gradient navigation and glow effects
- Character-themed UI and storytelling
- Recipe browsing and categories
- SQLite authentication with admin support
- Advanced recipe chatbot with 10 selectable characters
- Safe security-defense chatbot flow for authorized testing guidance
- Enhanced race mode and mission-based world tour
- Expanded owner spotlight including Nikolai's crew:
  - Nikolai Javier Jr.
  - Claudine Margaret Ricablanca
  - Gwyn Sapio

## Tech Stack

- Python 3.13
- Streamlit
- SQLite (`radiator_springs.db`)

## Installation

```powershell
python -m venv venv
venv\Scripts\activate
pip install streamlit requests
```

## Run

```powershell
streamlit run app.py
```

Open the URL shown in terminal (usually `http://localhost:8501`).

## Default Admin

- Username: `admin`
- Password: `admin123`

> For production, replace default credentials and strengthen authentication before deploying.

## Security Notes

### Audit Findings
- XSS risk in unsafe HTML rendering paths
- Weak password hashing (SHA-256 instead of bcrypt/argon2)
- Hardcoded default admin password
- No brute-force protection/rate limiting
- Limited registration input validation

### Recommendations
- Escape user content before unsafe HTML rendering
- Use `bcrypt` or `argon2-cffi`
- Remove default admin hint and force first-login password reset
- Add rate limiting/account lockout
- Validate username/email/password complexity

## Main Files

- `app.py` - main application logic/UI
- `radiator_springs.db` - SQLite data
- `map-of-the-world.png` - world map asset
- `logo-of-app.png` - app logo

## Version Summary

- **v1.2.0 (May 11, 2026)**
  - Character List page added
  - Home welcome cards switched to image-based Lightning/Mater cards
  - About page expanded with Claudine and Gwyn in Nikolai's crew
  - World Tour AI-agent protection narrative improvements
  - Finn-Holley chatbot safe cybersecurity-defense upgrade

- **v1.1.0 (May 5, 2026)**
  - Chatbot RAG/agentic improvements
  - New chatbot responders
  - Event Race roster expansion and UI improvements

## Recent Updates

### 2026-05-11
- Event Race full-grid upgrades, 70-100 laps, yellow flags, pit repairs, DNF crash-outs, and reset battle flow.
- Character List page added under General section.
- Home welcome card visuals switched from emoji-first to image-based.
- Owner spotlight expanded with Claudine Margaret Ricablanca and Gwyn Sapio.
- World Tour messaging updated for AI Agents vs. Lemons/Clippers.
- Finn-Holley chatbot updated for safe legal-defense cybersecurity guidance.

### 2026-05-05
- Added RAG + agentic recipe planning enhancements.
- Added new chatbot responders and profanity refusal handling.
- Improved orange/yellow UI styling and About page refresh.

## Notes

- Built for local/demo usage.
- If emoji text looks broken, ensure UTF-8 encoding and restart Streamlit.

## Deployment

- Live app: https://thehomeoftherecipecarsradiatorsprings.streamlit.app/
