import React, { useState, useEffect } from 'react';
import { fetchWithAuth } from '../utils/api';

function CommunityManager({ currentUserId }) {
  const [communities, setCommunities] = useState([]);
  const [myCommunities, setMyCommunities] = useState([]);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [all, mine] = await Promise.all([
        fetchWithAuth('/api/communities'),
        fetchWithAuth('/api/communities/mine')
      ]);
      setCommunities(all);
      setMyCommunities(mine);
    } catch (err) {
      console.error('Failed to load communities:', err);
      setError(err.message || 'Failed to load communities');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!name.trim()) return;
    try {
      await fetchWithAuth('/api/communities', {
        method: 'POST',
        body: { name, description }
      });
      setName('');
      setDescription('');
      await loadData();
    } catch (err) {
      setError(err.message || 'Failed to create community');
    }
  };

  const join = async (id) => {
    try {
      await fetchWithAuth(`/api/communities/${id}/join`, { method: 'POST' });
      await loadData();
    } catch (err) {
      setError(err.message || 'Failed to join');
    }
  };

  const leave = async (id) => {
    try {
      await fetchWithAuth(`/api/communities/${id}/leave`, { method: 'DELETE' });
      await loadData();
    } catch (err) {
      setError(err.message || 'Failed to leave');
    }
  };

  const remove = async (id) => {
    if (!window.confirm('Delete this community?')) return;
    try {
      await fetchWithAuth(`/api/communities/${id}`, { method: 'DELETE' });
      await loadData();
    } catch (err) {
      setError(err.message || 'Failed to delete');
    }
  };

  const isMember = (id) => myCommunities.some((c) => c.id === id);
  const isOwner = (community) => community.owner_id === currentUserId;

  return (
    <div className="community-manager">
      <h2>Communities</h2>
      <form onSubmit={handleCreate} className="community-create-form">
        <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Name" />
        <input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Description" />
        <button type="submit" disabled={loading}>Create</button>
      </form>
      {error && <p className="error-message">{error}</p>}
      {loading ? <p>Loading...</p> : (
        <div className="community-lists">
          <ul>
            {communities.map((c) => (
              <li key={c.id}>
                <strong>{c.name}</strong> - {c.description}
                {isMember(c.id) ? (
                  <button onClick={() => leave(c.id)}>Leave</button>
                ) : (
                  <button onClick={() => join(c.id)}>Join</button>
                )}
                {isOwner(c) && (
                  <button onClick={() => remove(c.id)}>Delete</button>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default CommunityManager;
