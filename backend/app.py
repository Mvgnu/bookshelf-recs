import os
import uuid
# import re # No longer needed for basic LLM parsing
# import cv2 # No longer needed
# import numpy as np # No longer needed
from flask import Flask, request, jsonify, send_from_directory, g # Added g
from flask_cors import CORS
from PIL import Image # Still needed for handling image uploads
# import pytesseract # No longer needed
import requests
# from collections import Counter # No longer needed
from dotenv import load_dotenv
import google.generativeai as genai
import requests_cache
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import jwt # For JWT token generation/decoding
from datetime import datetime, timedelta, timezone # For setting token expiry
from functools import wraps # Added for decorator
import logging  # Import the logging library
import bleach  # For sanitizing user input

# Load environment variables from .env file
load_dotenv()  # Takes environment variables from .env

# --- Configure Logging ---
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
numeric_level = getattr(logging, log_level, logging.INFO)
logging.basicConfig(level=numeric_level,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__) # Get a logger instance for this module
# --- End Logging Config ---

# Setup request caching to reduce API calls
cache_expiry = int(os.getenv('CACHE_EXPIRY', '86400'))  # defaults to 24h
requests_cache.install_cache('books_cache', expire_after=cache_expiry)

# Setup rate limiting
rate_limit = os.getenv('RATE_LIMIT', '200 per hour')
limiter = Limiter(key_func=get_remote_address, default_limits=[rate_limit])

# JWT token expiry in hours (default 1 hour)
token_expiry_hours = int(os.getenv('TOKEN_EXPIRY_HOURS', '1'))

# --- Simple OpenAPI Specification ---
OPENAPI_SPEC = {
    "openapi": "3.0.0",
    "info": {
        "title": "Bookshelf Recommender API",
        "version": "1.0.0",
    },
    "paths": {
        "/api/register": {"post": {"summary": "Create a new user"}},
        "/api/login": {"post": {"summary": "Log in and receive a token"}},
        "/api/bookshelves": {
            "get": {"summary": "List user's bookshelves"},
            "post": {"summary": "Create a new bookshelf"},
        },
        "/api/bookshelves/{id}": {
            "get": {"summary": "Retrieve a bookshelf"},
            "put": {"summary": "Update a bookshelf"},
            "delete": {"summary": "Delete a bookshelf"},
        },
        "/api/upload": {"post": {"summary": "Upload an image for analysis"}},
        "/api/friends": {"get": {"summary": "List confirmed friends"}},
        "/api/friends/requests": {"get": {"summary": "List incoming requests"}},
        "/api/friends/outgoing": {"get": {"summary": "List outgoing requests"}},
        "/api/friends/{user_id}": {
            "post": {"summary": "Send or accept a request"},
            "delete": {"summary": "Cancel, decline or remove"},
        },
        "/api/communities": {
            "get": {"summary": "List communities"},
            "post": {"summary": "Create a community"}
        },
        "/api/communities/{id}/join": {"post": {"summary": "Join a community"}},
        "/api/communities/{id}/leave": {"delete": {"summary": "Leave a community"}},
        "/api/communities/{id}/members": {"get": {"summary": "List community members"}},
        "/api/communities/mine": {"get": {"summary": "List user's communities"}},
        "/api/communities/{id}": {
            "get": {"summary": "Retrieve a community"},
            "put": {"summary": "Update a community"},
            "delete": {"summary": "Delete a community"},
        },
        "/api/users/{user_id}/bookshelves": {"get": {"summary": "View a user's bookshelves"}},
        "/api/public/bookshelves": {"get": {"summary": "List public shelves"}},
        "/api/public/bookshelves/{id}": {
            "get": {"summary": "View a public shelf"}
        },
        "/api/health": {"get": {"summary": "Health check"}},
        "/api/spec": {"get": {"summary": "Retrieve this OpenAPI spec"}},
    },
}

# --- Input Sanitization Helper ---
def sanitize_input(value: str) -> str:
    """Return a cleaned version of the user-supplied string."""
    if value is None:
        return None
    return bleach.clean(value, strip=True)
# --- End Sanitization Helper ---

# Configure the Gemini API key
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    logger.error("GOOGLE_API_KEY not found in environment. Uploads will be disabled.")
else:
    try:
        genai.configure(api_key=api_key)
        logger.info("Gemini API Key configured successfully.")
    except Exception as e:
        logger.error(f"Error configuring Gemini API: {e}")
        api_key = None  # Ensure api_key is None if configuration fails

# Create upload folder if it doesn't exist
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__, static_folder='../frontend/dist', static_url_path='/')
# --- Add JWT Secret Key Configuration ---
# IMPORTANT: Use a strong, secret key and keep it out of version control (e.g., in .env)
secret_key = os.getenv('SECRET_KEY')
if not secret_key:
    raise RuntimeError('SECRET_KEY environment variable not set.')
app.config['SECRET_KEY'] = secret_key
# --- End JWT Secret Key --- 

# Define the database name
DB_NAME = os.environ.get('DATABASE_NAME', 'bookshelf.db')

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}' # Configure SQLite URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Disable modification tracking
CORS(app)  # Enable Cross-Origin Resource Sharing for frontend requests
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit uploads to 16MB

# Initialize SQLAlchemy database extension
db = SQLAlchemy(app)
limiter.init_app(app)

# --- Error Handlers ---
@app.errorhandler(404)
def handle_404(e):
    """Return JSON response for 404 errors."""
    logger.warning(f"Route not found: {request.path}")
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(405)
def handle_405(e):
    """Return JSON response for method not allowed errors."""
    logger.warning(f"Method not allowed: {request.method} {request.path}")
    return jsonify({"error": "Method not allowed"}), 405


@app.errorhandler(429)
def handle_rate_limit(e):
    """Return JSON response when rate limit is exceeded."""
    logger.warning(f"Rate limit exceeded: {request.remote_addr}")
    return jsonify({"error": "Too many requests"}), 429


@app.errorhandler(500)
def handle_500(e):
    """Return JSON response for internal server errors."""
    logger.error(f"Internal server error: {e}")
    return jsonify({"error": "Internal server error"}), 500
# --- End Error Handlers ---

# Initialize the specific Gemini model we want to use
llm_model = None
if api_key:
    try:
        # Using gemini-1.5-flash as it's fast and suitable for this kind of task
        llm_model = genai.GenerativeModel('gemini-1.5-flash')
        logger.info("Gemini model (gemini-1.5-flash) loaded successfully.")
    except Exception as e:
        logger.error(f"Error initializing Gemini model: {e}")
        llm_model = None # Ensure model is None if init fails

# === Database Models === 

# Association table for the many-to-many relationship between Bookshelves and Books
shelf_books = db.Table('shelf_books',
    db.Column('bookshelf_id', db.Integer, db.ForeignKey('bookshelf.id'), primary_key=True),
    db.Column('book_id', db.Integer, db.ForeignKey('book.id'), primary_key=True)
)

