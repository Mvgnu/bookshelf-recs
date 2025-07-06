// Utility functions for making API requests

// Helper function to get token from localStorage
export const getToken = () => localStorage.getItem('authToken');

/**
 * Makes an authenticated API request.
 * Automatically adds the Content-Type: application/json header 
 * and the Authorization: Bearer <token> header if a token exists.
 * Handles JSON parsing and basic error handling.
 * Throws an error if the request fails.
 * Note: Does NOT automatically stringify body if it's FormData.
 * @param {string} url - The API endpoint URL.
 * @param {object} options - Fetch options (method, body, etc.).
 * @returns {Promise<any>} - The JSON response data.
 */
export const fetchWithAuth = async (url, options = {}) => {
  const token = getToken();
  const headers = {
    ...options.headers,
    // Only add Content-Type if body exists and is not FormData
    ...(options.body && !(options.body instanceof FormData) && { 'Content-Type': 'application/json' }),
    ...(token && { 'Authorization': `Bearer ${token}` }), // Add auth header if token exists
  };

  // Only stringify body if it exists and is not FormData
  let body = options.body;
  if (body && !(body instanceof FormData)) {
    body = JSON.stringify(body);
  }

  try {
      const response = await fetch(url, { ...options, headers, body });

      if (!response.ok) {
        let errorData = { error: `Request failed with status ${response.status}` };
        try {
            // Try to parse JSON error response from backend
            errorData = await response.json();
        } catch (_err) {
            // If parsing fails, use the status text
            errorData.error = errorData.error + ": " + response.statusText;
            console.warn("Could not parse error response as JSON.", _err);
        }
        throw new Error(errorData.error || "An unknown API error occurred");
      }

      // Handle cases with no content (e.g., 204 No Content)
      if (response.status === 204) {
          return null; 
      }

      return response.json(); // Parse JSON response by default
  } catch (error) {
      console.error("API request error:", error);
      // Re-throw the error so it can be caught by the calling component
      throw error;
  }
}; 
