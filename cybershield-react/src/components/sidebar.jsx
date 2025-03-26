import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const Sidebar = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { logout } = useAuth();
  
  const handleLogout = () => {
    logout();
    navigate('/login');
  };
  
  return (
    <nav className="sidebar">
      <div className="sidebar-logo">
        <div className="logo-container">
          <div className="logo-icon">
            <i className="fas fa-shield-alt"></i>
          </div>
          <h4 className="logo-text">CyberShield AI</h4>
        </div>
      </div>
      
      <div className="nav-section mb-4">
        <Link to="/dashboard" className={`sidebar-link ${location.pathname === '/dashboard' ? 'active' : ''}`}>
          <i className="fas fa-home"></i>
          Dashboard
        </Link>
        <Link to="#" className="sidebar-link">
          <i className="fas fa-history"></i>
          Analysis History
        </Link>
      </div>
      
      <div className="nav-section mt-auto">
        <Link to="#" onClick={handleLogout} className="sidebar-link">
          <i className="fas fa-sign-out-alt"></i>
          Logout
        </Link>
      </div>
    </nav>
  );
};

export default Sidebar;