import { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../AuthContext';

const Register = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState(0);
  const [alert, setAlert] = useState({ show: false, title: '', message: '' });
  const passwordStrengthBarRef = useRef(null);
  const navigate = useNavigate();
  const { register } = useAuth();

  useEffect(() => {
    evaluatePasswordStrength(password);
  }, [password]);

  const evaluatePasswordStrength = (password) => {
    let strength = 0;
    
    if (password.length >= 8) strength++;
    if (password.match(/[a-z]/) && password.match(/[A-Z]/)) strength++;
    if (password.match(/[0-9]/)) strength++;
    if (password.match(/[^a-zA-Z0-9]/)) strength++;
    
    setPasswordStrength(strength);
    
    if (passwordStrengthBarRef.current) {
      const width = strength * 25;
      let color;
      
      if (width >= 75) color = '#22c55e';
      else if (width >= 50) color = '#eab308';
      else if (width >= 25) color = '#f97316';
      else color = '#ef4444';
      
      passwordStrengthBarRef.current.style.width = width + '%';
      passwordStrengthBarRef.current.style.backgroundColor = color;
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Domain validation
    const allowedDomains = ['gmail.com', 'yahoo.com', 'charusat.edu.in', 'charusat.ac.in'];
    const domain = email.substring(email.lastIndexOf('@') + 1);
    
    if (!allowedDomains.includes(domain)) {
      showAlertMessage('Domain Not Allowed', 'Please register with a valid domain: gmail.com, yahoo.com, charusat.edu.in, charusat.ac.in');
      return;
    }
    
    try {
      const result = await register(email, password);
      
      if (result.success) {
        navigate('/login');
      } else {
        showAlertMessage('Registration Error', result.message);
      }
    } catch (error) {
      console.error('Error:', error);
      showAlertMessage('Connection Error', 'Unable to connect to the server. Please try again later.');
    }
  };

  const showAlertMessage = (title, message) => {
    setAlert({
      show: true,
      title,
      message
    });
  };

  const closeAlert = () => {
    setAlert({ ...alert, show: false });
  };

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  return (
    <div className="register-page">
      <div className="container">
        <div className="register-container">
          <div className="logo">
            <div className="logo-wrapper">
              <i className="fas fa-shield-alt"></i>
            </div>
            <h2>CyberShield AI</h2>
          </div>
          <h3 className="section-title">Create your account</h3>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label" htmlFor="email">Email Address</label>
              <div className="input-group">
                <span className="input-group-text">
                  <i className="fas fa-envelope"></i>
                </span>
                <input 
                  type="email" 
                  className="form-control" 
                  id="email" 
                  name="email" 
                  placeholder="Enter your email" 
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required 
                />
              </div>
              <div className="form-text">We'll never share your email with anyone else.</div>
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="password">Password</label>
              <div className="input-group">
                <span className="input-group-text">
                  <i className="fas fa-lock"></i>
                </span>
                <input 
                  type={showPassword ? "text" : "password"} 
                  className="form-control" 
                  id="password" 
                  name="password" 
                  placeholder="Create a password" 
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required 
                />
                <span 
                  className="input-group-text" 
                  onClick={togglePasswordVisibility} 
                  style={{ cursor: 'pointer' }}
                >
                  <i className={`fas ${showPassword ? 'fa-eye-slash' : 'fa-eye'}`} id="eyeIcon"></i>
                </span>
              </div>
              <div className="password-strength">
                <div className="password-strength-bar" ref={passwordStrengthBarRef}></div>
              </div>
              <div className="password-requirements">
                <div className="fw-medium mb-2">Password must contain:</div>
                <ul>
                  <li className={password.length >= 8 ? "text-success" : ""}>At least 8 characters</li>
                  <li className={password.match(/[a-z]/) && password.match(/[A-Z]/) ? "text-success" : ""}>
                    Upper and lowercase letters
                  </li>
                  <li className={password.match(/[0-9]/) ? "text-success" : ""}>At least one number</li>
                  <li className={password.match(/[^a-zA-Z0-9]/) ? "text-success" : ""}>
                    At least one special character
                  </li>
                </ul>
              </div>
            </div>

            <button type="submit" className="btn btn-primary w-100">
              <i className="fas fa-user-plus me-2"></i>Create Account
            </button>

            <div className="login-link">
              <span className="text-muted">Already have an account?</span>
              <Link to="/login" className="ms-1">Sign In</Link>
            </div>
          </form>
          
          {alert.show && (
            <div className="alert alert-danger" style={{ display: 'flex' }}>
              <i className="fas fa-circle-exclamation"></i>
              <div className="alert-content">
                <div className="alert-title">{alert.title}</div>
                <div className="alert-message">{alert.message}</div>
              </div>
              <div className="alert-close" onClick={closeAlert}>
                <i className="fas fa-xmark"></i>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Register;