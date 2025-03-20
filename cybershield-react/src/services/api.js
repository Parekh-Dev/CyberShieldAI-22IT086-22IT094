const API_URL = "http://127.0.0.1:8000";

// Email Authentication Service
export const emailAuthService = {
  // Register user
  register: async (email, password) => {
    try {
      const formData = new URLSearchParams();
      formData.append("email", email);
      formData.append("password", password);

      const response = await fetch(`${API_URL}/auth/email/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData
      });

      const data = await response.json();
      
      if (response.ok) {
        return { success: true, message: data.message };
      } else {
        return { success: false, message: data.detail || 'Registration failed' };
      }
    } catch (error) {
      console.error('Registration error:', error);
      return { success: false, message: 'Unable to connect to the server. Please try again later.' };
    }
  },

  // Login user
  login: async (email, password) => {
    try {
      const formData = new URLSearchParams();
      formData.append("email", email);
      formData.append("password", password);

      const response = await fetch(`${API_URL}/auth/email/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData
      });

      const data = await response.json();
      
      if (response.ok) {
        return { success: true, message: data.message };
      } else {
        return { success: false, message: data.detail || 'Login failed' };
      }
    } catch (error) {
      console.error('Login error:', error);
      return { success: false, message: 'Unable to connect to the server. Please try again later.' };
    }
  }
};

// Phone Authentication Service 
export const phoneAuthService = {
  // Send OTP (Frontend will use Firebase SDK)
  sendOTP: async (phoneNumber) => {
    try {
      const response = await fetch(`${API_URL}/auth/phone/send-otp`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ phone_number: phoneNumber })
      });

      const data = await response.json();
      
      return { 
        success: response.ok, 
        message: data.message || data.detail || 'OTP request processed'
      };
    } catch (error) {
      console.error('OTP request error:', error);
      return { success: false, message: 'Unable to connect to the server. Please try again later.' };
    }
  },

  // Verify OTP with Firebase ID token
  verifyOTP: async (phoneNumber, idToken) => {
    try {
      const response = await fetch(`${API_URL}/auth/phone/verify-otp`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          phone_number: phoneNumber,
          id_token: idToken
        })
      });

      const data = await response.json();
      
      return { 
        success: response.ok, 
        message: data.message || 'OTP verified successfully',
        error: !response.ok ? data.detail : null
      };
    } catch (error) {
      console.error('OTP verification error:', error);
      return { success: false, message: 'Unable to connect to the server. Please try again later.' };
    }
  }
};

// Content Analysis Service
export const contentService = {
  // Analyze text for hate speech
  analyzeText: async (text) => {
    try {
      const response = await fetch(`${API_URL}/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ text })
      });

      const data = await response.json();
      
      if (response.ok) {
        return { success: true, data };
      } else {
        return { success: false, message: data.detail || 'Analysis failed' };
      }
    } catch (error) {
      console.error('Analysis error:', error);
      return { success: false, message: 'Unable to connect to the server. Please try again later.' };
    }
  }
};