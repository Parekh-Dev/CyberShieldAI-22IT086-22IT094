import { createContext, useState, useContext, useEffect } from 'react';
import { emailAuthService, phoneAuthService } from './services/api';

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    // Check if user data exists in localStorage
    const savedUser = localStorage.getItem('user');
    return savedUser ? JSON.parse(savedUser) : null;
  });

  const [authMethod, setAuthMethod] = useState(() => {
    // Check if authMethod is saved in localStorage
    const savedUser = localStorage.getItem('user');
    if (savedUser) {
      const userData = JSON.parse(savedUser);
      return userData.authMethod || 'email';
    }
    return 'email'; // Default auth method
  });

  // Update localStorage when user changes
  useEffect(() => {
    if (user) {
      localStorage.setItem('user', JSON.stringify(user));
    } else {
      localStorage.removeItem('user');
    }
  }, [user]);

  // Email login
  const login = async (email, password) => {
    const result = await emailAuthService.login(email, password);
    
    if (result.success) {
      setUser({ email, authMethod: 'email' });
      setAuthMethod('email');
    }
    
    return result;
  };

  // Email registration
  const register = async (email, password) => {
    return await emailAuthService.register(email, password);
  };

  // Phone login (using Firebase)
  const loginWithPhone = async (phoneNumber, idToken) => {
    const result = await phoneAuthService.verifyOTP(phoneNumber, idToken);
    
    if (result.success) {
      setUser({ phoneNumber, authMethod: 'phone' });
      setAuthMethod('phone');
    }
    
    return result;
  };

  // Logout
  const logout = () => {
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ 
      user, 
      login, 
      register, 
      loginWithPhone, 
      logout, 
      authMethod 
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);