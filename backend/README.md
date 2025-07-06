# Backend

This directory contains the Flask application powering the Bookshelf Recommender API.

## Purpose
The backend exposes REST endpoints for user authentication, bookshelf management, friend connections and community groups. It also integrates Google Gemini Vision to extract book titles from uploaded images and uses external book APIs to generate recommendations.

## Key Files
- **app.py** – monolithic Flask application implementing all routes and models. Future work includes refactoring into Blueprints for maintainability.
- **requirements.txt** – Python dependencies required to run the server.

## Running
Install dependencies from `requirements.txt` and run `python backend/app.py`. The server reads configuration from environment variables described in the project root `README.md` and `.env.example`.

## Status
Active – basic features implemented, refactor planned.
