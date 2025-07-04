import React, { useState, useEffect } from 'react';
import LoginForm from './components/LoginForm';
import RegisterForm from './components/RegisterForm';
import BookshelfList from './components/BookshelfList'; // Import BookshelfList
import BookshelfDetail from './components/BookshelfDetail'; // Import BookshelfDetail
import { fetchWithAuth, getToken } from './utils/api'; // Import helpers from utils
import './App.css';

// Helper functions getToken and fetchWithAuth are now in utils/api.js

function App() {
  // Image Upload & Results State
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null); // Will now contain { detected_books, recommendations, save_message }
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('detected');

  // Authentication State
  const [currentUser, setCurrentUser] = useState(null); 
  const [authView, setAuthView] = useState('main'); // 'main', 'login', 'register'
  const [authLoading, setAuthLoading] = useState(true); 

  // Main content view state (when logged in)
  const [mainView, setMainView] = useState('upload'); // 'upload', 'bookshelves'
  const [selectedBookshelfId, setSelectedBookshelfId] = useState(null); // To view a specific shelf later

  // --- Effect for initial authentication check --- 
  useEffect(() => {
    const checkAuth = async () => {
      const token = getToken();
      const savedUser = localStorage.getItem('currentUser');
      
      if (token && savedUser) {
        try {
          // Verify token with backend
          const response = await fetch('/api/verify_token', {
            method: 'GET',
            headers: {
              'Authorization': `Bearer ${token}`
            }
          });
          
          if (response.ok) {
            // Token is valid
            const userData = await response.json();
            console.log('Token verified, user authenticated:', userData);
            setCurrentUser(JSON.parse(savedUser));
          } else {
            // Token is invalid or expired
            console.log('Invalid or expired token, logging out');
            localStorage.removeItem('authToken');
            localStorage.removeItem('currentUser');
            setCurrentUser(null);
            setAuthView('login');
          }
        } catch (error) {
          console.error('Auth verification error:', error);
          localStorage.removeItem('authToken');
          localStorage.removeItem('currentUser');
          setCurrentUser(null);
          setAuthView('login');
        }
      }
    };
    
    checkAuth();
  }, []);

  // --- Authentication Handlers ---
  const handleLoginSuccess = (userData) => {
    setCurrentUser(userData);
    setAuthView('main'); 
    setMainView('upload'); // Go to upload view after login
    // Token is already stored by LoginForm
  };

  // Add a new handler for registration success
  const handleRegisterSuccess = (userData) => {
    setCurrentUser(userData);
    setAuthView('main');
    setMainView('upload');
    console.log('Auto-login successful after registration');
  };

  const handleLogout = () => {
    // Clear authentication data from localStorage
    localStorage.removeItem('authToken');
    localStorage.removeItem('currentUser');
    
    // Reset application state
    setCurrentUser(null);
    setAuthView('main'); 
    setMainView('upload');
    console.log('Successfully logged out');
  };
  
  const switchToLogin = () => setAuthView('login');
  const switchToRegister = () => setAuthView('register');
  // No longer need switchToMain, as authView='main' is the logged-in/logged-out state
  // We use mainView to control content *within* the logged-in state

  // --- View Switching Handlers (for logged-in user) ---
  const switchToUploadView = () => {
      setMainView('upload');
      setSelectedBookshelfId(null); // Reset selected shelf
  };

  const switchToBookshelvesView = () => {
      setMainView('bookshelves');
      setSelectedBookshelfId(null); // Reset selected shelf
  };

  const handleSelectBookshelf = (shelfId) => {
      console.log("Selected bookshelf:", shelfId);
      setSelectedBookshelfId(shelfId);
      setMainView('shelfDetail'); // Switch to shelf detail view
  };


  // --- Image Upload Handler (uses fetchWithAuth via FormData special handling) ---
  const handleUpload = async () => {
    if (!selectedFile) {
      alert("Please select an image first!");
      return;
    }
    setLoading(true);
    setError(null);
    setResults(null); // Clear previous results
    const formData = new FormData();
    formData.append('bookshelfImage', selectedFile);
    
    try {
        const token = getToken();
        const response = await fetch('/api/upload', { 
            method: 'POST',
            headers: { ...(token && { 'Authorization': `Bearer ${token}` }) },
            body: formData, 
        });
        
        if (!response.ok) {
            let errorData = { error: `Upload failed with status ${response.status}` };
             try {
                 errorData = await response.json();
             } catch (parseError) { console.warn("Could not parse error response from upload as JSON."); }
            throw new Error(errorData.error || `Upload failed: ${response.statusText}`);
        }
        const data = await response.json(); // Contains detected_books, recommendations, save_message
        console.log('Upload successful:', data);
        setResults(data); // Set the entire results object
        // Decide if we want to switch tabs/views automatically, for now, stay on upload view
        // setActiveTab('recommendations'); 
    } catch (err) {
      console.error('Upload failed:', err);
      setError(err.message || 'Upload failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file && file.type.startsWith('image/')) {
      setSelectedFile(file);
      const reader = new FileReader();
      reader.onloadend = () => setPreviewUrl(reader.result);
      reader.readAsDataURL(file);
      setResults(null);
      setError(null);
    } else {
      setSelectedFile(null);
      setPreviewUrl(null);
      console.error("Please select an image file.");
    }
  };

  const handleCameraCapture = () => {
    const fileInput = document.getElementById('camera-input');
    if (fileInput) fileInput.click();
  };

  // --- Rendering Logic --- 

  // Show loading screen during initial auth check
  if (authLoading) {
      return <div className="loading-fullscreen">Initializing...</div>;
  }

  // Determine what main content to show based on login status and mainView
  const renderAppContent = () => {
      if (!currentUser) {
          // User is not logged in - show Login or Register form
          if (authView === 'login') {
              return (
                  <div className="auth-container">
                      <LoginForm onLoginSuccess={handleLoginSuccess} switchToRegister={switchToRegister} />
                  </div>
              );
          }
          if (authView === 'register') {
              return (
                  <div className="auth-container">
                      <RegisterForm onRegisterSuccess={handleRegisterSuccess} switchToLogin={switchToLogin} /> 
                  </div>
              );
          }
          // Default view for logged-out users (could be a landing page or just the login form)
          return (
              <div className="auth-container">
                  <LoginForm onLoginSuccess={handleLoginSuccess} switchToRegister={switchToRegister} />
              </div>
          );
      } else {
          // User IS logged in - show content based on mainView
          switch (mainView) {
              case 'upload':
                  return renderUploadSection(); // Extracted upload UI
              case 'bookshelves':
                  return <BookshelfList onSelectShelf={handleSelectBookshelf} />;
              case 'shelfDetail':
                  // Render BookshelfDetail if an ID is selected
                  if (selectedBookshelfId) {
                      return <BookshelfDetail shelfId={selectedBookshelfId} onBackToList={switchToBookshelvesView} />;
                  } else {
                      // Fallback if no ID somehow (e.g., direct navigation attempt?)
                      console.warn("Shelf detail view requested without a selected ID, returning to list.");
                      switchToBookshelvesView(); // Go back to list
                      return null; // Avoid rendering anything momentarily
                  }
              default:
                  return renderUploadSection(); // Fallback to upload
          }
      }
  };

  // Extracted Upload Section UI for clarity
  const renderUploadSection = () => (
    <>
      <div className="upload-section">
         {/* ... keep existing upload methods divs ... */} 
         <div className="upload-methods">
             <div className="upload-option">
                 <h3>Upload a Photo</h3>
                 <input 
                     id="file-input"
                     type="file" 
                     accept="image/*" 
                     onChange={handleFileChange} 
                     className="file-input"
                     aria-labelledby="upload-label"
                 />
                 <button 
                     id="upload-label"
                     className="upload-button" 
                     onClick={() => document.getElementById('file-input').click()}
                 >
                     Choose File
                 </button>
             </div>
             
             <div className="upload-option">
                 <h3>Use Camera</h3>
                 <input 
                     id="camera-input"
                     type="file" 
                     accept="image/*" 
                     capture="environment" // Prefer back camera
                     onChange={handleFileChange} 
                     className="file-input"
                     aria-labelledby="camera-label"
                 />
                 <button 
                     id="camera-label"
                     className="upload-button" 
                     onClick={handleCameraCapture}
                 >
                     Start Camera
                 </button>
             </div>
         </div>
 
         {previewUrl && (
           <div className="preview-section">
             <h4>Preview:</h4>
             <img src={previewUrl} alt="Bookshelf preview" className="image-preview" />
             <button 
               onClick={handleUpload} 
               disabled={loading || !selectedFile}
               className="analyze-button"
             >
               {loading ? <><span className="spinner-border-sm" role="status" aria-hidden="true"></span> Analyzing...</> : 'Analyze Bookshelf'}
             </button>
           </div>
         )}
 
         {error && <div className="error-message">Error: {error}</div>}
         
       </div>

       {/* --- Results Display Section (if results exist) --- */} 
       {results && (
            <div className="results-display-section">
                {/* Display save message from backend */} 
                {results.save_message && <p className="save-confirmation">{results.save_message}</p>}
                
                {/* Optionally use tabs, or just stack vertically */} 
                {/* <div className="tabs">...</div> */} 
                
                {/* Detected Books */} 
                <div className="detected-books-results">
                    <h2>Detected Books</h2>
                    {(results.detected_books && results.detected_books.length > 0) ? (
                        <ul className="detected-book-list">
                            {results.detected_books.map((bookTitle, index) => (
                                <li key={`book-${index}`}>
                                    {bookTitle}
                                </li>
                            ))}
                        </ul>
                    ) : (
                        <p>No books detected yet.</p>
                    )}
                </div>
                {/* TODO: Add rendering for recommendations if they exist */}
            </div>
       )}
    </>
  );

  return renderAppContent();
}

export default App;