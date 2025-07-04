import React, { useState, useEffect } from 'react';
import { fetchWithAuth } from '../utils/api'; // Assuming fetchWithAuth is moved to utils

function BookshelfList({ onSelectShelf }) { // Add prop to handle selecting a shelf
  const [bookshelves, setBookshelves] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // State for creating a new shelf
  const [newShelfName, setNewShelfName] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [createError, setCreateError] = useState(null);

  // State for delete operation
  const [deletingShelfId, setDeletingShelfId] = useState(null);
  const [deleteError, setDeleteError] = useState(null);

  useEffect(() => {
    const loadBookshelves = async () => {
      setIsLoading(true);
      setError(null);
      setDeleteError(null); // Clear delete error on load
      try {
        console.log("Fetching bookshelves...");
        const data = await fetchWithAuth('/api/bookshelves');
        console.log("Bookshelves received:", data);
        setBookshelves(data || []); // Handle potential null response
      } catch (err) {
        console.error("Failed to fetch bookshelves:", err);
        setError(err.message || "Failed to load bookshelves.");
      } finally {
        setIsLoading(false);
      }
    };

    loadBookshelves();
  }, []); // Fetch on component mount

  // Handle creating a new bookshelf
  const handleCreateShelf = async (event) => {
    event.preventDefault();
    if (!newShelfName.trim()) {
      setCreateError("Bookshelf name cannot be empty.");
      return;
    }

    setIsCreating(true);
    setCreateError(null);

    try {
      console.log(`Creating bookshelf: ${newShelfName}`);
      const newShelf = await fetchWithAuth('/api/bookshelves', {
        method: 'POST',
        body: { name: newShelfName.trim() } // Send name in the body
      });
      console.log("Bookshelf created:", newShelf);
      // Add the new shelf to the beginning of the list
      setBookshelves(prevShelves => [newShelf, ...prevShelves]); 
      setNewShelfName(''); // Clear the input field
    } catch (err) {
      console.error("Failed to create bookshelf:", err);
      setCreateError(err.message || "Failed to create bookshelf.");
    } finally {
      setIsCreating(false);
    }
  };

  // Handle deleting a bookshelf
  const handleDeleteShelf = async (shelfId, shelfName) => {
    // Confirm before deleting
    if (!window.confirm(`Are you sure you want to delete the bookshelf "${shelfName}"? This will also delete all books on it.`)) {
      return;
    }

    setDeletingShelfId(shelfId);
    setDeleteError(null);

    try {
      console.log(`Deleting bookshelf ID: ${shelfId}`);
      await fetchWithAuth(`/api/bookshelves/${shelfId}`, {
        method: 'DELETE'
      });
      console.log("Bookshelf deleted successfully from backend.");
      // Remove the shelf from the state
      setBookshelves(prevShelves => prevShelves.filter(shelf => shelf.id !== shelfId));
    } catch (err) {
      console.error("Failed to delete bookshelf:", err);
      setDeleteError(`Failed to delete bookshelf "${shelfName}": ${err.message}`);
    } finally {
      setDeletingShelfId(null); // Reset deleting state regardless of outcome
    }
  };

  if (isLoading) {
    return <div className="loading">Loading bookshelves...</div>;
  }

  if (error) {
    return <div className="error-message">Error loading shelves: {error}</div>;
  }

  return (
    <div className="bookshelf-list-container">
      <h2>My Bookshelves</h2>

      {/* Create New Shelf Form */} 
      <form onSubmit={handleCreateShelf} className="create-shelf-form">
         <input 
            type="text"
            value={newShelfName}
            onChange={(e) => setNewShelfName(e.target.value)}
            placeholder="New bookshelf name..."
            disabled={isCreating || deletingShelfId}
            className="shelf-name-input"
            aria-label="New bookshelf name"
         />
         <button type="submit" disabled={isCreating || deletingShelfId} className="button-primary">
            {isCreating ? (
                <><span className="spinner-border-sm" role="status" aria-hidden="true"></span>Creating...</>
            ) : ( 
                'Create Shelf'
            )}
         </button>
         {createError && <p className="error-message create-error">{createError}</p>}
      </form>

      {/* Display Shelf Deletion Error */} 
      {deleteError && <p className="error-message delete-error">{deleteError}</p>}

      {/* Bookshelf List */} 
      {bookshelves.length === 0 && !isLoading ? (
        <p className="no-shelves-message">You don't have any bookshelves yet. Create one above!</p>
      ) : (
        <ul className="bookshelf-list">
          {bookshelves.map((shelf) => (
            <li key={shelf.id} className={`bookshelf-item ${deletingShelfId === shelf.id ? 'deleting' : ''}`}>
              <div onClick={() => onSelectShelf(shelf.id)} className="bookshelf-item-content">
                  <h3>{shelf.name}</h3>
                  <p>{shelf.book_count || 0} book(s)</p>
                  {shelf.description && <p className="shelf-description">{shelf.description}</p>}
              </div>
              <div className="bookshelf-item-actions">
                  <button 
                     onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteShelf(shelf.id, shelf.name);
                     }}
                     className="button-danger button-small"
                     title="Delete Bookshelf"
                     disabled={deletingShelfId === shelf.id || isCreating}
                  >
                     {deletingShelfId === shelf.id ? (
                        <><span className="spinner-border-sm" role="status" aria-hidden="true"></span>Deleting...</>
                     ) : ( 
                        'Delete'
                     )}
                  </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default BookshelfList; 