# API Reference

This document summarizes the main backend endpoints.

## Authentication

- `POST /api/register` — Create a new user account.
- `POST /api/login` — Obtain a JWT token for future requests.

## Bookshelves

- `GET /api/bookshelves` — List current user's bookshelves.
- `POST /api/bookshelves` — Create a new bookshelf.
- `GET/PUT/DELETE /api/bookshelves/<id>` — Retrieve, update or delete a shelf you own.
- `POST /api/bookshelves/<id>/books` — Add a book to a shelf.
- `GET /api/public/bookshelves` — List all public bookshelves.
- `GET /api/public/bookshelves/<id>` — View a specific public shelf and its books.

## Books

- `DELETE /api/books/<id>` — Remove a book from a shelf you own.

## Friends

- `GET /api/friends` — List your confirmed friends.
- `GET /api/friends/requests` — View pending friend requests.
- `POST /api/friends/<user_id>` — Send a friend request or accept one if the user already requested you.
- `GET /api/friends/outgoing` — View friend requests you have sent that are still pending.
- `DELETE /api/friends/<user_id>` — Cancel/decline a request or remove a friend.
- `GET /api/users/<user_id>/bookshelves` — View another user's bookshelves. Friends see all shelves, others only public ones.

## Communities

- `GET /api/communities` — List existing communities.
- `POST /api/communities` — Create a new community (requires auth).
- `POST /api/communities/<id>/join` — Join a community.
- `DELETE /api/communities/<id>/leave` — Leave a community you belong to.
- `GET /api/communities/<id>/members` — List community members.
- `GET /api/communities/mine` — List communities you have joined.
- `GET /api/communities/<id>` — Retrieve details of a community.
- `PUT /api/communities/<id>` — Update a community you own.
- `DELETE /api/communities/<id>` — Delete a community you own.
  Responses from the list endpoints include an `owner_id` field so clients can
  determine whether the current user is the owner.

## Upload

- `POST /api/upload` — Upload an image of a bookshelf for analysis and recommendation.

## Status

- `GET /api/health` — Quick health check returning `{ "status": "ok" }`.
- `GET /api/spec` — Retrieve the OpenAPI specification for the API.

All authenticated routes require an `Authorization: Bearer <token>` header.

### Errors

Unknown routes return a JSON `{ "error": "Not found" }` response with a 404 status. Server errors return `{ "error": "Internal server error" }`.
Requests using unsupported HTTP methods return a JSON `{ "error": "Method not allowed" }` with a 405 status.
Exceeding the rate limit returns `{ "error": "Too many requests" }` with a 429 status.

