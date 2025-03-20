import React from 'react';
import { Link } from 'react-router-dom';
import '../styles/global.css';

const Home = () => {
  // Define a more specific button style that will override other styles
  const buttonStyle = {
    display: 'inline-block',
    width: 'fit-content',
    maxWidth: '200px', // Limit maximum width
    boxSizing: 'content-box',
    flexBasis: 'auto',
    flexGrow: 0,
    whiteSpace: 'nowrap'
  };

  return (
    <>
      <nav className="navbar navbar-expand-lg navbar-dark">
        <div className="container">
          <Link className="navbar-brand" to="/">
            <i className="fas fa-shield-alt me-2"></i>CyberShield AI
          </Link>
          <button className="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
            <span className="navbar-toggler-icon"></span>
          </button>
          <div className="collapse navbar-collapse" id="navbarNav">
            <ul className="navbar-nav ms-auto">
              <li className="nav-item"><Link className="nav-link active" to="/">Home</Link></li>
              <li className="nav-item"><Link className="nav-link" to="/login">Login</Link></li>
              <li className="nav-item"><Link className="nav-link" to="/register">Sign Up</Link></li>
            </ul>
          </div>
        </div>
      </nav>

      <section className="hero-section text-white">
        <div className="container">
          <div className="row align-items-center">
            <div className="col-lg-7 hero-content">
              <h1 className="hero-title">Detect Hate Speech with AI Precision</h1>
              <p className="lead mb-4">Harness the power of artificial intelligence to identify and prevent online hate speech in real-time. Protect your community with advanced machine learning technology.</p>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem' }}>
                <Link to="/login" className="btn btn-light btn-lg" style={buttonStyle}>
                  Get Started
                </Link>
                <a href="#features" className="btn btn-outline-light btn-lg" style={buttonStyle}>
                  Learn More
                </a>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="features" className="container py-5">
        <h2 className="text-center mb-5 fw-bold">Why Choose CyberShield AI?</h2>
        <div className="row g-4">
          <div className="col-md-6">
            <div className="feature-card text-center">
              <i className="fas fa-robot feature-icon"></i>
              <h3>Advanced AI Detection</h3>
              <p>State-of-the-art machine learning algorithms for accurate hate speech detection, powered by cutting-edge natural language processing.</p>
            </div>
          </div>
          <div className="col-md-6">
            <div className="feature-card text-center">
              <i className="fas fa-bolt feature-icon"></i>
              <h3>Real-Time Analysis</h3>
              <p>Instant feedback and analysis of text content for immediate action, ensuring swift response to potential threats and violations.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="cta-section text-center">
        <div className="container">
          <h2 className="mb-4 fw-bold">Ready to Start?</h2>
          <p className="lead mb-4">Join thousands of users who trust CyberShield AI for online content moderation.</p>
          <Link to="/register" className="btn btn-custom btn-lg" style={buttonStyle}>
            Create Free Account
          </Link>
        </div>
      </section>
    </>
  );
};

export default Home;