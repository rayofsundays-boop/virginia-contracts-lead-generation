import { useState, useEffect } from 'react';
import { rfpAPI } from '../services/api';

export default function RFPsPage() {
  const [rfps, setRfps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    search: '',
    source_state: '',
    category: '',
    active_only: 'true',
  });

  useEffect(() => {
    fetchRFPs();
  }, [filters]);

  const fetchRFPs = async () => {
    setLoading(true);
    try {
      const response = await rfpAPI.getAll(filters);
      setRfps(response.data.results || response.data);
    } catch (error) {
      console.error('Error fetching RFPs:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleBookmark = async (rfpId) => {
    try {
      await rfpAPI.bookmark(rfpId, {});
      alert('RFP bookmarked successfully!');
      fetchRFPs(); // Refresh list
    } catch (error) {
      console.error('Error bookmarking RFP:', error);
      alert('Failed to bookmark RFP');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-800">
          Government Procurement Opportunities
        </h1>
      </div>

      {/* Filters */}
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="grid md:grid-cols-4 gap-4">
          <input
            type="text"
            placeholder="Search RFPs..."
            className="border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-primary-500"
            value={filters.search}
            onChange={(e) => setFilters({ ...filters, search: e.target.value })}
          />
          
          <select
            className="border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-primary-500"
            value={filters.source_state}
            onChange={(e) => setFilters({ ...filters, source_state: e.target.value })}
          >
            <option value="">All States</option>
            <option value="CA">California</option>
            <option value="TX">Texas</option>
            <option value="NY">New York</option>
            <option value="FL">Florida</option>
            <option value="VA">Virginia</option>
            {/* Add all 50 states */}
          </select>

          <select
            className="border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-primary-500"
            value={filters.category}
            onChange={(e) => setFilters({ ...filters, category: e.target.value })}
          >
            <option value="">All Categories</option>
            <option value="janitorial">Janitorial Services</option>
            <option value="construction">Construction</option>
            <option value="it_services">IT Services</option>
            <option value="consulting">Consulting</option>
            <option value="maintenance">Maintenance</option>
          </select>

          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={filters.active_only === 'true'}
              onChange={(e) =>
                setFilters({ ...filters, active_only: e.target.checked ? 'true' : 'false' })
              }
              className="rounded text-primary-600"
            />
            <span>Active Only</span>
          </label>
        </div>
      </div>

      {/* RFP List */}
      {loading ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading opportunities...</p>
        </div>
      ) : (
        <div className="space-y-4">
          {rfps.length === 0 ? (
            <div className="bg-white p-12 rounded-lg shadow text-center">
              <p className="text-gray-600 text-lg">No RFPs found matching your criteria.</p>
            </div>
          ) : (
            rfps.map((rfp) => (
              <div key={rfp.id} className="bg-white p-6 rounded-lg shadow hover:shadow-lg transition">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <h3 className="text-xl font-bold text-gray-800 mb-2">{rfp.title}</h3>
                    <div className="flex flex-wrap gap-2 mb-3">
                      <span className="px-3 py-1 bg-primary-100 text-primary-800 rounded-full text-sm font-medium">
                        {rfp.category}
                      </span>
                      <span className="px-3 py-1 bg-gray-100 text-gray-800 rounded-full text-sm">
                        {rfp.source_state}
                      </span>
                      {rfp.estimated_value && (
                        <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm">
                          ${rfp.estimated_value.toLocaleString()}
                        </span>
                      )}
                    </div>
                    <p className="text-gray-600 mb-4">{rfp.description?.substring(0, 200)}...</p>
                    <div className="flex items-center space-x-4 text-sm text-gray-500">
                      <span>📅 Due: {rfp.due_date || 'N/A'}</span>
                      <span>🏛️ {rfp.issuing_agency}</span>
                      <span>👁️ {rfp.view_count} views</span>
                    </div>
                  </div>
                  <div className="flex flex-col space-y-2 ml-4">
                    <a
                      href={rfp.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 transition text-center"
                    >
                      View Details
                    </a>
                    <button
                      onClick={() => handleBookmark(rfp.id)}
                      className="bg-gray-200 text-gray-800 px-4 py-2 rounded-lg hover:bg-gray-300 transition"
                    >
                      🔖 Bookmark
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
