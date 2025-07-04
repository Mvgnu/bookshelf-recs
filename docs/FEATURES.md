# Features: Bookshelf Recommender

This document details the current and planned features of the application, expanding on the `README.md`.

## Core Feature: Bookshelf Analysis & Recommendation

**Status:** Partially Implemented (v0.2 using OCR, v0.3 target with Image LLM)

1.  **Image Input:**
    *   [x] File Upload (Frontend)
    *   [x] Direct Camera Capture (Frontend)
    *   [ ] Image validation (size, type) (Backend - basic implemented)
2.  **Book Detection:**
    *   [ ] **Image LLM Processing:** (v0.3 Target)
        *   [ ] Send image data to chosen LLM API (e.g., Gemini Vision).
        *   [ ] Craft effective prompt for identifying book titles and authors visible on spines/covers.
        *   [ ] Parse structured response from LLM (e.g., list of identified books).
        *   [ ] Handle API errors and rate limits gracefully.
    *   ~~[x] OCR-Based Detection: (v0.2 - To be removed)~~~
        *   ~~[x] Image preprocessing (contrast, sharpness, grayscale, thresholding).~~
        *   ~~[x] Tesseract OCR execution with multiple configurations.~~
        *   ~~[x] Basic text parsing and candidate filtering.~~
3.  **Recommendation Generation:**
    *   [x] Query External API (Google Books) based on detected book(s).
    *   [x] Extract relevant book metadata (title, author, description, cover, publisher, categories, etc.).
    *   [x] Basic duplicate filtering based on title similarity.
    *   [ ] Use **multiple** detected books from LLM for broader search criteria (v0.4 Target).
    *   [ ] Implement advanced recommendation logic (genre/author similarity) (v0.4 Target).
    *   [ ] Integrate alternative book data sources (Open Library, etc.) (v0.4 Target).
    *   [ ] Allow user filtering/preference settings for recommendations (v0.4 Target).
4.  **Results Display (Frontend):**
    *   [x] Show uploaded image preview.
    *   [x] Loading/Processing indicator during analysis.
    *   [x] Display list of detected books.
    *   [x] Display grid of recommended books with details (cover, title, author, description, metadata).
    *   [x] Tabbed interface for detected vs. recommended books.
    *   [x] Link to external book preview (e.g., Google Books).
    *   [x] Clear error message display.

## Planned Features (Post v0.3)

### Community & User Features (Target v0.5)

*   **User Accounts:**
    *   [ ] Secure registration and login (e.g., email/password, OAuth).
    *   [ ] User profile management.
*   **Personal Bookshelves:**
    *   [ ] Saving scanned bookshelves (requires database).
    *   [ ] Manually adding/editing books in the virtual shelf.
    *   [ ] Viewing/managing saved virtual bookshelves.
*   **Social Features:**
    *   [ ] Sharing virtual bookshelves (publicly or with specific users).
    *   [ ] Viewing friends' bookshelves/activity.
    *   [ ] Generating recommendations based on friends' overlapping libraries.
*   **Interaction & Tracking:**
    *   [ ] Creating reading lists (Want to Read, Reading, Read).
    *   [ ] Tracking reading progress.
    *   [ ] Rating and reviewing books.
    *   [ ] Basic discussion forum or comment sections.

### User Experience Enhancements (Target v0.6)

*   [ ] Dark Mode theme.
*   [ ] Accessibility audit and improvements (WCAG compliance).
*   [ ] Advanced search and filtering within results/bookshelves.
*   [ ] Integration with e-commerce platforms for purchasing books.
*   [ ] Push notifications for new recommendations or community activity (requires user opt-in).

### Technical Enhancements

*   [ ] Caching API responses (Google Books, LLM if applicable) to reduce costs and improve speed.
*   [ ] Asynchronous task processing for image analysis (e.g., using Celery) for long-running jobs.
*   [ ] Database implementation for users, bookshelves, reviews, etc.
*   [ ] Dedicated image processing service (if complexity grows significantly).
*   [ ] Comprehensive automated testing (unit, integration, end-to-end). 