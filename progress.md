# Progress Log

## 2024-05-05
- Added missing newline characters to multiple documentation and code files to satisfy POSIX text file conventions.
- Extended `Book` model with a `cover_image_url` column.
- Fixed `add_book_to_shelf` route to associate books via the many-to-many relationship instead of an undefined `bookshelf_id` field.

## 2024-05-06
- Replaced all `print` statements with structured `logging` calls.
- Enforced mandatory `SECRET_KEY` via environment variable.
- Added `sanitize_input` helper and integrated `bleach` for sanitization.
- Introduced basic PyTest suite with a sample model test.
- Updated requirements to include `bleach` and `pytest`.

## 2024-05-07
- Implemented recommendations rendering in the React frontend.
- Added a unit test for `sanitize_input` to improve security coverage.
- Documented environment variable setup in the README.


## 2024-05-08
- Created integration tests covering user registration, login and bookshelf CRUD.
- Fixed ESLint errors and added navigation with logout functionality.
- Removed stray shell prompts from React source files.

## 2024-05-09
- Added optional dark mode with theme toggle and persisted preference.
- Documented dark mode usage in README.
- Installed Python dependencies in tests to ensure passing suite.

## 2024-05-10
- Implemented JSON error handlers for 404 and 500 responses.
- Added integration test confirming 404 handler returns structured JSON.
- Verified test suite passes after installing dependencies.

## 2024-05-11
- Added integration test for the 500 error handler ensuring JSON responses.
- Documented linting limitations and offline installation notes.
- Updated refinement plan with additional tasks after code review.

## 2024-05-12
- Implemented a 405 error handler so unsupported methods return JSON.
- Added a new integration test for the 405 response.
- Documented the new error response in the API reference.

## 2024-05-13
- Added `/api/health` endpoint returning a simple status for monitoring.
- Configured logging level via `LOG_LEVEL` environment variable.
- Documented the endpoint in the README and API reference and added a test.

## 2024-05-14
- Implemented request caching for external book APIs using `requests-cache`.
- Added `LOG_LEVEL` and `CACHE_EXPIRY` examples in `.env.example`.
- Documented caching behavior in the README.

## 2024-05-15
- Made JWT token expiration configurable via a new `TOKEN_EXPIRY_HOURS` variable.
- Added example value to `.env.example` and updated README instructions.
- Created an integration test verifying the login route respects the configured expiry.

## 2024-05-16
- Updated README to reflect Gemini Vision integration and removed obsolete OCR references.
- Marked completed tasks in `docs/IMPLEMENTATION_PLAN.md` and `docs/FEATURES.md`.
- Added new refinement items for rate limiting, OpenAPI docs and offline lint workflow.

## 2024-05-17
- Implemented Flask-Limiter for global API rate limiting with configurable limit.
- Added a dedicated 429 error handler returning JSON.
- Documented rate limiting in README and API reference.
- Updated implementation plan and features lists to mark rate limiting completed.
- Expanded example `.env` with `RATE_LIMIT` variable.

## 2024-05-18
- Added `FriendRequest` model and new API routes for sending and accepting friend requests.
- Updated API docs and README with friend endpoint usage.
- Marked friend request feature in planning documents.

## 2024-05-19
- Implemented public bookshelf endpoints to list and view shared shelves.
- Documented new APIs in README and API reference.
- Updated features and implementation plan to mark shelf sharing.
- Added tests covering public shelf access.

## 2024-05-20
- Added endpoints to list outgoing friend requests and to cancel, decline or remove friendships.
- Updated API reference and README with the new friend management options.
- Extended integration tests for friend workflows covering cancel, decline and removal.

## 2024-05-21
- Created React `FriendManager` component with UI to send, accept and remove friend requests.
- Added navigation link to the new friends page and basic styling.
- Updated README and documentation to describe the friends UI.

## 2024-05-22
- Implemented `/api/spec` route returning a simple OpenAPI specification.
- Documented the endpoint in README and API reference.
- Marked OpenAPI documentation task complete in refinement notes.

## 2024-05-23
- Added `/api/users/<id>/bookshelves` endpoint so friends can view each other's shelves.
- Frontend now lets you view a friend's shelves from the Friends page.
- Updated API docs, README and feature list accordingly.
- Added integration test covering access rules for friend shelves.

## 2024-05-24
- Created Community model and endpoints to list, create, join and leave communities.
- Documented new routes in API reference and README.
- Updated planning docs noting community groups implementation.
- Added tests covering community creation and membership flows.

## 2024-05-25
- Added endpoint to list the communities a user belongs to and a DELETE route for community owners.
- Updated OpenAPI spec, README and API docs with the new community management functionality.
- Extended tests to cover listing personal communities and verifying deletion permissions.

## 2024-05-26
- Extended community responses with `owner_id` so the frontend can determine ownership.
- Created React `CommunityManager` component with UI to create, join, leave and delete communities.
- Added Communities tab to navigation and documented its usage in README and API reference.

## 2024-05-27
- Added `GET` and `PUT /api/communities/<id>` so owners can view and edit community details.
- Updated OpenAPI spec, README and API reference with the new endpoints.
- Documented the feature completion in planning docs and marked as implemented in features list.
- Added integration tests covering retrieval and update of community information.
