/*
# musikconnect tags
purpose: Handle friend requests and manage friends
inputs: API data, user inputs
outputs: friend management UI, API calls
status: active
depends_on: React, fetchWithAuth
related_docs: frontend/src/components/README.md
*/
import React, { useState, useEffect } from 'react';
import { fetchWithAuth } from '../utils/api';

function FriendManager() {
  const [friends, setFriends] = useState([]);
  const [incoming, setIncoming] = useState([]);
  const [outgoing, setOutgoing] = useState([]);
  const [requestUserId, setRequestUserId] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedShelves, setSelectedShelves] = useState([]);
  const [selectedFriend, setSelectedFriend] = useState(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [friendsData, incomingData, outgoingData] = await Promise.all([
        fetchWithAuth('/api/friends'),
        fetchWithAuth('/api/friends/requests'),
        fetchWithAuth('/api/friends/outgoing')
      ]);
      setFriends(friendsData);
      setIncoming(incomingData);
      setOutgoing(outgoingData);
    } catch (err) {
      console.error('Failed to load friend data:', err);
      setError(err.message || 'Failed to load friend data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSendRequest = async (e) => {
    e.preventDefault();
    if (!requestUserId.trim()) return;
    try {
      await fetchWithAuth(`/api/friends/${requestUserId}`, { method: 'POST' });
      setRequestUserId('');
      await loadData();
    } catch (err) {
      setError(err.message || 'Failed to send request');
    }
  };

  const accept = async (userId) => {
    try {
      await fetchWithAuth(`/api/friends/${userId}`, { method: 'POST' });
      await loadData();
    } catch (err) {
      setError(err.message || 'Failed to accept');
    }
  };

  const declineOrCancel = async (userId) => {
    try {
      await fetchWithAuth(`/api/friends/${userId}`, { method: 'DELETE' });
      await loadData();
    } catch (err) {
      setError(err.message || 'Failed to update request');
    }
  };

  const removeFriend = async (userId) => {
    if (!window.confirm('Remove this friend?')) return;
    try {
      await fetchWithAuth(`/api/friends/${userId}`, { method: 'DELETE' });
      await loadData();
    } catch (err) {
      setError(err.message || 'Failed to remove friend');
    }
  };

  const viewShelves = async (userId, username) => {
    setError(null);
    setSelectedShelves([]);
    setSelectedFriend(username);
    try {
      const data = await fetchWithAuth(`/api/users/${userId}/bookshelves`);
      setSelectedShelves(data);
    } catch (err) {
      setError(err.message || 'Failed to fetch shelves');
    }
  };

  return (
    <div className="friend-manager">
      <h2>Friends</h2>
      <form onSubmit={handleSendRequest} className="friend-request-form">
        <input
          type="number"
          placeholder="User ID"
          value={requestUserId}
          onChange={(e) => setRequestUserId(e.target.value)}
          className="request-input"
        />
        <button type="submit" disabled={loading}>Send Request</button>
      </form>
      {error && <p className="error-message">{error}</p>}
      {loading ? (
        <p>Loading...</p>
      ) : (
        <div className="friend-lists">
          <div className="friend-section">
            <h3>Incoming Requests</h3>
            {incoming.length === 0 ? <p>No requests</p> : (
              <ul>
                {incoming.map((req) => (
                  <li key={req.id}>
                    {req.from_user.username}
                    <button onClick={() => accept(req.from_user.id)}>Accept</button>
                    <button onClick={() => declineOrCancel(req.from_user.id)}>Decline</button>
                  </li>
                ))}
              </ul>
            )}
          </div>
          <div className="friend-section">
            <h3>Outgoing Requests</h3>
            {outgoing.length === 0 ? <p>No outgoing</p> : (
              <ul>
                {outgoing.map((req) => (
                  <li key={req.id}>
                    {req.to_user.username}
                    <button onClick={() => declineOrCancel(req.to_user.id)}>Cancel</button>
                  </li>
                ))}
              </ul>
            )}
          </div>
          <div className="friend-section">
            <h3>Friends List</h3>
            {friends.length === 0 ? <p>No friends yet</p> : (
              <ul>
                {friends.map((u) => (
                  <li key={u.id}>
                    {u.username}
                    <button onClick={() => viewShelves(u.id, u.username)}>View Shelves</button>
                    <button onClick={() => removeFriend(u.id)}>Unfriend</button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
      {selectedFriend && (
        <div className="friend-shelves">
          <h3>{selectedFriend}'s Bookshelves</h3>
          {selectedShelves.length === 0 ? (
            <p>No shelves available</p>
          ) : (
            <ul>
              {selectedShelves.map((s) => (
                <li key={s.id}>{s.name} ({s.book_count} books)</li>
              ))}
            </ul>
          )}
          <button onClick={() => { setSelectedFriend(null); setSelectedShelves([]); }}>Close</button>
        </div>
      )}
    </div>
  );
}

export default FriendManager;
