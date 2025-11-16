import { Link } from 'react-router-dom';
import { useState } from 'react';

export default function Navbar() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const isAuthenticated = !!localStorage.getItem('authToken');

  const handleLogout = () => {
    localStorage.removeItem('authToken');
    window.location.href = '/login';
  };

  return (
    <nav className="bg-primary-600 text-white shadow-lg">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center py-4">
          {/* Logo */}
          <Link to="/" className="text-2xl font-bold">
            ContractLink AI
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex space-x-6 items-center">
            <Link to="/rfps" className="hover:text-primary-200 transition">
              Browse RFPs
            </Link>
            <Link to="/states" className="hover:text-primary-200 transition">
              States
            </Link>
            <Link to="/cities" className="hover:text-primary-200 transition">
              Cities
            </Link>
            
            {isAuthenticated ? (
              <>
                <Link to="/dashboard" className="hover:text-primary-200 transition">
                  Dashboard
                </Link>
                <Link to="/settings" className="hover:text-primary-200 transition">
                  Settings
                </Link>
                <button
                  onClick={handleLogout}
                  className="bg-white text-primary-600 px-4 py-2 rounded-lg hover:bg-primary-50 transition"
                >
                  Logout
                </button>
              </>
            ) : (
              <>
                <Link to="/login" className="hover:text-primary-200 transition">
                  Login
                </Link>
                <Link
                  to="/register"
                  className="bg-white text-primary-600 px-4 py-2 rounded-lg hover:bg-primary-50 transition"
                >
                  Sign Up
                </Link>
              </>
            )}
          </div>

          {/* Mobile menu button */}
          <button
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            className="md:hidden focus:outline-none"
          >
            <svg
              className="w-6 h-6"
              fill="none"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              {isMenuOpen ? (
                <path d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path d="M4 6h16M4 12h16M4 18h16" />
              )}
            </svg>
          </button>
        </div>

        {/* Mobile Navigation */}
        {isMenuOpen && (
          <div className="md:hidden pb-4 space-y-2">
            <Link to="/rfps" className="block hover:text-primary-200 py-2">
              Browse RFPs
            </Link>
            <Link to="/states" className="block hover:text-primary-200 py-2">
              States
            </Link>
            <Link to="/cities" className="block hover:text-primary-200 py-2">
              Cities
            </Link>
            {isAuthenticated ? (
              <>
                <Link to="/dashboard" className="block hover:text-primary-200 py-2">
                  Dashboard
                </Link>
                <Link to="/settings" className="block hover:text-primary-200 py-2">
                  Settings
                </Link>
                <button
                  onClick={handleLogout}
                  className="block w-full text-left hover:text-primary-200 py-2"
                >
                  Logout
                </button>
              </>
            ) : (
              <>
                <Link to="/login" className="block hover:text-primary-200 py-2">
                  Login
                </Link>
                <Link to="/register" className="block hover:text-primary-200 py-2">
                  Sign Up
                </Link>
              </>
            )}
          </div>
        )}
      </div>
    </nav>
  );
}
