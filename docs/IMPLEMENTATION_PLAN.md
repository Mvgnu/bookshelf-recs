# Implementation Plan: Bookshelf Recommender

This document outlines the phased implementation strategy and technical decisions.

## Phase 1: Core Functionality - Image LLM Integration (v0.3)

**Goal:** Replace inaccurate OCR with a robust Image LLM for book detection.

**Tasks:**

1.  **Setup API Key Handling:** [x]
2.  **Integrate Image LLM API:** [x]
3.  **Backend Cleanup:**
    *   [x] Remove Tesseract and OpenCV dependencies.
    *   [x] Update comments and docstrings in `backend/app.py`.
4.  **Testing:** [x] Automated backend tests implemented with PyTest.

## Phase 2: Recommendation Enhancement (v0.4)

**Goal:** Improve the quality and relevance of book recommendations.

**Tasks:**

1.  **Utilize Full LLM Output:** [x] Modified `get_recommendations` to use multiple (up to 5) books identified by the LLM.
2.  **Advanced Algorithms:** [In Progress] Implemented basic content-based filtering using categories from Google Books API. Further refinement possible.
3.  **Data Source Expansion:** [x] Integrated Open Library Search API as a supplementary source.
4.  **User Preferences:** [Deferred] Requires frontend changes and more specific user direction.

## Phase 3: Community Features & Persistence (v0.5) - COMPLETE

**Goal:** Introduce user accounts and allow saving/sharing of bookshelves.

**Tasks:**

1.  **Database Setup:**
    *   [x] Choose database (SQLite for now).
    *   [x] Define schema (User, Bookshelf, Book models).
    *   [x] Integrate ORM (SQLAlchemy).
2.  **Authentication:**
    *   [x] Implement registration/login.
    *   [x] Secure password hashing (bcrypt).
    *   [x] Implement JWT for session management.
3.  **Backend API Endpoints:** 
    *   [x] Create CRUD endpoints for Bookshelves and Books.
    *   [x] Secure endpoints using JWT decorator.
4.  **Frontend Integration:** 
    *   [x] Build UI components (Login/Register Forms, Bookshelf List, Bookshelf Detail).
    *   [x] Implement state management for auth and views.
    *   [x] Integrate API calls for CRUD operations.
    *   [x] Add basic styling and loading/error handling.

## Phase 4: UX Polish & Advanced Features (v0.6+)

**Goal:** Refine the user experience and add value-added features.

**Tasks:**

1.  **UI Refinements:** [x] Dark Mode implemented. Accessibility improvements and advanced styling pending.
2.  **Feature Additions:** [ ] Reading progress tracking, purchase links, book search within shelves.
    * Public bookshelf sharing implemented via `is_public` flag and new endpoints.
    * Friend request system implemented for connecting users.
    * React UI for managing friends and requests.
    * Endpoint and UI to view a friend's bookshelves.
    * Community groups with join/leave endpoints for shared shelves.
    * Endpoint to list user's communities and allow owners to delete a community.
    * Endpoint to view and update community details.
    * Search communities by name and edit them via the UI.
3.  **Performance Optimization:** [x] Caching, async tasks (if needed), database indexing.
4.  **Rate Limiting:** [x] Protect API endpoints using Flask-Limiter to mitigate abuse.
5.  **Deployment:** [ ] Prepare for production (e.g., switch DB, configure WSGI server).

## Technology Stack Rationale

-   **Frontend:** React (Vite)
-   **Backend:** Python/Flask
-   **Image Analysis:** Image LLM (Google Gemini Vision)
-   **Book Data:** Google Books API, Open Library API
-   **Database:** SQLite + SQLAlchemy (Current), PostgreSQL (Potential Future)
-   **Auth:** Bcrypt (Hashing), PyJWT (Tokens) 
