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

### 🔐 Login / Register
SQLite-based user login with admin support.

### 📋 Product List
Main recipe board with search/filter.

### 🍔 Radiator Springs Food
Cars-themed recipe section.

### 🇵🇭 Filipino Food List
Traditional Filipino dishes and entries.

### 🤖 Finn-Holley AI Chatbot
Character-style assistant for:
- recipe questions
- greetings (English/Tagalog flow)
- race-related prompts (e.g., schedule / next racers)

### 🏁 Event Race
Expanded race simulation mode with multiple racers, conditions, and standings.

### 🌍 World Tour Recipe
Map-first travel mode where users select a starting country before beginning the tour.

### ⚙️ Settings
Account/status and app preferences.

## 🎮 Gameplay-Like Systems

## 🏁 Event Race Mode
- Large racer roster (classic + added world racers)
- Track selection includes:
  - Radiator Springs Speedway
  - Coastal Circuit
  - Desert Loop
  - Philippine Clark International Speedway (Pampanga)
  - Batangas Racing Circuit (Rosario, Batangas)
  - Fuji Speedway
- Weather + laps affect simulation
- Time-based finish model (`14s - 32s`)
- Podium + full standings output

## 🌍 World Tour Mode
- Shows `map-of-the-world.png` before tour begins
- User selects **starting country**
- `Start World Tour` / `Reset Tour` flow
- Tour cards reorder from selected starting country

## 🧩 What The App Includes

- Character-themed UI and storytelling
- Recipe browsing and categories
- SQLite authentication
- Admin visibility for user management
- Recipe chatbot experience
- Race mode and world-tour mode

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

For production, replace credentials and strengthen auth/security.

## 📁 Main Files

- `app.py` — main application logic/UI
- `radiator_springs.db` — SQLite data
- `map-of-the-world.png` — world map asset

## 📝 Recent Updates

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
