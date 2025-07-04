# Bookshelf Recommender

An application that analyzes photos of bookshelves using AI to identify books and provide personalized recommendations.

## Current State (v0.2 - Pre-LLM Integration)

- **Frontend**: 
  - React application with image upload and camera capture.
  - Modern, responsive UI with tabs for organizing content.
  - Comprehensive book details display with cover images.
  - Preview capability for recommended books.
- **Backend**: 
  - Flask API currently using OCR for text extraction (to be replaced).
  - Advanced image processing for OCR enhancement (to be replaced).
  - Google Books API integration for recommendation data.
- **Core Features**:
  - Upload or capture bookshelf images.
  - Rudimentary OCR-based book detection (identified as inaccurate, pending replacement).
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
- [ ] Social recommendations based on similar users.
- [ ] Reading lists and book tracking.
- [ ] Community ratings and reviews.
- [ ] Book clubs and discussion forums.

### User Experience Enhancements (v0.6)

- [ ] Dark mode and accessibility improvements.
- [ ] Reading progress tracking.
- [ ] One-click purchase options from various retailers.

## Technical Roadmap

(See `docs/IMPLEMENTATION_PLAN.md` for more detail)

- [ ] **Implement Image LLM API integration (e.g., Google Gemini Vision)**.
- [ ] **Set up secure API key handling (`.env`)**.
- [ ] **Refactor backend `detect_books` function**.
- [ ] Migrate image processing to dedicated service (Future).
- [ ] Implement proper data storage with database (e.g., PostgreSQL, SQLite for community features).
- [ ] Create user authentication system (e.g., Flask-Login, JWT).
- [ ] Build API endpoints for community features.
- [ ] Add ML model for book cover visual recognition (Advanced Future).
- [ ] Deploy to production environment (e.g., Heroku, Vercel, AWS).

## Getting Started

### Prerequisites

- Node.js and npm
- Python 3.7+
- **Image LLM API Key**: An API key for the chosen service (e.g., Google AI Studio for Gemini) - store in `backend/.env`.
- Tesseract OCR (Optional - will be removed post-LLM integration)
- OpenCV (Optional - will be removed post-LLM integration)

### Installation

1. Clone the repository
2. Set up the backend:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate
   # Create .env file and add API Key: echo "GOOGLE_API_KEY='YOUR_API_KEY_HERE'" > .env
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