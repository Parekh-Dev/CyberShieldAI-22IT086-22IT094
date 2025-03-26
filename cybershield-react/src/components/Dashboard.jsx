import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { contentService } from '../config/api';
import '../styles/dashboard.css';

const Dashboard = () => {
  const [textToAnalyze, setTextToAnalyze] = useState('');
  const [analysisResult, setAnalysisResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [recentAnalyses, setRecentAnalyses] = useState([
    {
      status: 'safe',
      time: 'Just now',
      text: 'Content analysis complete - No concerning elements detected.'
    },
    {
      status: 'hate-speech',
      time: '5 min ago',
      text: 'Content flagged for review - Potential policy violation detected.'
    }
  ]);

  const { user, logout } = useAuth();
  const navigate = useNavigate();

  // Load history from localStorage on component mount
  useEffect(() => {
    const savedAnalyses = localStorage.getItem('analysisHistory');
    if (savedAnalyses) {
      try {
        setRecentAnalyses(JSON.parse(savedAnalyses));
      } catch (e) {
        console.error('Error parsing saved history', e);
      }
    }
  }, []);

  // Save history to localStorage when it changes
  useEffect(() => {
    if (recentAnalyses.length > 0) {
      localStorage.setItem('analysisHistory', JSON.stringify(recentAnalyses));
    }
  }, [recentAnalyses]);

  const handleAnalyze = async (e) => {
    e.preventDefault();
    
    if (!textToAnalyze.trim()) {
      return;
    }
    
    setIsLoading(true);
    setAnalysisResult(null);
    
    try {
      const result = await contentService.analyzeText(textToAnalyze);
      
      if (result.success) {
        setAnalysisResult(result.data);
        
        // Add to history
        const newAnalysis = {
          status: result.data.isHateSpeech ? 'hate-speech' : 'safe',
          time: 'Just now',
          text: result.data.isHateSpeech 
            ? 'Content flagged for review - Potential policy violation detected.'
            : 'Content analysis complete - No concerning elements detected.'
        };
        
        setRecentAnalyses(prev => [newAnalysis, ...prev.slice(0, 4)]); // Keep last 5 items
      } else {
        console.error('Analysis failed:', result.message);
        alert('Analysis failed: ' + result.message);
      }
    } catch (error) {
      console.error('Error during analysis:', error);
      alert('An error occurred while analyzing text.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = (e) => {
    e.preventDefault();
    logout();
    navigate('/');
  };

  return (
    <div className="d-flex">
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
          <a href="#" className="sidebar-link active">
            <i className="fas fa-home"></i>
            Dashboard
          </a>
          <a href="#" className="sidebar-link">
            <i className="fas fa-history"></i>
            Analysis History
          </a>
        </div>
        <div className="nav-section mt-auto">
          <a href="#" className="sidebar-link" onClick={handleLogout}>
            <i className="fas fa-sign-out-alt"></i>
            Logout
          </a>
        </div>
      </nav>

      <main className="main-content">
        <div className="container-fluid">
          <h2 className="dashboard-title">Content Analysis Dashboard</h2>
          
          <div className="row">
            <div className="col-lg-8 mb-4">
              <div className="analysis-box">
                <h4 className="section-title">Analyze Text Content</h4>
                <form id="analysisForm" onSubmit={handleAnalyze}>
                  <div className="mb-3">
                    <textarea 
                      id="textToAnalyze" 
                      className="form-control text-input"
                      placeholder="Enter the text content you want to analyze..." 
                      value={textToAnalyze}
                      onChange={(e) => setTextToAnalyze(e.target.value)}
                      required>
                    </textarea>
                  </div>
                  <button 
                    type="submit" 
                    className="btn btn-primary analyze-btn"
                    disabled={isLoading || !textToAnalyze.trim()}
                  >
                    {isLoading ? (
                      <>
                        <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                        Analyzing...
                      </>
                    ) : (
                      <>
                        <i className="fas fa-search me-2"></i>Analyze Content
                      </>
                    )}
                  </button>
                </form>

                {analysisResult && !analysisResult.isHateSpeech && (
                  <div id="safeResult" className="result-box safe" style={{ display: 'block' }}>
                    <h5 className="mb-2">
                      <i className="fas fa-check-circle me-2"></i>Safe Content Detected
                    </h5>
                    <p className="mb-0">Our AI analysis indicates that this content is safe and appropriate.</p>
                  </div>
                )}

                {analysisResult && analysisResult.isHateSpeech && (
                  <div id="hateSpeechResult" className="result-box hate-speech" style={{ display: 'block' }}>
                    <h5 className="mb-2">
                      <i className="fas fa-exclamation-triangle me-2"></i>Potentially Harmful Content
                    </h5>
                    <p className="mb-0">Our AI has detected potentially inappropriate or harmful content.</p>
                  </div>
                )}
              </div>
            </div>

            <div className="col-lg-4">
              <div className="analysis-box">
                <h4 className="section-title">Recent Analyses</h4>
                {recentAnalyses.map((analysis, index) => (
                  <div key={index} className="history-item">
                    <div className="d-flex justify-content-between align-items-center">
                      {/* Fixed badge styling with inline styles to override everything */}
                      <div style={{ 
                        display: 'inline-block', 
                        width: 'auto', 
                        maxWidth: 'fit-content',
                        padding: '0',
                        margin: '0'
                      }}>
                        <div style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          backgroundColor: analysis.status === 'safe' ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                          padding: '4px 10px',
                          borderRadius: '20px',
                          fontSize: '0.8rem',
                          fontWeight: '500',
                          whiteSpace: 'nowrap',
                          border: '1px solid rgba(0,0,0,0.05)',
                          width: 'auto',
                          maxWidth: 'fit-content'
                        }}>
                          <i 
                            className={`fas ${analysis.status === 'safe' ? 'fa-check-circle' : 'fa-exclamation-triangle'}`}
                            style={{ 
                              marginRight: '6px',
                              fontSize: '0.9rem',
                              color: analysis.status === 'safe' ? '#22c55e' : '#ef4444'
                            }}
                          ></i>
                          <span>{analysis.status === 'safe' ? 'Safe' : 'Review'}</span>
                        </div>
                      </div>
                      <span className="history-time text-muted">{analysis.time}</span>
                    </div>
                    <div className="history-text mt-2">
                      {analysis.text}
                    </div>
                  </div>
                ))}
                {recentAnalyses.length === 0 && (
                  <div className="text-center text-muted p-4">
                    <i className="fas fa-info-circle mb-2 d-block" style={{ fontSize: '2rem' }}></i>
                    <p>No analysis history yet.<br />Analyzed text will appear here.</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;