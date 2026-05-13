# Cars Radiator Springs: Home Of The Cooking Recipe

A Streamlit story app inspired by the *Cars* universe.  
It combines recipes, character interactions, race simulation, and world tour exploration in one experience.

## App Story

Radiator Springs is imagined as a food-and-racing town where Lightning McQueen, Mater, and friends welcome players into a journey of:
- local themed dishes
- Filipino food culture
- world food stops
- race events with champions

This app is designed like a light story mode: you start at home, explore recipes freely in guest mode, then move into race, chatbot, and world-tour gameplay. Login is optional and kept mainly for account/admin features.

## Story Modes

### Home / Welcome
The intro scene now uses image-based welcome cards for Lightning McQueen and Mater.

### Character List
New General page with roster sections for:
- Characters
- AI Agents
- Villains (Clippers/Lemons)
- Racers with image cards and descriptions

### The Story of Radiator Springs
Full narrative mode telling how the town became the Home Of The Recipe.

### Login / Register
SQLite-based user login with admin support. App pages are now free to use without login.

### Product List
Main recipe board with search/filter.

### Radiator Springs Food
Cars-themed recipe section.

### Filipino Food List
Traditional Filipino dishes and entries.

### Finn-Holley AI Chatbot
Character-style assistant with 10 selectable personalities and Google AI Studio (Gemini) real-world responses.

Key capabilities:
- recipe questions and cooking guidance
- greetings (English/Tagalog flow)
- race-related prompts (schedule / next racers)
- retrieval-augmented generation (RAG) from local recipe knowledge
- agentic planning for menus, shopping lists, and step-by-step cooking
- SQLite chat memory and response cache
- profanity/cuss filtering
- safe cybersecurity-defense guidance for legal/authorized testing workflows
- refuses harmful hacking requests

### AI CHAT AI Chatbot
Interactive page powered by Google AI Studio (Gemini), with RAG recipe context and Agentic AI helpers for real-world answers.

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
- Guest-mode access with login optional
- Advanced recipe chatbot with 10 selectable characters
- Google AI Studio (Gemini) chatbot support
- AI CHAT AI Chatbot page with RAG and Agentic AI support
- SQLite chat history and cached responses
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
- Google AI Studio / Gemini API

## Installation

```powershell
python -m venv venv
venv\Scripts\activate
pip install streamlit requests
```

Optional Gemini environment variable:

```powershell
$env:GOOGLE_API_KEY="your_google_ai_studio_key"
$env:GOOGLE_MODEL="gemini-1.5-flash"
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

## Google AI Studio Setup

The chatbot now uses Google AI Studio instead of OpenAI.

- Use a Google AI Studio API key in the chatbot setup panel, or set `GOOGLE_API_KEY`.
- Default model: `gemini-1.5-flash`
- Optional model override: `GOOGLE_MODEL`
- The app keeps local fallback responses when no Gemini key is configured.

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

- **v1.3.0 (May 13, 2026)**
  - Migrated chatbot provider from OpenAI to Google AI Studio (Gemini)
  - Added AI CHAT AI Chatbot page under Interactive
  - Added Google API key/model setup fields
  - Added SQLite chat history and response cache for chatbot flows
  - Made app pages free to use without login
  - Added full racer roster to Character List under General
  - Improved RAG + Agentic AI chatbot flows and safe defense responses

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

### 2026-05-13
- Replaced OpenAI integration with Google AI Studio (Gemini).
- Added AI CHAT AI Chatbot page for real-world Gemini responses with RAG and Agentic AI.
- Added Google API key/model setup using `GOOGLE_API_KEY`, `GOOGLE_MODEL`, and in-app session fields.
- Added SQLite chat memory and response caching.
- Removed login requirements from app pages; guest mode is now supported.
- Added the full racer roster with images and descriptions to Character List.

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
