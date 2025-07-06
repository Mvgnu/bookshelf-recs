/*
# musikconnect tags
purpose: User registration form component
inputs: username, email, password
outputs: registration API request, success message
status: active
depends_on: React, fetchWithAuth
related_docs: frontend/src/components/README.md
*/
import React, { useState } from 'react';

function RegisterForm({ onRegisterSuccess, switchToLogin }) {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    setSuccessMessage('');

    if (!username || !email || !password) {
      setError('Please fill in all fields.');
      setLoading(false);
      return;
    }
    // Add more validation if needed (e.g., password strength, email format)

    try {
      const response = await fetch('/api/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, email, password }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || `Registration failed with status ${response.status}`);
      }

      console.log('Registration successful:', data);

      // Auto-login after successful registration
      try {
        const loginResponse = await fetch('/api/login', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ username, password }),
        });

        const loginData = await loginResponse.json();

        if (!loginResponse.ok) {
          throw new Error(loginData.error || 'Auto-login failed after registration');
        }

        // Store auth token and user data
        localStorage.setItem('authToken', loginData.token);
        localStorage.setItem('currentUser', JSON.stringify(loginData.user));
        
        // Call parent function to update app state
        onRegisterSuccess(loginData.user);
        console.log('Auto-login successful after registration');
      } catch (loginErr) {
        console.error("Auto-login error:", loginErr);
        setSuccessMessage('Registration successful! Please log in.');
        setTimeout(switchToLogin, 1500);
      }

    } catch (err) {
      console.error("Registration error:", err);
      setError(err.message || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-form register-form">
      <h2>Register</h2>
      <form onSubmit={handleSubmit}>
        {error && <p className="error-message">{error}</p>}
        {successMessage && <p className="success-message">{successMessage}</p>}
        <div className="form-group">
          <label htmlFor="register-username">Username:</label>
          <input
            type="text"
            id="register-username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            minLength="3"
            placeholder="Choose a username (min 3 chars)"
          />
        </div>
        <div className="form-group">
          <label htmlFor="register-email">Email:</label>
          <input
            type="email"
            id="register-email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            placeholder="Enter your email"
          />
        </div>
        <div className="form-group">
          <label htmlFor="register-password">Password:</label>
          <input
            type="password"
            id="register-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength="6"
            placeholder="Choose a password (min 6 chars)"
          />
        </div>
        <button type="submit" className="button-primary" disabled={loading}>
          {loading ? 'Registering...' : 'Register'}
        </button>
      </form>
      <p className="switch-auth">
        Already have an account?{' '}
        <button onClick={switchToLogin} className="link-button">
          Login here
        </button>
      </p>
    </div>
  );
}

export default RegisterForm; 
