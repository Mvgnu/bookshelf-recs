# React Components

This directory contains the UI building blocks for the Bookshelf Recommender frontend.

## Components

- **BookshelfList.jsx** – lists the current user's bookshelves.
- **BookshelfDetail.jsx** – shows books within a shelf and allows deletion.
- **CommunityManager.jsx** – manage reading communities, with creation, search, join/leave and inline editing.
- **FriendManager.jsx** – manage friends and requests, plus browsing friend bookshelves.
- **LoginForm.jsx** / **RegisterForm.jsx** – authentication forms.

Each component uses `fetchWithAuth` for API requests and displays basic loading and error states.

All component files include a machine-readable metadata header using "musikconnect tags" to document purpose, inputs, outputs and dependencies.