class User(db.Model):
    """Data model for users."""
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False) # Added email
    # Increased length for stronger hashes, ensure nullable=False
    password_hash = db.Column(db.String(256), nullable=False) 
    
    # Relationship to Bookshelf (one-to-many)
    bookshelves = db.relationship('Bookshelf', backref='owner', lazy=True)

    def set_password(self, password):
        """Create hashed password using pbkdf2:sha256 method."""
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        """Check hashed password."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Bookshelf(db.Model):
    """Data model for user bookshelves."""
    __tablename__ = 'bookshelf'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, default='My Bookshelf')
    description = db.Column(db.String(250), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_public = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    # Relationship to Book (many-to-many)
    books = db.relationship('Book', secondary=shelf_books,
                            lazy='subquery', # Load books immediately when shelf is loaded
                            backref=db.backref('bookshelves', lazy=True))

    def __repr__(self):
        return f'<Bookshelf {self.name} (User ID: {self.user_id})>'

class Book(db.Model):
    """Data model for individual books.
       Stores core identifying information. Consider adding ISBN or OLID later for better uniqueness.
    """
    __tablename__ = 'book'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    # Storing authors as a simple comma-separated string for now
    # A separate Author table might be better for complex querying later
    authors = db.Column(db.String(255), nullable=True) 
    isbn = db.Column(db.String(13), unique=True, nullable=True) # Added ISBN field
    # Optional: Add fields like openlibrary_id, google_books_id, cover_image_url later
    cover_image_url = db.Column(db.String(255), nullable=True)  # Optional cover image
    added_at = db.Column(db.DateTime, server_default=db.func.now())
    
    # Note: The relationship back to Bookshelf is defined via the backref in Bookshelf.books

    def __repr__(self):
        return f'<Book {self.title}>'

# Friend request relationship between users
class FriendRequest(db.Model):
    """Represents a friendship invitation between two users."""
    __tablename__ = 'friend_request'
    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    addressee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending', nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def __repr__(self):
        return f'<FriendRequest from {self.requester_id} to {self.addressee_id}>'

# Association table between users and communities
community_members = db.Table(
    'community_members',
    db.Column('community_id', db.Integer, db.ForeignKey('community.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

class Community(db.Model):
    """Simple community/group for collaborative bookshelves."""
    __tablename__ = 'community'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.String(250))
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    owner = db.relationship('User', backref='owned_communities')
    members = db.relationship('User', secondary=community_members, backref='communities')

# === API Endpoints ===

@app.route('/api/hello')
def hello_world():
    """Simple test endpoint to confirm backend is running."""
    return {'message': 'Hello from Backend!'}


@app.route('/api/health')
def health_check():
    """Return a basic status message for monitoring."""
    return jsonify({'status': 'ok'}), 200


@app.route('/api/spec')
def openapi_spec():
    """Return a machine-readable OpenAPI specification."""
    return jsonify(OPENAPI_SPEC), 200

# --- JWT Token Required Decorator ---
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # Check if 'Authorization' header exists and has the Bearer token
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                # Split 'Bearer <token>'
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({"error": "Bearer token malformed"}), 401

        if not token:
            return jsonify({"error": "Token is missing"}), 401

        try:
            # Decode the token using the secret key
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            # Store the user ID in Flask's g object for access within the route
            g.user_id = data['user_id']
            logger.info(f"Token verified for user_id: {g.user_id}")
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Token is invalid"}), 401
        except Exception as e:
             logger.error(f"Token verification failed: {e}")
             return jsonify({"error": "Token verification failed"}), 401


        return f(*args, **kwargs)
    return decorated

@app.route('/api/upload', methods=['POST'])
@token_required # Protect this route
def upload_file():
    """
    Handles image uploads, triggers book detection via LLM, gets recommendations,
    saves results to user bookshelves, and returns the original detection/recommendation lists.
    """
    user_id = g.user_id # Get user ID from token
    
    # Check if LLM is configured and available
    if not api_key or not llm_model:
         logger.error("Upload attempt failed: LLM service is not available.")
         return jsonify({'error': 'Image analysis service is not available.'}), 503

    # --- File Handling --- 
    if 'bookshelfImage' not in request.files:
        logger.warning(f"User {user_id}: Upload failed - No file part.")
        return jsonify({'error': 'No file part in request'}), 400
    file = request.files['bookshelfImage']
    if file.filename == '':
        logger.warning(f"User {user_id}: Upload failed - No selected file.")
        return jsonify({'error': 'No selected file'}), 400
    if not file.mimetype.startswith('image/'):
        logger.warning(f"User {user_id}: Upload failed - Not an image file.")
        return jsonify({'error': 'Uploaded file is not an image.'}), 400

    filepath = None
    detected_books = []
    recommendations = []
    save_message = "" # Message about saving status

    try:
        # --- Save and Process Image --- 
        filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        logger.info(f"User {user_id}: File saved temporarily to: {filepath}")

        detected_books = detect_books_with_llm(filepath)
        recommendations = get_recommendations(detected_books)

        # --- Save Results to Database --- 
        if detected_books or recommendations: # Only proceed if there's something to save
            # Find/Create Target Bookshelves
            detected_shelf_name = "Detected from Upload"
            recs_shelf_name = "Recommendations from Upload"
            
            # Find user's first shelf OR the specific detected shelf
            detected_shelf = Bookshelf.query.filter_by(user_id=user_id, name=detected_shelf_name).first()
            if not detected_shelf:
                # Fallback to first shelf if specific one doesn't exist
                detected_shelf = Bookshelf.query.filter_by(user_id=user_id).order_by(Bookshelf.created_at).first()
            if not detected_shelf:
                 # If still no shelf, create the default "Detected" one
                 logger.info(f"User {user_id}: No existing shelf found for detected books. Creating '{detected_shelf_name}'.")
                 detected_shelf = Bookshelf(name=detected_shelf_name, user_id=user_id, description="Books automatically added from image uploads.")
                 db.session.add(detected_shelf)
                 db.session.flush() # Ensure shelf gets an ID if needed immediately
                 
            # Find or create the recommendations shelf
            recs_shelf = Bookshelf.query.filter_by(user_id=user_id, name=recs_shelf_name).first()
            if not recs_shelf:
                logger.info(f"User {user_id}: Creating '{recs_shelf_name}' shelf.")
                recs_shelf = Bookshelf(name=recs_shelf_name, user_id=user_id, description="Book recommendations generated from uploads.")
                db.session.add(recs_shelf)
                db.session.flush()

            # Add Detected Books
            added_detected_count = 0
            valid_detected_titles = [t for t in detected_books if t and not t.lower().startswith("error")] # Filter out errors
            if detected_shelf and valid_detected_titles:
                existing_titles_detected = {b.title.lower() for b in detected_shelf.books}
                for title in valid_detected_titles:
                    if title.lower() not in existing_titles_detected:
                        new_book = Book(title=title, authors=None, isbn=None) # Basic info for detected
                        # Add book to the shelf's collection
                        detected_shelf.books.append(new_book) 
                        # No need to add book to session separately if using relationship append
                        existing_titles_detected.add(title.lower())
                        added_detected_count += 1
            logger.info(f"User {user_id}: Added {added_detected_count} new detected books to shelf '{detected_shelf.name}'.")
            
            # Add Recommendations
            added_recs_count = 0
            if recs_shelf and recommendations:
                existing_titles_recs = {b.title.lower() for b in recs_shelf.books}
                for rec in recommendations:
                    rec_title = rec.get('title', 'Unknown Title')
                    if rec_title != 'Unknown Title' and rec_title.lower() not in existing_titles_recs:
                         # Extract authors correctly (it's a list in the recommendation data)
                         authors_list = rec.get('authors', [])
                         authors_str = ", ".join(authors_list) if authors_list else None
                         
                         new_rec_book = Book(
                             title=rec_title,
                             authors=authors_str,
                             isbn=None,
                             # Consider storing more fields like cover_image_url, isbn if the Book model supports them
                             # isbn=rec.get('isbn'), 
                             # cover_image_url=rec.get('image')
                         )
                         recs_shelf.books.append(new_rec_book)
                         existing_titles_recs.add(rec_title.lower())
                         added_recs_count += 1
            logger.info(f"User {user_id}: Added {added_recs_count} new recommended books to shelf '{recs_shelf.name}'.")
            
            if added_detected_count > 0 or added_recs_count > 0:
                 db.session.commit() # Commit all additions
                 save_message = f"Added {added_detected_count} detected and {added_recs_count} recommended books to your shelves."
            else:
                 save_message = "No new books needed to be added to your shelves."
                 # No db.session.commit() needed if nothing was added
        else:
            save_message = "No books detected or recommended to save."

    except Exception as e:
        db.session.rollback() # Rollback any potential partial adds on error
        logger.error(f"User {user_id}: Error during upload processing or saving: {e}", exc_info=True)
        # Ensure cleanup even if processing fails
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
                logger.info(f"User {user_id}: Cleaned up temporary file (on error): {filepath}")
            except OSError as rm_err:
                logger.error(f"User {user_id}: Error removing file during exception handling: {rm_err}")
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500
    finally:
        # Ensure the temporary file is always cleaned up
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
                logger.info(f"User {user_id}: Cleaned up temporary file (in finally): {filepath}")
            except OSError as rm_err:
                logger.error(f"User {user_id}: Error removing file in finally block: {rm_err}")

    # Return original results + save message
    return jsonify({
        'detected_books': detected_books,
        'recommendations': recommendations,
        'save_message': save_message # Add the message
    })

@app.route('/api/register', methods=['POST'])
def register_user():
    """Registers a new user."""
    data = request.get_json()
    
    # Input validation
    if not data or not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Missing username, email, or password'}), 400
        
    username = sanitize_input(data['username'].strip())
    email = sanitize_input(data['email'].strip().lower())
    password = data['password']
    
    # Basic validation checks (can be expanded)
    if len(username) < 3:
        return jsonify({'error': 'Username must be at least 3 characters long'}), 400
    if '@' not in email or '.' not in email:
         return jsonify({'error': 'Invalid email format'}), 400
    if len(password) < 6:
         return jsonify({'error': 'Password must be at least 6 characters long'}), 400

    # Check if user already exists (case-insensitive check for username/email)
    existing_user = User.query.filter(
        (db.func.lower(User.username) == db.func.lower(username)) | 
        (db.func.lower(User.email) == db.func.lower(email))
    ).first()
    if existing_user:
        return jsonify({'error': 'Username or email already exists'}), 409 # Conflict
        
    # Create new user instance
    new_user = User(username=username, email=email)
    new_user.set_password(password) # Hash the password before saving
    
    try:
        db.session.add(new_user)
        db.session.commit()  # Commit user first to get the ID
        logger.info(f"Registered new user: {username} (ID: {new_user.id})")
        
        # Create a default bookshelf for the new user
        default_shelf = Bookshelf(name=f"{username}'s Bookshelf", owner=new_user)
        db.session.add(default_shelf)
        db.session.commit()
        logger.info(f"Created default bookshelf for user: {username}")
        
        # Consider returning user info (without password hash) or a token
        return jsonify({
            'message': f'User {username} registered successfully!',
            'user': { 'id': new_user.id, 'username': new_user.username, 'email': new_user.email }
        }), 201 # Created
    except Exception as e:
        db.session.rollback()  # Rollback session on error
        logger.error(f"Error during registration DB commit: {e}")
        return jsonify({'error': 'Registration failed due to a server error.'}), 500

@app.route('/api/login', methods=['POST'])
@limiter.limit("5 per minute")
def login_user():
    """Logs a user in by verifying credentials and returns a JWT."""
    data = request.get_json()
    if not data or not data.get('identifier') or not data.get('password'):
        return jsonify({'error': 'Missing identifier (username or email) or password'}), 400

    identifier = sanitize_input(data['identifier'].strip())
    password = data['password']
    user = User.query.filter(
        (db.func.lower(User.username) == db.func.lower(identifier)) | 
        (db.func.lower(User.email) == db.func.lower(identifier))
    ).first()

    if user and user.check_password(password):
        # Login successful - Generate JWT
        try:
            expiry_hours = int(os.getenv('TOKEN_EXPIRY_HOURS', str(token_expiry_hours)))
            token_payload = {
                'user_id': user.id,
                'username': user.username,
                'exp': datetime.now(timezone.utc) + timedelta(hours=expiry_hours)
            }
            token = jwt.encode(
                token_payload, 
                app.config['SECRET_KEY'], 
                algorithm='HS256'
            )
            logger.info(f"User {user.username} logged in successfully. Token generated.")
            return jsonify({
                'message': f'User {user.username} logged in successfully!',
                'user': { 'id': user.id, 'username': user.username, 'email': user.email },
                'token': token # Return the generated token
            }), 200
        except Exception as e:
            logger.error(f"Error generating token for user {user.username}: {e}")
            return jsonify({'error': 'Login succeeded but failed to generate session token.'}), 500
    else:
        logger.warning(f"Login failed for identifier: {identifier}")
        return jsonify({'error': 'Invalid username/email or password'}), 401 

# --- Example Protected Endpoint --- 

@app.route('/api/verify_token', methods=['GET'])
@token_required # Use the decorator here
def verify_token():
    """Verifies a JWT token sent in the Authorization header."""
    # If @token_required passes, the token is valid and g.user_id is set
    logger.info(f"Token verified successfully via /api/verify_token for user_id: {g.user_id}")
    # Optionally return user info based on g.user_id if needed
    user = User.query.get(g.user_id)
    if user:
        user_data = {"id": user.id, "username": user.username, "email": user.email}
        return jsonify({"message": "Token is valid", "user": user_data}), 200
    else:
         # Should theoretically not happen if token was valid, but good practice
        return jsonify({"error": "User associated with token not found"}), 404

# --- Bookshelf & Book Management Endpoints --- 

# GET (all) and POST (create) for the LOGGED-IN user's bookshelves
@app.route('/api/bookshelves', methods=['GET', 'POST'])
@token_required # Requires login for both GET and POST
def handle_bookshelves():
    user_id = g.user_id # Get user_id from the token

    if request.method == 'GET':
        """Gets all bookshelves belonging to the logged-in user."""
        user_shelves = Bookshelf.query.filter_by(user_id=user_id).order_by(Bookshelf.created_at.desc()).all()
        shelves_data = []
        for shelf in user_shelves:
             shelves_data.append({
                 'id': shelf.id,
                 'name': shelf.name,
                 'description': shelf.description,
                 'is_public': shelf.is_public,
                 'book_count': len(shelf.books),
                 'created_at': shelf.created_at.isoformat() if shelf.created_at else None,
                 'updated_at': shelf.updated_at.isoformat() if shelf.updated_at else None
             })
        logger.info(f"Fetched {len(shelves_data)} bookshelves for user {user_id}")
        return jsonify(shelves_data), 200

    elif request.method == 'POST':
        """Creates a new bookshelf for the logged-in user."""
        data = request.get_json()
        if not data or not data.get('name'):
            return jsonify({'error': 'Bookshelf name is required'}), 400
            
        name = sanitize_input(data['name'].strip())
        description = sanitize_input(data.get('description', '').strip())
        is_public = data.get('is_public', False)
        
        if not name:
            return jsonify({'error': 'Bookshelf name cannot be empty'}), 400

        # Check for duplicate shelf name for the same user (optional but good practice)
        existing_shelf = Bookshelf.query.filter_by(user_id=user_id, name=name).first()
        if existing_shelf:
            return jsonify({'error': f'Bookshelf with name "{name}" already exists'}), 409 # Conflict

        new_shelf = Bookshelf(
            name=name, 
            description=description, 
            is_public=is_public,
            user_id=user_id # Associate with the logged-in user
        )
        
        try:
            db.session.add(new_shelf)
            db.session.commit()
            logger.info(f"Created bookshelf '{name}' for user ID {user_id}")
            # Return the created shelf data
            return jsonify({
                'id': new_shelf.id,
                'name': new_shelf.name,
                'description': new_shelf.description,
                'is_public': new_shelf.is_public,
                'book_count': 0,
                'created_at': new_shelf.created_at.isoformat(),
                'updated_at': new_shelf.updated_at.isoformat()
            }), 201 # Created
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create bookshelf '{name}' for user {user_id}: {e}")
            return jsonify({'error': 'Failed to create bookshelf'}), 500

# GET (specific), PUT (update), DELETE (specific) for a bookshelf
@app.route('/api/bookshelves/<int:shelf_id>', methods=['GET', 'PUT', 'DELETE'])
@token_required # Requires login
def handle_specific_bookshelf(shelf_id):
    user_id = g.user_id
    # Query for the shelf ensuring it belongs to the logged-in user
    shelf = Bookshelf.query.filter_by(id=shelf_id, user_id=user_id).first()

    if not shelf:
        logger.warning(f"Attempt to access or modify non-existent or unauthorized bookshelf {shelf_id} by user {user_id}")
        return jsonify({"error": "Bookshelf not found or access denied"}), 404

    if request.method == 'GET':
        """Gets details of a specific bookshelf owned by the user."""
        books_data = []
        for book in shelf.books:
            books_data.append({
                 'id': book.id,
                 'title': book.title,
                 'author': book.authors,
                 'isbn': book.isbn,
                 'cover_image_url': book.cover_image_url,
                 'added_at': book.added_at.isoformat() if book.added_at else None
            })
        logger.info(f"Fetched bookshelf {shelf_id} for user {user_id}")
        return jsonify({
            'id': shelf.id,
            'name': shelf.name,
            'description': shelf.description,
            'is_public': shelf.is_public,
            'created_at': shelf.created_at.isoformat(),
            'updated_at': shelf.updated_at.isoformat(),
            'books': books_data
        }), 200

    elif request.method == 'PUT':
        """Updates a specific bookshelf owned by the user."""
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required for update'}), 400

        # Update fields if they are provided in the request
        updated = False
        if 'name' in data:
            new_name = data['name'].strip()
            if not new_name:
                return jsonify({"error": "Bookshelf name cannot be empty"}), 400
            if new_name != shelf.name:
                 # Optional: check if the new name conflicts with another shelf of the same user
                 existing_shelf = Bookshelf.query.filter(Bookshelf.user_id == user_id, Bookshelf.name == new_name, Bookshelf.id != shelf_id).first()
                 if existing_shelf:
                     return jsonify({'error': f'Another bookshelf named "{new_name}" already exists'}), 409
                 shelf.name = new_name
                 updated = True
        if 'description' in data:
            shelf.description = data['description'].strip()
            updated = True
        if 'is_public' in data and isinstance(data['is_public'], bool):
            shelf.is_public = data['is_public']
            updated = True

        if not updated:
            return jsonify({"message": "No changes provided to update."}), 200 # Or 304 Not Modified

        try:
            db.session.commit()
            logger.info(f"Bookshelf {shelf_id} updated by user {user_id}")
            # Return the updated shelf data
            return jsonify({
                'id': shelf.id,
                'name': shelf.name,
                'description': shelf.description,
                'is_public': shelf.is_public,
                'created_at': shelf.created_at.isoformat(),
                'updated_at': shelf.updated_at.isoformat() # Should be updated by timestamp behavior
            }), 200
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to update bookshelf {shelf_id} for user {user_id}: {e}")
            return jsonify({"error": "Failed to update bookshelf"}), 500

    elif request.method == 'DELETE':
        """Deletes a specific bookshelf owned by the user."""
        try:
            db.session.delete(shelf) # Cascade should handle deleting associated books
            db.session.commit()
            logger.info(f"Bookshelf {shelf_id} deleted by user {user_id}")
            return jsonify({"message": "Bookshelf deleted successfully"}), 200 # Can also use 204 No Content
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to delete bookshelf {shelf_id} for user {user_id}: {e}")
            return jsonify({"error": "Failed to delete bookshelf"}), 500

# POST (add book) to a specific bookshelf
@app.route('/api/bookshelves/<int:shelf_id>/books', methods=['POST'])
@token_required # Requires login
def add_book_to_shelf(shelf_id):
    user_id = g.user_id
    # Ensure the user owns the target bookshelf
    shelf = Bookshelf.query.filter_by(id=shelf_id, user_id=user_id).first()
    if not shelf:
        logger.warning(f"Attempt to add book to non-existent or unauthorized bookshelf {shelf_id} by user {user_id}")
        return jsonify({"error": "Bookshelf not found or access denied"}), 404

    data = request.get_json()
    if not data or not data.get('title'):
        return jsonify({"error": "Book title is required"}), 400

    title = data['title'].strip()
    author = data.get('author', '').strip()
    isbn = data.get('isbn', '').strip()
    cover_image_url = data.get('cover_image_url', '').strip()
    
    if not title:
        return jsonify({"error": "Book title cannot be empty"}), 400

    # Optional: Check if book already exists in this shelf (e.g., by ISBN or title/author)
    # if existing_book:
    #     return jsonify({"error": "Book already exists in this shelf"}), 409

    new_book = Book(
        title=title,
        authors=author,
        isbn=isbn,
        cover_image_url=cover_image_url,
    )
    
    try:
        db.session.add(new_book)
        shelf.books.append(new_book)
        db.session.commit()
        logger.info(f"Book '{title}' added to bookshelf {shelf_id} by user {user_id}")
        # Return the created book data
        return jsonify({
             'id': new_book.id,
             'title': new_book.title,
             'author': new_book.authors,
             'isbn': new_book.isbn,
             'cover_image_url': new_book.cover_image_url,
             'added_at': new_book.added_at.isoformat()
        }), 201 # Created
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to add book '{title}' to bookshelf {shelf_id} for user {user_id}: {e}")
        return jsonify({"error": "Failed to add book"}), 500

# DELETE a specific book from a bookshelf
# Note: This route operates on the book ID directly, but still checks ownership via the shelf
@app.route('/api/books/<int:book_id>', methods=['DELETE'])
@token_required # Requires login
def delete_book_from_shelf(book_id):
    user_id = g.user_id
    # Find the book and ensure its shelf belongs to the logged-in user
    book = db.session.query(Book).join(Bookshelf).filter(
        Book.id == book_id, 
        Bookshelf.user_id == user_id
    ).first()

    if not book:
        logger.warning(f"Attempt to delete non-existent or unauthorized book {book_id} by user {user_id}")
        return jsonify({"error": "Book not found or access denied"}), 404

    try:
        db.session.delete(book)
        db.session.commit()
        logger.info(f"Book {book_id} (title: {book.title}) deleted by user {user_id}")
        return jsonify({"message": "Book deleted successfully"}), 200 # Can use 204
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to delete book {book_id} for user {user_id}: {e}")
        return jsonify({"error": "Failed to delete book"}), 500

# --- Public Bookshelf Endpoints ---

@app.route('/api/public/bookshelves', methods=['GET'])
def list_public_bookshelves():
    """Return all bookshelves marked as public."""
    shelves = Bookshelf.query.filter_by(is_public=True).order_by(Bookshelf.created_at.desc()).all()
    results = []
    for shelf in shelves:
        results.append({
            'id': shelf.id,
            'name': shelf.name,
            'description': shelf.description,
            'owner': {'id': shelf.owner.id, 'username': shelf.owner.username},
            'book_count': len(shelf.books),
            'created_at': shelf.created_at.isoformat() if shelf.created_at else None
        })
    return jsonify(results), 200


@app.route('/api/public/bookshelves/<int:shelf_id>', methods=['GET'])
def get_public_bookshelf(shelf_id):
    """Retrieve a single public bookshelf and its books."""
    shelf = Bookshelf.query.filter_by(id=shelf_id, is_public=True).first()
    if not shelf:
        return jsonify({'error': 'Bookshelf not found'}), 404

    books_data = []
    for book in shelf.books:
        books_data.append({
            'id': book.id,
            'title': book.title,
            'author': book.authors,
            'isbn': book.isbn,
            'cover_image_url': book.cover_image_url,
            'added_at': book.added_at.isoformat() if book.added_at else None
        })

    return jsonify({
        'id': shelf.id,
        'name': shelf.name,
        'description': shelf.description,
        'owner': {'id': shelf.owner.id, 'username': shelf.owner.username},
        'created_at': shelf.created_at.isoformat() if shelf.created_at else None,
        'books': books_data
    }), 200

# --- Social / Friends Endpoints ---

@app.route('/api/friends', methods=['GET'])
@token_required
def list_friends():
    """Return a list of friends for the logged-in user."""
    user_id = g.user_id
    friendships = FriendRequest.query.filter(
        FriendRequest.status == 'accepted',
        ((FriendRequest.requester_id == user_id) | (FriendRequest.addressee_id == user_id))
    ).all()
    results = []
    for fr in friendships:
        friend_id = fr.addressee_id if fr.requester_id == user_id else fr.requester_id
        user = User.query.get(friend_id)
        if user:
            results.append({'id': user.id, 'username': user.username})
    return jsonify(results), 200


@app.route('/api/friends/requests', methods=['GET'])
@token_required
def list_friend_requests():
    """List pending friend requests for the logged-in user."""
    user_id = g.user_id
    requests_q = FriendRequest.query.filter_by(addressee_id=user_id, status='pending').all()
    results = []
    for fr in requests_q:
        requester = User.query.get(fr.requester_id)
        if requester:
            results.append({'id': fr.id, 'from_user': {'id': requester.id, 'username': requester.username}})
    return jsonify(results), 200


@app.route('/api/friends/<int:target_id>', methods=['POST'])
@token_required
def add_or_accept_friend(target_id):
    """Send or accept a friend request."""
    user_id = g.user_id
    if user_id == target_id:
        return jsonify({'error': 'Cannot befriend yourself'}), 400

    target = User.query.get(target_id)
    if not target:
        return jsonify({'error': 'User not found'}), 404

    existing = FriendRequest.query.filter(
        ((FriendRequest.requester_id == user_id) & (FriendRequest.addressee_id == target_id)) |
        ((FriendRequest.requester_id == target_id) & (FriendRequest.addressee_id == user_id))
    ).first()

    if existing:
        if existing.status == 'accepted':
            return jsonify({'message': 'Already friends'}), 200
        if existing.addressee_id == user_id and existing.status == 'pending':
            existing.status = 'accepted'
            db.session.commit()
            return jsonify({'message': 'Friend request accepted'}), 200
        return jsonify({'error': 'Friend request already sent'}), 409

    fr = FriendRequest(requester_id=user_id, addressee_id=target_id)
    db.session.add(fr)
    db.session.commit()
    return jsonify({'message': 'Friend request sent'}), 201


@app.route('/api/friends/outgoing', methods=['GET'])
@token_required
def list_outgoing_requests():
    """List friend requests the user has sent that are pending."""
    user_id = g.user_id
    pending = FriendRequest.query.filter_by(requester_id=user_id, status='pending').all()
    results = []
    for fr in pending:
        user = User.query.get(fr.addressee_id)
        if user:
            results.append({'id': fr.id, 'to_user': {'id': user.id, 'username': user.username}})
    return jsonify(results), 200


@app.route('/api/friends/<int:target_id>', methods=['DELETE'])
@token_required
def remove_or_cancel_friend(target_id):
    """Remove a friend or cancel/decline a request."""
    user_id = g.user_id
    fr = FriendRequest.query.filter(
        ((FriendRequest.requester_id == user_id) & (FriendRequest.addressee_id == target_id)) |
        ((FriendRequest.requester_id == target_id) & (FriendRequest.addressee_id == user_id))
    ).first()
    if not fr:
        return jsonify({'error': 'No friend relationship or request found'}), 404

    if fr.status == 'pending':
        # If the logged-in user sent the request, cancel it. Otherwise decline it.
        if fr.requester_id == user_id:
            db.session.delete(fr)
            db.session.commit()
            return jsonify({'message': 'Friend request canceled'}), 200
        elif fr.addressee_id == user_id:
            fr.status = 'declined'
            db.session.commit()
            return jsonify({'message': 'Friend request declined'}), 200

    db.session.delete(fr)
    db.session.commit()
    return jsonify({'message': 'Friend removed'}), 200


# --- Community Endpoints ---

@app.route('/api/communities', methods=['GET'])
def list_communities():
    """Return all communities."""
    communities = Community.query.order_by(Community.name).all()
    results = []
    for c in communities:
        results.append({
            'id': c.id,
            'name': c.name,
            'description': c.description,
            'member_count': len(c.members),
            'owner_id': c.owner_id,
        })
    return jsonify(results), 200


@app.route('/api/communities', methods=['POST'])
@token_required
def create_community():
    """Create a new community and join it."""
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({'error': 'Community name is required'}), 400

    name = sanitize_input(data['name'].strip())
    description = sanitize_input(data.get('description', '').strip())
    if Community.query.filter_by(name=name).first():
        return jsonify({'error': 'Community already exists'}), 409

    community = Community(name=name, description=description, owner_id=g.user_id)
    user = User.query.get(g.user_id)
    community.members.append(user)
    db.session.add(community)
    db.session.commit()
    return jsonify({'id': community.id, 'name': community.name, 'description': community.description}), 201


@app.route('/api/communities/<int:comm_id>/join', methods=['POST'])
@token_required
def join_community(comm_id):
    """Join an existing community."""
    community = Community.query.get(comm_id)
    if not community:
        return jsonify({'error': 'Community not found'}), 404
    user = User.query.get(g.user_id)
    if user in community.members:
        return jsonify({'message': 'Already a member'}), 200
    community.members.append(user)
    db.session.commit()
    return jsonify({'message': 'Joined community'}), 200


@app.route('/api/communities/<int:comm_id>/leave', methods=['DELETE'])
@token_required
def leave_community(comm_id):
    """Leave a community you belong to."""
    community = Community.query.get(comm_id)
    if not community:
        return jsonify({'error': 'Community not found'}), 404
    user = User.query.get(g.user_id)
    if user not in community.members:
        return jsonify({'error': 'Not a member'}), 404
    community.members.remove(user)
    db.session.commit()
    return jsonify({'message': 'Left community'}), 200


@app.route('/api/communities/<int:comm_id>/members', methods=['GET'])
def list_community_members(comm_id):
    """List members of a community."""
    community = Community.query.get(comm_id)
    if not community:
        return jsonify({'error': 'Community not found'}), 404
    members = [{'id': u.id, 'username': u.username} for u in community.members]
    return jsonify(members), 200


@app.route('/api/communities/mine', methods=['GET'])
@token_required
def list_my_communities():
    """List communities the logged-in user belongs to."""
    user = User.query.get(g.user_id)
    results = [
        {
            'id': c.id,
            'name': c.name,
            'description': c.description,
            'member_count': len(c.members),
            'owner_id': c.owner_id,
        }
        for c in user.communities
    ]
    return jsonify(results), 200


@app.route('/api/communities/<int:comm_id>', methods=['GET', 'PUT'])
@token_required
def get_or_update_community(comm_id):
    """Retrieve or update a community."""
    community = Community.query.get(comm_id)
    if not community:
        return jsonify({'error': 'Community not found'}), 404

    if request.method == 'GET':
        return jsonify({
            'id': community.id,
            'name': community.name,
            'description': community.description,
            'member_count': len(community.members),
            'owner_id': community.owner_id,
        }), 200

    # PUT - only owner may update
    if community.owner_id != g.user_id:
        return jsonify({'error': 'Only the owner can update this community'}), 403
    data = request.get_json() or {}
    new_name = sanitize_input(data.get('name', community.name).strip())
    new_desc = sanitize_input(data.get('description', community.description or '').strip())
    if new_name:
        existing = Community.query.filter(Community.name == new_name, Community.id != comm_id).first()
        if existing:
            return jsonify({'error': 'Community with that name already exists'}), 409
        community.name = new_name
    community.description = new_desc
    db.session.commit()
    return jsonify({'id': community.id, 'name': community.name, 'description': community.description}), 200


@app.route('/api/communities/<int:comm_id>', methods=['DELETE'])
@token_required
def delete_community(comm_id):
    """Delete a community if the logged-in user is the owner."""
    community = Community.query.get(comm_id)
    if not community:
        return jsonify({'error': 'Community not found'}), 404
    if community.owner_id != g.user_id:
        return jsonify({'error': 'Only the owner can delete this community'}), 403
    db.session.delete(community)
    db.session.commit()
    return jsonify({'message': 'Community deleted'}), 200


@app.route('/api/users/<int:target_id>/bookshelves', methods=['GET'])
@token_required
def list_user_bookshelves(target_id):
    """List another user's bookshelves.

    Friends can view all of each other's shelves. Non-friends only see
    shelves marked as public.
    """
    viewer_id = g.user_id
    if viewer_id == target_id:
        shelves = Bookshelf.query.filter_by(user_id=target_id).order_by(Bookshelf.created_at.desc()).all()
    else:
        friendship = FriendRequest.query.filter(
            FriendRequest.status == 'accepted',
            ((FriendRequest.requester_id == viewer_id) & (FriendRequest.addressee_id == target_id)) |
            ((FriendRequest.requester_id == target_id) & (FriendRequest.addressee_id == viewer_id))
        ).first()
        if friendship:
            shelves = Bookshelf.query.filter_by(user_id=target_id).order_by(Bookshelf.created_at.desc()).all()
        else:
            shelves = Bookshelf.query.filter_by(user_id=target_id, is_public=True).order_by(Bookshelf.created_at.desc()).all()

    results = []
    for shelf in shelves:
        results.append({
            'id': shelf.id,
            'name': shelf.name,
            'description': shelf.description,
            'is_public': shelf.is_public,
            'book_count': len(shelf.books),
            'created_at': shelf.created_at.isoformat() if shelf.created_at else None,
        })
    return jsonify(results), 200

# === Core Logic Functions ===

def detect_books_with_llm(image_path):
    """
    Uses the configured Google Gemini Vision model to detect book titles from an image.

    Args:
        image_path (str): The file path to the temporarily saved image.

    Returns:
        list[str]: A list of detected book titles. Returns a list containing 
                   error messages if detection fails or the LLM is unavailable.
    """
    if not llm_model:
        logger.error("LLM model not initialized during detection call.")
        return ["Error: LLM service not available"]

    try:
        logger.info(f"Processing image with LLM: {image_path}")
        # Verify file exists before opening
        if not os.path.exists(image_path):
            logger.error(f"Error: Image file not found at {image_path}")
            return ["Error: Temporary image file not found for analysis."]

        img = Image.open(image_path) # Open image using Pillow

        # Define the prompt for the LLM
        prompt = (
            "Your task is to identify book titles from the provided image of a bookshelf. "
            "Focus ONLY on the text that represents book titles on the spines or covers. "
            "List each distinct book title you can clearly identify on a new line. "
            "Do NOT include author names unless they are undeniably part of the main title. "
            "Do NOT include publisher logos or series names unless part of the title. "
            "Provide ONLY the list of titles, with no introduction, explanation, numbering, or formatting like bullet points."
        )

        # Call the Gemini API (using the initialized llm_model)
        # Include safety settings to understand potential blocks
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ]
        response = llm_model.generate_content(
            [prompt, img],
            safety_settings=safety_settings,
            # stream=False # Ensure non-streaming response for .text access
        )

        # Debugging: Log the raw response for inspection
        logger.debug("--- LLM Raw Response Start ---")
        extracted_text = "" # Initialize default value
        try:
            # Check for safety blocks before accessing text
            # Accessing prompt_feedback raises AttributeError if no safety settings block it
            if hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason:
                logger.warning(f"LLM Prompt Blocked: {response.prompt_feedback.block_reason}")
                logger.debug(f"Safety Ratings: {response.prompt_feedback.safety_ratings}")
                return [f"LLM analysis failed: Blocked by safety filter ({response.prompt_feedback.block_reason})"]

            # Check if response candidate finished properly
            if not response.candidates or response.candidates[0].finish_reason != 1: # 1 = STOP
                 logger.warning(f"LLM Warning: Response did not finish normally. Reason: {response.candidates[0].finish_reason if response.candidates else 'Unknown'}")
                 # Potentially still try to access text, but be aware it might be incomplete

            extracted_text = response.text
            logger.debug(extracted_text)
        except ValueError as ve:
            # This might indicate issues during text generation itself
            logger.error(f"ValueError accessing response text: {ve}")
            # Log feedback if available
            if hasattr(response, 'prompt_feedback'):
                 logger.debug(f"Prompt Feedback: {response.prompt_feedback}")
            return ["LLM analysis blocked (Safety/Invalid Response)"]
        except AttributeError as ae:
            # Fallback if response.text doesn't exist - check prompt_feedback first
            if hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason:
                 # If it was blocked, we already handled it above or should have
                 logger.warning(f"AttributeError accessing text, but prompt feedback indicates block: {response.prompt_feedback.block_reason}")
                 # Return the block reason if available
                 return [f"LLM analysis failed: Blocked by safety filter ({response.prompt_feedback.block_reason})"]

            logger.error(f"AttributeError accessing response text: {ae}. Checking parts...")
            if hasattr(response, 'parts') and response.parts:
                try:
                    extracted_text = '\n'.join(part.text for part in response.parts if hasattr(part, 'text'))
                    logger.debug(f"Extracted from parts: {extracted_text}")
                except Exception as part_err:
                    logger.error(f"Error extracting text from parts: {part_err}")
                    return ["LLM analysis failed: Error parsing response parts."]
            else:
                logger.error("Could not extract text. No .text or valid .parts found.")
                return ["LLM analysis failed: Unexpected response structure."]
        except Exception as e:
            logger.error(f"An unexpected error occurred accessing LLM response text: {e}")
            return ["LLM analysis failed: Error reading response."]
        finally:
             logger.debug("--- LLM Raw Response End ---")

        # Process the extracted text
        if extracted_text:
            titles = [line.strip() for line in extracted_text.split('\n') if line.strip()]
            titles = [title for title in titles if 3 < len(title) < 150]
            logger.debug(f"Processed titles: {titles}")
            return titles if titles else ["No valid book titles identified by LLM."]
        else:
            logger.warning("LLM response processing yielded no text. Check raw response above.")
            return ["LLM analysis returned no parseable text."]

    # Specific exception handling for Google AI library
    except genai.types.BlockedPromptException as bpe:
        logger.error(f"LLM Error: Prompt was blocked by API - {bpe}")
        return ["LLM analysis failed: Prompt blocked by safety filters."]
    except genai.types.StopCandidateException as sce:
        logger.error(f"LLM Error: Generation stopped unexpectedly - {sce}")
        return ["LLM analysis failed: Generation stopped prematurely."]
    except Exception as e:
        # Catch other potential errors (e.g., network issues, image opening errors)
        logger.error(f"Generic error during LLM book detection: {str(e)}")
        return [f"Error during LLM analysis: {str(e)}"]

def get_recommendations(detected_books):
    """
    Get book recommendations based on detected books from LLM.
    Enhances recommendations by searching based on categories of initial results.
    """
    recommendations = []
    unique_titles_found = set() # Avoid duplicate recommendations

    # Sample recommendations for fallback cases
    sample_recs = [
        {
            'title': 'Sample Rec: The Hitchhiker\'s Guide',
            'authors': ['Douglas Adams'], 'description': 'A hilarious sci-fi adventure...','image': '',
            'publisher': 'Pan Books', 'publishedDate': '1979', 'pageCount': 180, 'categories': ['Fiction'], 'language': 'en', 'previewLink': ''
        },
        {
            'title': 'Sample Rec: Sapiens',
            'authors': ['Yuval Noah Harari'], 'description': 'A brief history of humankind...','image': '',
            'publisher': 'Harvill Secker', 'publishedDate': '2011', 'pageCount': 464, 'categories': ['History'], 'language': 'en', 'previewLink': ''
        }
    ]

    # Filter out error messages or non-book strings from detection results
    valid_books = [book for book in detected_books 
                   if book and 
                   not book.lower().startswith("error") and 
                   not book.lower().startswith("llm analysis") and 
                   not book.lower().startswith("no valid book titles")]
    
    if not valid_books:
        logger.info("No valid books detected to search for recommendations. Returning samples.")
        return sample_recs

    # --- Initial Search based on Titles --- 
    max_search_terms = 5 # Use up to 5 detected books
    search_terms = valid_books[:max_search_terms]
    logger.info(f"Phase 2.1: Getting recommendations based on detected books: {search_terms}")

    initial_categories = set() # Collect categories from initial results

    try:
        for search_term in search_terms:
            if len(recommendations) >= 6: 
                break
            
            logger.debug(f"Querying Google Books for title: {search_term}")
            quoted_search_term = requests.utils.quote(search_term)
            # More results per query initially to gather categories
            response = requests.get(
                f"https://www.googleapis.com/books/v1/volumes?q={quoted_search_term}&maxResults=8&orderBy=relevance&printType=books" 
            )
            response.raise_for_status() 
            
            books_data = response.json()
            
            if 'items' in books_data:
                for item in books_data['items']:
                    if len(recommendations) >= 6:
                        break 
                        
                    volume_info = item.get('volumeInfo', {})
                    title = volume_info.get('title', 'Unknown Title')
                    authors = volume_info.get('authors', ['Unknown Author'])
                    categories = volume_info.get('categories', [])
                    
                    normalized_title = title.lower()
                    normalized_search_term = search_term.lower()
                    is_self_recommendation = normalized_search_term == normalized_title
                    
                    if title != 'Unknown Title' and normalized_title not in unique_titles_found and not is_self_recommendation:
                        unique_titles_found.add(normalized_title)
                        
                        # Add book to recommendations
                        book = {
                            'title': title,
                            'authors': authors,
                            'description': volume_info.get('description', 'No description available.')[:250] + '...' if volume_info.get('description') else 'No description available.',
                            'image': volume_info.get('imageLinks', {}).get('thumbnail', ''),
                            'publisher': volume_info.get('publisher', ''),
                            'publishedDate': volume_info.get('publishedDate', ''),
                            'pageCount': volume_info.get('pageCount', 0),
                            'categories': categories,
                            'language': volume_info.get('language', ''),
                            'previewLink': volume_info.get('previewLink', '')
                        }
                        recommendations.append(book)
                        logger.debug(f"Added recommendation (from title search): {title}")
                        
                        # Collect categories for phase 2 search
                        if categories:
                            initial_categories.update(cat.lower() for cat in categories)
                            
                    # (Keep logging for skipped books)
                    # ... existing logging logic ...
                         
    except requests.exceptions.RequestException as e:
        logger.error(f"Error querying Google Books API (Initial Search): {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error processing initial recommendations: {str(e)}")

    # --- Phase 2.2: Category-Based Search --- 
    logger.debug(f"Phase 2.2: Found initial categories: {initial_categories}")
    if len(recommendations) < 6 and initial_categories:
        # Limit the number of category searches to avoid too many API calls
        category_search_limit = 3
        categories_to_search = list(initial_categories)[:category_search_limit]
        logger.debug(f"Searching based on categories: {categories_to_search}")

        try:
            for category in categories_to_search:
                if len(recommendations) >= 6:
                    break
                
                # Construct category search query (e.g., subject:Fiction)
                # Note: Google Books API uses 'subject:' for category searches
                category_query = f"subject:{category}"
                logger.debug(f"Querying Google Books for category: {category_query}")
                quoted_category_query = requests.utils.quote(category_query)
                
                # Fetch a few books for this category
                response = requests.get(
                   f"https://www.googleapis.com/books/v1/volumes?q={quoted_category_query}&maxResults=5&orderBy=relevance&printType=books"
                )
                response.raise_for_status()
                
                books_data = response.json()

                if 'items' in books_data:
                    for item in books_data['items']:
                        if len(recommendations) >= 6:
                            break
                            
                        volume_info = item.get('volumeInfo', {})
                        title = volume_info.get('title', 'Unknown Title')
                        authors = volume_info.get('authors', ['Unknown Author'])
                        
                        normalized_title = title.lower()
                        
                        # Check if valid title and not already recommended (less strict on self-rec here)
                        if title != 'Unknown Title' and normalized_title not in unique_titles_found:
                            unique_titles_found.add(normalized_title)
                            
                            book = {
                                'title': title,
                                'authors': authors,
                                'description': volume_info.get('description', 'No description available.')[:250] + '...' if volume_info.get('description') else 'No description available.',
                                'image': volume_info.get('imageLinks', {}).get('thumbnail', ''),
                                'publisher': volume_info.get('publisher', ''),
                                'publishedDate': volume_info.get('publishedDate', ''),
                                'pageCount': volume_info.get('pageCount', 0),
                                'categories': volume_info.get('categories', []),
                                'language': volume_info.get('language', ''),
                                'previewLink': volume_info.get('previewLink', '')
                            }
                            recommendations.append(book)
                            logger.debug(f"Added recommendation (from category search '{category}'): {title}")
                        # (Optional: Log skipped category results)

        except requests.exceptions.RequestException as e:
            logger.error(f"Error querying Google Books API (Category Search): {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error processing category recommendations: {str(e)}")

    # --- Phase 2.3: Open Library Search (Experimental) ---
    # Try Open Library if we still need more recommendations
    if len(recommendations) < 6:
        logger.debug("Phase 2.3: Trying Open Library search as fallback/supplement.")
        try:
            # Use the same initial search terms 
            for search_term in search_terms: 
                if len(recommendations) >= 6:
                    break

                logger.debug(f"Querying Open Library for: {search_term}")
                # Open Library Search API endpoint
                ol_search_url = f"https://openlibrary.org/search.json?q={requests.utils.quote(search_term)}&limit=3" 
                response_ol = requests.get(ol_search_url, timeout=10) # Add timeout
                response_ol.raise_for_status()
                ol_data = response_ol.json()

                if 'docs' in ol_data:
                    for doc in ol_data['docs']: 
                        if len(recommendations) >= 6:
                            break

                        title = doc.get('title', 'Unknown Title')
                        authors = doc.get('author_name', ['Unknown Author'])
                        normalized_title = title.lower()
                        
                        # Check if valid title and not already found
                        if title != 'Unknown Title' and normalized_title not in unique_titles_found:
                            unique_titles_found.add(normalized_title)

                            # Extract additional details (may require more API calls or parsing)
                            # Cover images often use OLID/ISBN: https://openlibrary.org/dev/docs/api/covers
                            cover_id = doc.get('cover_i', None)
                            image_url = f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else ''
                            
                            # Get description (might require separate Works API call using doc['key'])
                            description = doc.get('first_sentence_value', 'No description available.')[:250] + '...' if doc.get('first_sentence_value') else 'No description available.'

                            book = {
                                'title': title,
                                'authors': authors,
                                'description': description,
                                'image': image_url,
                                'publisher': ", ".join(doc.get('publisher', [])[:2]), # Limit publishers shown
                                'publishedDate': str(doc.get('first_publish_year', '')),
                                'pageCount': doc.get('number_of_pages_median', 0),
                                'categories': doc.get('subject', [])[:5], # Limit subjects shown
                                'language': ", ".join(doc.get('language', [])[:2]),
                                'previewLink': f"https://openlibrary.org{doc.get('key', '')}" if doc.get('key') else ''
                            }
                            recommendations.append(book)
                            logger.debug(f"Added recommendation (from Open Library search): {title}")
                        else:
                             if title == 'Unknown Title':
                                 logger.debug("Skipped OL item: Unknown Title")
                             elif normalized_title in unique_titles_found:
                                 logger.debug(f"Skipped OL item (duplicate rec): {title}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Error querying Open Library API: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error processing Open Library recommendations: {str(e)}")

    # --- Final Fallback & Return --- 
    if not recommendations:
        logger.info("Could not find any recommendations after all searches. Returning samples.")
        return sample_recs

    # Ensure the final list does not exceed the limit
    logger.info(f"Returning final {len(recommendations[:6])} recommendations.")
    return recommendations[:6]

if __name__ == '__main__':
    with app.app_context():
        # Create database tables if they don't exist
        # Note: For more complex migrations later, consider Flask-Migrate
        db.create_all()
        logger.info(f"Database {DB_NAME} initialized/checked.")
    
    logger.info("Starting Bookshelf Recommender Backend...")
    logger.info("----------------------------------------")
    # Check for API key presence on startup
    if not api_key:
        logger.warning("*** WARNING: GOOGLE_API_KEY not found in backend/.env ***")
        logger.warning("*** Image analysis will fail. Please create .env file. ***")
    else:
        logger.info("GOOGLE_API_KEY found.")
        if not llm_model:
            logger.warning("*** WARNING: Failed to initialize Gemini Model. Check API Key and backend logs. ***")
        else:
            logger.info("Gemini Model (gemini-1.5-flash) ready.")
    logger.info("----------------------------------------")
    logger.info("Requirements reminder:")
    logger.info("- Ensure GOOGLE_API_KEY is set in backend/.env")
    logger.info("- Run: pip install -r backend/requirements.txt")
    logger.info("----------------------------------------")
    app.run(debug=True, port=5001)
