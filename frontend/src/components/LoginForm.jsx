/*
# musikconnect tags
purpose: User login form component
inputs: identifier, password from user
outputs: login API request, authentication state
status: active
depends_on: React, fetchWithAuth
related_docs: frontend/src/components/README.md
*/
import React, { useState } from 'react';

function LoginForm({ onLoginSuccess, switchToRegister }) {
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    if (!identifier || !password) {
      setError('Please enter both username/email and password.');
      setLoading(false);
      return;
    }

    try {
      const response = await fetch('/api/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ identifier, password }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || `Login failed with status ${response.status}`);
      }

      // Handle successful login
      console.log('Login successful:', data);
      
      // Store token in localStorage
      if (data.token) {
          localStorage.setItem('authToken', data.token);
          localStorage.setItem('currentUser', JSON.stringify(data.user)); // Store user info too
          console.log("Auth token and user info stored in localStorage.");
      }
      
      onLoginSuccess(data.user); // Pass user data up to parent component

    } catch (err) {
      console.error("Login error:", err);
      setError(err.message || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-form login-form">
      <h2>Login</h2>
      <form onSubmit={handleSubmit}>
        {error && <p className="error-message">{error}</p>}
        <div className="form-group">
          <label htmlFor="login-identifier">Username or Email:</label>
          <input
            type="text"
            id="login-identifier"
            value={identifier}
            onChange={(e) => setIdentifier(e.target.value)}
            required
            placeholder="Enter username or email"
          />
        </div>
        <div className="form-group">
          <label htmlFor="login-password">Password:</label>
          <input
            type="password"
            id="login-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            placeholder="Enter password"
          />
        </div>
        <button type="submit" className="button-primary" disabled={loading}>
          {loading ? 'Logging in...' : 'Login'}
        </button>
      </form>
      <p className="switch-auth">
        Don't have an account?{' '}
        <button onClick={switchToRegister} className="link-button">
          Register here
        </button>
      </p>
    </div>
  );
}

export default LoginForm; 
