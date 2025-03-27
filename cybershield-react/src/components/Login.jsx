import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [alert, setAlert] = useState({ show: false, type: '', title: '', message: '' });
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    console.log("Login form submitted with email:", email);
    
    try {
      console.log("Calling login function...");
      const result = await login(email, password);
      console.log("Login function returned:", result);
  
      if (result && result.success) {
        console.log("Login successful, navigating to dashboard...");
        navigate('/dashboard');
      } else {
        console.warn("Login completed but success flag is false or missing:", result);
        // Convert any type of error message to string
        const errorMessage = typeof result?.message === 'string' 
          ? result.message
          : (result?.message instanceof Error 
              ? result.message.message 
              : JSON.stringify(result?.message || "Unknown error"));
        
        showAlert(errorMessage);
      }
    } catch (error) {
      console.error('Login error:', error);
      // Convert error to string regardless of type
      const errorMessage = error instanceof Error
        ? error.message
        : (typeof error === 'string' 
            ? error 
            : JSON.stringify(error));
      
      showAlert(errorMessage || 'Unable to connect to the server. Please try again later.');
    }
  };

  const showAlert = (errorMessage) => {
    let title, message, type;
    
    // Ensure errorMessage is always a string
    const errorStr = String(errorMessage);

    if (errorStr.includes('not found')) {
      type = 'warning';
      title = 'Account Not Found';
      message = 'We couldn\'t find an account with this email address. Please check your email or create a new account.';
    } else if (errorStr.includes('password')) {
      type = 'danger';
      title = 'Incorrect Password';
      message = 'The password you entered is incorrect. Please try again or use the "Forgot Password" link.';
    } else {
      type = 'danger';
      title = 'Login Error';
      message = errorStr;
    }

    setAlert({ 
      show: true, 
      type, 
      title, 
      message 
    });
  };

  // Rest of component remains the same
  // ...

  const closeAlert = () => {
    setAlert({ ...alert, show: false });
  };

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  return (
    <div className="login-page">
      <div className="container">
        <div className="login-container">
          <div className="logo">
            <div className="logo-wrapper">
              <i className="fas fa-shield-alt"></i>
            </div>
            <h2>CyberShield AI</h2>
          </div>
          <h3 className="section-title">Welcome back</h3>
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
              <div className="form-text">Enter the email you used to register</div>
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
                  placeholder="Enter your password" 
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required 
                />
                <span 
                  className="input-group-text" 
                  onClick={togglePasswordVisibility} 
                  style={{ cursor: 'pointer' }}
                >
                  <i className={`fas ${showPassword ? 'fa-eye-slash' : 'fa-eye'}`}></i>
                </span>
              </div>
            </div>
            <div className="forgot-password">
              <a href="#">Forgot Password?</a>
            </div>

            <button type="submit" className="btn btn-primary w-100" id="loginButton">
              <i className="fas fa-sign-in-alt me-2"></i>Sign In
            </button>
            <div className="register-link">
              <span className="text-muted">Don't have an account?</span>
              <Link to="/register" className="ms-1">Create Account</Link>
            </div>
          </form>
          
          {alert.show && (
            <div className={`alert alert-${alert.type}`}>
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

export default Login;