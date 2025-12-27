<h1 align="center">AETHER</h1>

<p align="center"><strong>Your AI-powered News & Tech Companion</strong></p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/Flask-3.1.2-green?logo=flask" alt="Flask">
  <img src="https://img.shields.io/badge/OpenAI-GPT--4o--mini-purple?logo=openai" alt="OpenAI">
  <img src="https://img.shields.io/badge/spaCy-NLP-09A3D5?logo=spacy" alt="spaCy">
  <img src="https://img.shields.io/badge/NewsAPI-News-ff6600" alt="NewsAPI">
  <img src="https://img.shields.io/badge/YouTube-API-red?logo=youtube" alt="YouTube">
  <img src="https://img.shields.io/badge/Reddit-API-FF4500?logo=reddit" alt="Reddit">
</p>

<p align="center">
  <a href="https://aether-news-trends-vpt4.onrender.com/" target="_blank">🔗 View Live Demo</a>
</p>

---

## Table of Contents

- [About](#about)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [API Keys](#api-keys)
- [Usage](#usage)

---

## About

AETHER is an intelligent AI-powered chatbot that aggregates real-time news, YouTube videos and Reddit discussions into a seamless conversational experience. Ask about any topic and get curated content with AI-generated insights.

Beyond news aggregation, AETHER also functions as a powerful general-purpose AI assistant capable of answering questions, having conversations and helping with everyday tasks - making it your all-in-one AI companion.

---

## Features

| Feature | Description |
|---------|-------------|
| **Multi-Source Aggregation** | Fetches news, YouTube videos and Reddit posts in real-time |
| **AI-Powered Responses** | Intelligent answers using OpenAI GPT-4o-mini |
| **17+ Response Tones** | Casual, professional, comic, sarcastic, genz, bollywood and more |
| **Aether's Briefing** | Summarized highlights with philosophical "Aether's Take" |
| **Smart Relevance Scoring** | Content ranked by relevance, engagement and recency |
| **Voice Input** | Speak your queries using Web Speech API |
| **Pause/Resume** | Stop and continue AI responses anytime |
| **Responsive Design** | Works on desktop, tablet and mobile |

---

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Backend** | Python, Flask, Gunicorn |
| **AI/ML** | OpenAI API, spaCy, scikit-learn, NLTK |
| **APIs** | NewsAPI, GNews, YouTube Data API, Reddit API |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript |

---

## Project Structure

```
aether-news-trends/
├── src/
│   ├── core/
│   │   ├── intent.py           # Intent classification & routing
│   │   ├── moderation.py       # Content safety filters
│   │   └── session_state.py    # Session memory & pagination
│   ├── data_ingest/
│   │   ├── fetch_news.py       # NewsAPI & GNews integration
│   │   ├── fetch_youtube.py    # YouTube API with smart ranking
│   │   └── fetch_reddit.py     # Reddit public API
│   ├── llm/
│   │   └── response_engine.py  # OpenAI LLM & tone detection
│   └── summary/
│       └── summarizer.py       # Briefing generation
├── webapp/
│   ├── app.py                  # Flask entry point
│   ├── routes/
│   │   └── chat.py             # Chat endpoints
│   ├── templates/
│   │   └── index.html          # UI template
│   └── static/
│       ├── css/style.css       # Glassmorphism UI
│       └── js/script.js        # Chat logic
├── requirements.txt
├── Procfile
└── .env                        # API keys (not tracked)
```

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/Mohit-Bagri/aether-news-trends.git
cd aether-news-trends
```

### 2. Create virtual environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 4. Configure environment variables

Create a `.env` file in the root directory:

```env
NEWS_API_KEY=your_newsapi_key
GNEWS_API_KEY=your_gnews_key
YOUTUBE_API_KEY=your_youtube_key
OPENAI_API_KEY=your_openai_key
AETHER_PORT=5050
```

### 5. Run the application

```bash
PYTHONPATH=$(pwd) python webapp/app.py
```

Open **http://127.0.0.1:5050** in your browser.

---

## API Keys

| Service | Purpose | Get Key |
|---------|---------|---------|
| NewsAPI | News articles | [newsapi.org](https://newsapi.org/) |
| GNews | Fallback news | [gnews.io](https://gnews.io/) |
| YouTube | Video search | [Google Cloud Console](https://console.cloud.google.com/) |
| OpenAI | AI responses | [platform.openai.com](https://platform.openai.com/) |

---

## Usage

### Basic Queries
- "What's happening in AI today?"
- "Show me news about climate change"
- "Find YouTube videos about machine learning"
- "Reddit discussions on cryptocurrency"

### Tone Switching
- "Switch to sarcastic mode"
- "Be more professional"
- "Talk like Shakespeare"

### Pagination
- "Show me more news"
- "More YouTube videos"
- "More Reddit posts"

---

<p align="center">
  Made in 🇮🇳 with ❤️ by <a href="https://github.com/Mohit-Bagri">MOHIT BAGRI</a>
</p>
