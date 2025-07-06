# Refinement Notes

Based on the current codebase and `docs/IMPLEMENTATION_PLAN.md`, several areas can be improved or require further work:

1. **Automated Testing**
   - Introduced initial PyTest suite (`tests/`) covering model logic. Expand with integration tests and frontend coverage.
2. **Error Handling & Logging**
   - Consolidated logging: replaced all `print` statements with structured `logging`.
   - Standardize API error responses using consistent JSON schemas. Implemented basic 404/500 handlers returning JSON.
3. **Security Improvements**
   - Enforce `SECRET_KEY` via environment variable at startup.
   - Added `sanitize_input` helper using `bleach` and applied to user-supplied fields.
4. **Database Schema**
   - Consider migrations via `Flask-Migrate` to evolve the schema smoothly.
5. **LLM Integration Resilience**
   - Implement retries and graceful degradation if the Gemini API fails or rate limits are hit.
6. **Frontend Enhancements**
   - Dark mode toggle implemented. Still need to perform an accessibility audit and improve contrast.
   - Provide user feedback for long‑running operations (uploading, API calls) beyond current spinners.
7. **Performance & Deployment**
   - Investigate caching external API responses.
   - Plan for production deployment with a WSGI server and environment specific settings.
   - Rate limiting implemented to protect the API from abuse.
8. **Documentation**
    - Expand README with development scripts and test instructions.
    - ~~Document API endpoints formally using OpenAPI or similar.~~ (completed)

## Newly Identified Tasks

- Expand test coverage to include frontend components.
- Perform a formal accessibility audit and address any issues found.
- ~~Resolve ESLint dependency installation for offline environments.~~ (install_offline_node.sh added)
- ~~Investigate token revocation/refresh mechanisms for improved security.~~ (implemented `/api/token/refresh` and `/api/logout`)
- ~~Implement rate limiting with `Flask-Limiter` to mitigate abuse.~~ (completed)
- ~~Generate an OpenAPI specification for the REST API.~~ (completed)
- ~~Provide offline-capable npm packages or setup script to support linting without network access.~~ (install_offline_node.sh)
- ~~Embed musikconnect tags across frontend components for metadata.~~ (implemented)
- ~~Implement friend request system for user connections.~~ (completed)
- ~~Implement UI components for managing friend requests and friends list.~~ (completed)
- ~~Viewing friends' bookshelves.~~ (completed)
  - Introduce notification system to alert users of new requests or bookshelf activity.
  - ~~Explore community or group bookshelf features for collaborative lists.~~ (implemented basic communities)
  - ~~Design community/group bookshelf model and endpoints for collaborative collections.~~ (implemented)
  - Added endpoint to list user's communities and ability for owners to delete a community.
  - ~~Create frontend UI for managing communities (list, join, leave, delete).~~ (implemented)
  - Added endpoints to retrieve and update community details.
  - Added search endpoint for communities and inline editing in the UI.

### Additional Opportunities
- Implemented a 405 handler returning JSON when HTTP methods are not allowed.
- Ship a `.env.example` file documenting required environment variables.
- Refactor large `app.py` into Blueprints for maintainability.
- Explore caching for external API calls to reduce latency and rate limit issues.
- Caching of Google Books API responses implemented via `requests-cache` with configurable expiry.
- Add a `/api/health` endpoint for uptime checks (implemented).
- Configure logging level via `LOG_LEVEL` environment variable (implemented).
- JWT token expiry configurable via `TOKEN_EXPIRY_HOURS` environment variable (implemented).
- Public bookshelf sharing implemented via new endpoints. Group discussion features remain to be explored.
- Friend removal and request cancellation endpoints added. Frontend features pending.
- Add in-app notifications for community events and friend requests.
 - ~~Investigate implementing JWT refresh tokens for longer sessions.~~ (basic refresh endpoint added)

- ~~Replace deprecated `Query.get` calls with `db.session.get` to silence SQLAlchemy warnings.~~ (completed)
- ~~Provide a script or packaged dependencies so ESLint can run offline.~~ (install_offline_node.sh)
- Refactor backend into Blueprints for better maintainability.
- Blueprint refactor investigated but deferred due to circular import issues.
