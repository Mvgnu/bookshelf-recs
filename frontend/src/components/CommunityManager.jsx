/*
# musikconnect tags
purpose: Manage reading communities from the UI
inputs: API responses, user form inputs
outputs: community list UI, join/leave/edit actions
status: active
depends_on: React, fetchWithAuth
related_docs: frontend/src/components/README.md
*/
import React, { useState, useEffect } from 'react';
import { fetchWithAuth } from '../utils/api';

function CommunityManager({ currentUserId }) {
  const [communities, setCommunities] = useState([]);
  const [myCommunities, setMyCommunities] = useState([]);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');
  const [editingId, setEditingId] = useState(null);
  const [editName, setEditName] = useState('');
  const [editDesc, setEditDesc] = useState('');

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const all = search.trim()
        ? await fetchWithAuth(`/api/communities/search?q=${encodeURIComponent(search)}`)
        : await fetchWithAuth('/api/communities');
      const mine = await fetchWithAuth('/api/communities/mine');
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

  useEffect(() => { loadData(); }, [search]);

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

  const startEdit = (c) => {
    setEditingId(c.id);
    setEditName(c.name);
    setEditDesc(c.description || '');
  };

  const saveEdit = async (e) => {
    e.preventDefault();
    try {
      await fetchWithAuth(`/api/communities/${editingId}`, {
        method: 'PUT',
        body: { name: editName, description: editDesc }
      });
      setEditingId(null);
      await loadData();
    } catch (err) {
      setError(err.message || 'Failed to update');
    }
  };

  const cancelEdit = () => {
    setEditingId(null);
  };

  const isMember = (id) => myCommunities.some((c) => c.id === id);
  const isOwner = (community) => community.owner_id === currentUserId;

  return (
    <div className="community-manager">
      <h2>Communities</h2>
      <input
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder="Search..."
        className="community-search"
      />
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
                {editingId === c.id ? (
                  <form onSubmit={saveEdit} className="community-edit-form">
                    <input value={editName} onChange={(e) => setEditName(e.target.value)} />
                    <input value={editDesc} onChange={(e) => setEditDesc(e.target.value)} />
                    <button type="submit">Save</button>
                    <button type="button" onClick={cancelEdit}>Cancel</button>
                  </form>
                ) : (
                  <>
                    <strong>{c.name}</strong> - {c.description}
                    {isOwner(c) && (
                      <>
                        <button onClick={() => startEdit(c)}>Edit</button>
                        <button onClick={() => remove(c.id)}>Delete</button>
                      </>
                    )}
                    {isMember(c.id) ? (
                      <button onClick={() => leave(c.id)}>Leave</button>
                    ) : (
                      <button onClick={() => join(c.id)}>Join</button>
                    )}
                  </>
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
