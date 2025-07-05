# Bookshelf Recommender

An application that analyzes photos of bookshelves using AI to identify books and provide personalized recommendations.

## Current State (v0.3 - Image LLM Integrated)

- **Frontend**: 
  - React application with image upload and camera capture.
  - Modern, responsive UI with tabs for organizing content.
  - Comprehensive book details display with cover images.
  - Preview capability for recommended books.
- **Backend**:
  - Flask API now uses Google Gemini Vision for text extraction.
  - OCR and OpenCV dependencies have been removed.
  - Google Books API integration for recommendation data.
- **Core Features**:
  - Upload or capture bookshelf images.
  - Multimodal book detection powered by Gemini Vision.
  - Recommendations based on detected books.
  - Mobile-friendly responsive design.

**Note:** The current OCR-based book detection (v0.2) has proven unreliable. The project is now pivoting to use a multimodal Large Language Model (Image LLM) for improved accuracy, as outlined below.

## Vision & Planned Improvements

(See `docs/VISION.md` and `docs/FEATURES.md` for more detail)

### Foundational: Image LLM Integration (v0.3)

- [ ] **Replace OCR with Image LLM**: Integrate a service like Google Gemini Vision or OpenAI GPT-4V for robust book spine/cover text recognition.
- [ ] **API Key Management**: Securely handle API keys using environment variables.
- [ ] **Refine Recommendation Trigger**: Use the high-quality output from the LLM to generate more relevant recommendations.

### Improved Recommendations (v0.4)

- [ ] Analyze **all** detected books from LLM output.
- [ ] Implement genre-based recommendation algorithms.
- [ ] Add author similarity matching.
- [ ] Incorporate popularity and rating metrics.
- [ ] Enable filtering recommendations by preferences.
- [ ] Integrate with multiple book databases (Open Library, Goodreads data).

### Community Features (v0.5)

- [ ] User accounts and authentication.
- [ ] Personal virtual bookshelf storage (Database implementation required).
- [ ] Bookshelf sharing capabilities.
- [ ] Friend connections between users.
- [ ] Social recommendations based on similar users.
- [ ] Reading lists and book tracking.
- [ ] Community ratings and reviews.
- [ ] Book clubs and discussion forums.

### User Experience Enhancements (v0.6)

- [x] Dark mode toggle (button in the UI).
- [ ] Accessibility improvements.
- [ ] Reading progress tracking.
- [ ] One-click purchase options from various retailers.

## Technical Roadmap

(See `docs/IMPLEMENTATION_PLAN.md` for more detail)

- [x] **Implement Image LLM API integration (e.g., Google Gemini Vision)**.
- [x] **Set up secure API key handling (`.env`)**.
- [x] **Refactor backend `detect_books` function**.
- [ ] Migrate image processing to dedicated service (Future).
- [x] Implement proper data storage with database (e.g., PostgreSQL, SQLite for community features).
- [x] Create user authentication system (e.g., Flask-Login, JWT).
- [x] Build API endpoints for community features.
- [ ] Add ML model for book cover visual recognition (Advanced Future).
- [ ] Deploy to production environment (e.g., Heroku, Vercel, AWS).

## Getting Started

### Prerequisites

- Node.js and npm
- Python 3.7+
- **Image LLM API Key**: An API key for the chosen service (e.g., Google AI Studio for Gemini) - store in `backend/.env`.

### Installation

1. Clone the repository
2. Set up the backend:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate
   # Copy .env.example and edit with your keys
   cp ../.env.example .env
   # Then update GOOGLE_API_KEY and SECRET_KEY values
   # Optional: adjust LOG_LEVEL, CACHE_EXPIRY, TOKEN_EXPIRY_HOURS or RATE_LIMIT if needed
   pip install -r requirements.txt
   ```
3. Set up the frontend:
   ```bash
   cd frontend
   npm install
   ```

### Running the Application

1. Start the backend server:
   ```bash
   cd backend
   source venv/bin/activate
   python app.py
   ```
2. Start the frontend development server:
   ```bash
   cd frontend
   npm run dev
   ```
3. Access the application at http://localhost:5173

### Running Tests

Backend tests use `pytest`.

```bash
pytest -q
```

Ensure dependencies are installed via `pip install -r backend/requirements.txt` before running tests.
The application also requires a `SECRET_KEY` environment variable to be set.

Additional endpoint details are available in [docs/API_REFERENCE.md](docs/API_REFERENCE.md).
The backend exposes a simple health check at `/api/health` which returns `{ "status": "ok" }` when the server is running.
You can retrieve a machine-readable OpenAPI specification of all endpoints at `/api/spec`.

External book API responses are cached using `requests-cache`. The cache file lives in `books_cache.sqlite` and defaults to a 24 hour expiry. You can change this period with the `CACHE_EXPIRY` environment variable.
JWT tokens expire after one hour by default. Adjust `TOKEN_EXPIRY_HOURS` in your `.env` to modify the lifespan.
API requests are rate limited. The default is `200 per hour`, configurable via the `RATE_LIMIT` environment variable. Login attempts are further limited to `5 per minute`.

### Friends

After logging in, open the **Friends** tab in the navigation bar to manage your connections. The page lets you:

- Send a request by entering another user's ID.
- Accept or decline incoming requests.
- Cancel outgoing requests you've sent.
- View your current friends and unfriend them if desired.
- Browse a friend's bookshelves by clicking **View Shelves** next to their name.

The underlying API uses `/api/friends/<user_id>` for sending, accepting, cancelling or removing friendships. Lists of friends and pending requests are available from the `/api/friends`, `/api/friends/requests` and `/api/friends/outgoing` endpoints.
To see another user's shelves directly you can call `/api/users/<id>/bookshelves` (friends can view all shelves, others only public ones).

### Public Bookshelves

Bookshelves can be marked as `is_public` so other users can browse them. Access all public shelves at `/api/public/bookshelves` and view a specific shelf (including its books) via `/api/public/bookshelves/<id>`.

### Communities

Create or join reading communities to share recommendations with groups of friends. Use `/api/communities` to list or create communities. Join with `/api/communities/<id>/join`, leave with `/api/communities/<id>/leave`, and view members via `/api/communities/<id>/members`. Retrieve your joined communities with `/api/communities/mine`.
View a specific community with `GET /api/communities/<id>` or update its name and description via `PUT /api/communities/<id>` (owner only). Owners can remove groups using `DELETE /api/communities/<id>`.
The Communities tab in the app allows you to browse all groups, create new ones, join or leave existing communities, and delete communities you own.
API responses for listing communities include an `owner_id` field so the frontend can display delete options only for communities owned by the logged-in user.

### Dark Mode

Use the **Dark Mode** button (found in the navigation bar or below the login forms) to switch between light and dark themes. Your choice is saved in the browser so it persists across visits.

### Linting

Run `npm run lint` inside the `frontend` directory to check code style. The command relies on devDependencies which must be installed ahead of time. In offline environments, ensure `node_modules` is available or install from a local cache, otherwise ESLint will fail to load `@eslint/js`.
