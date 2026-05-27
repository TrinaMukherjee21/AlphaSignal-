# Trade Sentiment Dashboard

A full-stack real-time sentiment trading dashboard.

## Project Structure

```
trade-sentiment/
  backend/
    scrapers/    # Data collection scripts (News, Reddit, etc.)
    kafka/       # Kafka producers and consumers
    nlp/         # Sentiment analysis logic
    api/         # FastAPI endpoints
    db/          # Database models and migrations
    requirements.txt
  frontend/      # Frontend dashboard (React/Vite)
  docker-compose.yml
  .env.example
  README.md
```

## Setup

1.  **Clone the repository.**
2.  **Infrastructure**: Run `docker-compose up -d` to start Kafka, Zookeeper, PostgreSQL, and Redis.
3.  **Backend**:
    - Create a virtual environment: `python -m venv venv`
    - Activate it: `source venv/bin/activate` (or `venv\Scripts\activate` on Windows)
    - Install dependencies: `pip install -r backend/requirements.txt`
4.  **Environment**: Copy `.env.example` to `.env` and fill in your API keys.

## Features (Planned)
- Real-time sentiment analysis of financial news and social media.
- Live trading dashboard with sentiment indicators.
- Historical sentiment data visualization.
