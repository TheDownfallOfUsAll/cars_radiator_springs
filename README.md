# Cars Radiator Springs: Home Of The Recipe

A Streamlit app inspired by the *Cars* universe, mixing recipes, character-themed interactions, and racing mini-features in one experience.

## Story Behind The App

This app imagines Radiator Springs as more than a stop on Route 66.  
In this version of the story, Lightning McQueen, Mater, and friends share food culture from their town and around the world.

The app combines:
- Cars-themed food ideas
- Filipino dishes and recipe discovery
- Character-based chatbot interactions
- Event race simulation
- World tour food stops with a map-first flow

The goal is to make a playful app where users can explore recipes while staying in a Cars-style setting.

## Features

- `🏠 Home / Welcome`: Character welcome screen
- `🔐 Login / Register`: SQLite authentication with admin user view
- `📋 Product List`: Search/filter recipes and items
- `🍔 Radiator Springs Food`: Cars-themed menu section
- `🇵🇭 Filipino Food List`: Filipino dishes
- `🤖 Finn-Holley AI Chatbot`: Recipe Q&A and race prompts
- `🏁 Event Race`: Multi-racer race simulation with standings
- `🌍 World Tour Recipe`: Country-based recipe tour with map briefing
- `⚙️ Settings`: Account and preference controls

## Tech Stack

- Python 3.13
- Streamlit
- SQLite (`radiator_springs.db`)

## Installation

From the project folder:

```powershell
python -m venv venv
venv\Scripts\activate
pip install streamlit requests
```

## Run The App

```powershell
streamlit run app.py
```

Then open the local URL shown by Streamlit (usually `http://localhost:8501`).

## Default Admin Account

- Username: `admin`
- Password: `admin123`

Change this in production before sharing publicly.

## Project Files

- `app.py`: Main Streamlit application
- `radiator_springs.db`: SQLite database
- `map-of-the-world.png`: Map shown before the world tour starts

## Recent Updates

### 2026-04-28
- Navigation layout refactor with section-based browsing.
- World Tour now supports selecting a starting country before starting.
- Event Race expanded with additional racers and more tracks.
- Race simulation updated to time-based results in the `14s–32s` range.
- Emoji and text rendering cleanup after encoding issues.
- UI polish updates for cards/buttons/sidebar presentation.

## How To Add Future Updates

If someone updates the app, append a new dated entry under **Recent Updates** in this format:

```md
### YYYY-MM-DD
- Short change summary 1
- Short change summary 2
- Any migration/setup notes
```

Keep each bullet concise and user-facing.

## Notes

- The app is designed for local/demo use.
- If text or emoji looks broken, ensure files are UTF-8 and restart Streamlit.
