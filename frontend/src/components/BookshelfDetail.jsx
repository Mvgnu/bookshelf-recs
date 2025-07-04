import React, { useState, useEffect } from 'react';
import { fetchWithAuth } from '../utils/api';

function BookshelfDetail({ shelfId, onBackToList }) {
  const [shelf, setShelf] = useState(null);
  const [books, setBooks] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // State for adding a book
  const [newBookTitle, setNewBookTitle] = useState('');
  const [newBookAuthor, setNewBookAuthor] = useState('');
  const [newBookIsbn, setNewBookIsbn] = useState('');
  const [isAddingBook, setIsAddingBook] = useState(false);
  const [addBookError, setAddBookError] = useState(null);

  // State for delete operation
  const [deletingBookId, setDeletingBookId] = useState(null);
  const [deleteBookError, setDeleteBookError] = useState(null);

  // State for deleting the entire shelf
  const [isDeletingShelf, setIsDeletingShelf] = useState(false);
  const [deleteShelfError, setDeleteShelfError] = useState(null);

  // State for editing the shelf
  const [isEditing, setIsEditing] = useState(false);
  const [editedName, setEditedName] = useState('');
  const [editedDescription, setEditedDescription] = useState('');
  const [isUpdatingShelf, setIsUpdatingShelf] = useState(false);
  const [updateShelfError, setUpdateShelfError] = useState(null);

  // Fetch shelf details when shelfId changes
  useEffect(() => {
    if (!shelfId) return; 
    loadShelfDetails();
  }, [shelfId]);

  const loadShelfDetails = async () => {
    setIsLoading(true);
    setError(null);
    setShelf(null); 
    setBooks([]);
    setDeleteBookError(null); 
    setDeleteShelfError(null);
    setUpdateShelfError(null); // Clear update error on load/reload
    setIsEditing(false); // Ensure edit mode is off on load

    try {
      console.log(`Fetching details for bookshelf ID: ${shelfId}`);
      const data = await fetchWithAuth(`/api/bookshelves/${shelfId}`);
      console.log("Shelf details received:", data);
      setShelf({ id: data.id, name: data.name, description: data.description });
      setBooks(data.books || []);
      // Set initial values for editing
      setEditedName(data.name || ''); 
      setEditedDescription(data.description || '');
    } catch (err) {
      console.error("Failed to fetch shelf details:", err);
      setError(err.message || "Failed to load shelf details.");
    } finally {
      setIsLoading(false);
    }
  };

  // Handle adding a new book
  const handleAddBook = async (event) => {
    event.preventDefault();
    if (!newBookTitle.trim()) {
      setAddBookError("Book title is required.");
      return;
    }

    setIsAddingBook(true);
    setAddBookError(null);

    const bookData = {
      title: newBookTitle.trim(),
      author: newBookAuthor.trim(),
      isbn: newBookIsbn.trim(),
      // cover_image_url: '' // Add later if needed
    };

    try {
      console.log(`Adding book to shelf ${shelfId}:`, bookData);
      const addedBook = await fetchWithAuth(`/api/bookshelves/${shelfId}/books`, {
        method: 'POST',
        body: bookData
      });
      console.log("Book added:", addedBook);
      // Add the new book to the state
      setBooks(prevBooks => [...prevBooks, addedBook]);
      // Clear the form
      setNewBookTitle('');
      setNewBookAuthor('');
      setNewBookIsbn('');
    } catch (err) {
      console.error("Failed to add book:", err);
      setAddBookError(err.message || "Failed to add book.");
    } finally {
      setIsAddingBook(false);
    }
  };

  // Handle deleting a book
  const handleDeleteBook = async (bookId) => {
    // Basic confirmation dialog
    if (!window.confirm("Are you sure you want to delete this book from the shelf?")) {
      return;
    }

    setDeletingBookId(bookId); // Indicate which book is being deleted (for UI feedback)
    setDeleteBookError(null);

    try {
      console.log(`Deleting book ID: ${bookId}`);
      // API uses DELETE /api/books/:book_id
      await fetchWithAuth(`/api/books/${bookId}`, {
        method: 'DELETE'
      });
      console.log("Book deleted successfully from backend.");
      // Remove the book from the state
      setBooks(prevBooks => prevBooks.filter(book => book.id !== bookId));
    } catch (err) {
      console.error("Failed to delete book:", err);
      setDeleteBookError(`Failed to delete book: ${err.message}`);
    } finally {
      setDeletingBookId(null); // Reset deleting state
    }
  };

  // Handle deleting the entire bookshelf
  const handleDeleteShelf = async () => {
    if (!shelf || !shelf.name) return; // Should not happen, but safeguard

    if (!window.confirm(`Are you sure you want to delete the bookshelf "${shelf.name}"? This action cannot be undone.`)) {
      return;
    }

    setIsDeletingShelf(true);
    setDeleteShelfError(null);

    try {
      console.log(`Deleting bookshelf ID: ${shelfId}`);
      await fetchWithAuth(`/api/bookshelves/${shelfId}`, {
        method: 'DELETE'
      });
      console.log("Bookshelf deleted successfully via detail view.");
      // Navigate back to the list view after successful deletion
      onBackToList(); 
    } catch (err) {
      console.error("Failed to delete bookshelf:", err);
      setDeleteShelfError(`Failed to delete bookshelf: ${err.message}`);
      // Keep the user on the detail page to see the error
      setIsDeletingShelf(false); // Re-enable button if deletion fails
    } 
    // No finally block resetting isDeletingShelf, as successful deletion navigates away
  };

  // --- Edit Shelf Handlers ---
  const handleEditToggle = () => {
      if (!isEditing) {
          // Entering edit mode: sync edit fields with current shelf state
          setEditedName(shelf?.name || '');
          setEditedDescription(shelf?.description || '');
          setUpdateShelfError(null); // Clear previous errors
      }
      setIsEditing(!isEditing);
  };

  const handleUpdateShelf = async (event) => {
    event.preventDefault();
    if (!editedName.trim()) {
      setUpdateShelfError("Bookshelf name cannot be empty.");
      return;
    }
    if (!shelf) return; // Should not happen

    setIsUpdatingShelf(true);
    setUpdateShelfError(null);

    const updateData = {
      name: editedName.trim(),
      description: editedDescription.trim(),
      // Add is_public later if needed
    };

    try {
      console.log(`Updating bookshelf ID ${shelfId}:`, updateData);
      const updatedShelf = await fetchWithAuth(`/api/bookshelves/${shelfId}`, {
        method: 'PUT',
        body: updateData
      });
      console.log("Shelf updated:", updatedShelf);
      // Update the main shelf state with the response
      setShelf(prev => ({ ...prev, ...updatedShelf })); 
      setIsEditing(false); // Exit edit mode on success
    } catch (err) {
      console.error("Failed to update bookshelf:", err);
      setUpdateShelfError(err.message || "Failed to update bookshelf.");
    } finally {
      setIsUpdatingShelf(false);
    }
  };

  // --- Render Logic ---
  if (!shelfId) {
      // Should not happen if App.jsx logic is correct, but good fallback
      return <p>No bookshelf selected.</p>; 
  }

  if (isLoading) {
    return <div className="loading">Loading bookshelf details...</div>;
  }

  if (error) {
    return (
      <div className="error-message">
        <p>Error: {error}</p>
        <button onClick={onBackToList} className="button-secondary">Back to List</button>
      </div>
    );
  }

  if (!shelf) {
    // If not loading and no error, but shelf is null (shouldn't normally happen)
    return (
      <div>
        <p>Bookshelf not found.</p>
        <button onClick={onBackToList} className="button-secondary">Back to List</button>
      </div>
    );
  }

  // Display shelf delete error prominently if it occurs
  if (deleteShelfError) {
      return (
          <div className="bookshelf-detail-container error-state">
              <button onClick={onBackToList} className="button-back">← Back to Shelves</button>
              <h2>Error Deleting Shelf</h2>
              <p className="error-message delete-shelf-error">{deleteShelfError}</p>
              {/* Optionally show shelf details again if needed */}
              {/* {shelf && <h2>{shelf.name}</h2>} ... */}
          </div>
      );
  }

  return (
    <div className={`bookshelf-detail-container ${isDeletingShelf ? 'deleting-shelf' : ''} ${isEditing ? 'editing-shelf' : ''}`}>
      <div className="detail-header">
        <button onClick={onBackToList} className="button-back" disabled={isDeletingShelf || isUpdatingShelf}>← Back to Shelves</button>
        {/* Edit Toggle Button */} 
        <button 
            onClick={handleEditToggle}
            className={`button-secondary button-small ${isEditing ? 'active' : ''}`}
            disabled={isDeletingShelf || isUpdatingShelf}
        >
            {isEditing ? 'Cancel Edit' : 'Edit Shelf'}
        </button>
      </div>
      
      {/* Shelf Title and Description (Conditionally Editable) */} 
      {isEditing ? (
          <form onSubmit={handleUpdateShelf} className="edit-shelf-form">
              <div className="form-group">
                 <label htmlFor="shelfNameEdit">Bookshelf Name *</label>
                  <input 
                      id="shelfNameEdit"
                      type="text"
                      value={editedName}
                      onChange={(e) => setEditedName(e.target.value)}
                      required
                      disabled={isUpdatingShelf}
                  />
              </div>
              <div className="form-group">
                  <label htmlFor="shelfDescEdit">Description</label>
                  <textarea 
                      id="shelfDescEdit"
                      value={editedDescription}
                      onChange={(e) => setEditedDescription(e.target.value)}
                      rows="3"
                      disabled={isUpdatingShelf}
                  />
              </div>
               {updateShelfError && <p className="error-message update-shelf-error">{updateShelfError}</p>}
              <div className="form-actions">
                  <button type="submit" className="button-primary" disabled={isUpdatingShelf}>
                       {isUpdatingShelf ? (
                           <><span className="spinner-border-sm" role="status" aria-hidden="true"></span>Saving...</>
                       ) : (
                           'Save Changes'
                       )}
                  </button>
                   <button type="button" className="button-secondary" onClick={handleEditToggle} disabled={isUpdatingShelf}>
                       Cancel
                   </button>
              </div>
          </form>
      ) : (
          <> {/* Display Mode */} 
              <h2>{shelf.name}</h2>
              {shelf.description && <p className="shelf-detail-description">{shelf.description}</p>}
          </>
      )}

      {/* Add Book Section (Disabled when editing shelf) */} 
      <div className={`add-book-section ${isEditing ? 'disabled-section' : ''}`}>
         <h4>Add New Book</h4>
         <form onSubmit={handleAddBook} className="add-book-form">
              {/* ... (form inputs and button) ... */}
             <div className="form-group">
                <label htmlFor="bookTitle">Title *</label>
                <input id="bookTitle" type="text" value={newBookTitle} onChange={(e) => setNewBookTitle(e.target.value)} placeholder="Book title" required disabled={isAddingBook || isDeletingShelf || isEditing}/>
             </div>
             <div className="form-group">
                 <label htmlFor="bookAuthor">Author</label>
                 <input id="bookAuthor" type="text" value={newBookAuthor} onChange={(e) => setNewBookAuthor(e.target.value)} placeholder="Author's name" disabled={isAddingBook || isDeletingShelf || isEditing} />
             </div>
             <div className="form-group">
                 <label htmlFor="bookIsbn">ISBN</label>
                 <input id="bookIsbn" type="text" value={newBookIsbn} onChange={(e) => setNewBookIsbn(e.target.value)} placeholder="ISBN (optional)" disabled={isAddingBook || isDeletingShelf || isEditing} />
             </div>
             <div className="form-actions">
                 <button type="submit" disabled={isAddingBook || isDeletingShelf || isEditing} className="button-primary">
                      {isAddingBook ? (
                          <><span className="spinner-border-sm" role="status" aria-hidden="true"></span>Adding...</>
                      ) : (
                          'Add Book'
                      )}
                 </button>
             </div>
             {addBookError && <p className="error-message add-book-error">{addBookError}</p>}
         </form>
      </div>

      <hr className="section-divider" />

      <h3>Books on this Shelf ({books.length})</h3>
      {deleteBookError && <p className="error-message delete-book-error">{deleteBookError}</p>}
      {books.length === 0 ? (
        <p>This bookshelf is empty. Add some books above!</p>
      ) : (
        <ul className="book-list-detail">
          {books.map((book) => (
            <li key={book.id} className={`book-item-detail ${deletingBookId === book.id ? 'deleting' : ''}`}>
              <div className="book-info">
                  <strong>{book.title}</strong>
                  {book.author && <span> by {book.author}</span>}
                  {book.isbn && <span className="book-isbn"> (ISBN: {book.isbn})</span>}
              </div>
              <button 
                 onClick={() => handleDeleteBook(book.id)}
                 className="button-danger button-small"
                 title="Delete Book"
                 disabled={deletingBookId === book.id || isDeletingShelf || isEditing} // Disable if deleting book, shelf, or editing shelf
              >
                 {deletingBookId === book.id ? (
                     <span className="spinner-border-sm" role="status" aria-hidden="true"></span>
                 ) : ( 
                     '×' /* Use multiplication sign for delete */
                 )}
              </button>
            </li>
          ))}
        </ul>
      )}
      
      {/* Delete Bookshelf Button Section (Hidden when editing) */} 
      {!isEditing && (
          <div className="delete-shelf-section">
              <hr className="section-divider" />
              <button 
                  onClick={handleDeleteShelf}
                  className="button-danger"
                  disabled={isDeletingShelf}
                  title="Delete this entire bookshelf and all its books"
              >
                   {isDeletingShelf ? (
                       <><span className="spinner-border-sm" role="status" aria-hidden="true"></span>Deleting Shelf...</>
                   ) : (
                       'Delete This Bookshelf'
                   )}
              </button>
          </div>
      )}
    </div>
  );
}

export default BookshelfDetail; 