import { createContext, useState, useContext } from 'react';
import { authService } from '../config/api';
const AuthContext = createContext();

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [isAuthenticated, setIsAuthenticated] = useState(false); // Add this missing state variable


    const register = async (email, password) => {
        setLoading(true);
        setError(null);
        
        try {
            await authService.register(email, password);
            return { success: true };
        } catch (error) {
            setError(error.message);
            return {
                success: false,
                message: error.message
            };
        } finally {
            setLoading(false);
        }
    };

   // Add better error handling in the login function:
   const login = async (email, password) => {
    try {
      console.log(`AuthContext: Attempting to login with email: ${email}`);
      
      const response = await authService.login(email, password);
      console.log("AuthContext: Raw login response:", response);
      
    

      // Check if we have a valid response with token
      if (!response || response.status !== 'success' ) {
        console.error("AuthContext: Invalid login response - missing token", response);
        return { 
          success: false, 
          message: "Login failed: Invalid server response"
        };
      }

      const fakeToken = `user_${response.email}_${Date.now()}`;

      
      // Store the user token in localStorage
      console.log("AuthContext: Storing authentication data");
      localStorage.setItem('token', fakeToken);
      
      // Handle user data - might be in different response formats
      const userData = response.user || response.data || {};
      localStorage.setItem('user', JSON.stringify(userData));
      
      // Update context state
      setUser(userData);
      setIsAuthenticated(true);
      
      console.log("AuthContext: Login successful, auth state updated");
      return { success: true };
    } catch (error) {
      console.error("AuthContext: Login error:", error);
      return { 
        success: false, 
        message: error.message || "Login failed"
      };
    }
  };

    const logout = () => {
       // Clear localStorage
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    
    // Reset state
    setUser(null);
    setError(null);
    setIsAuthenticated(false);
    };

    const value = {
        user,
        loading,
        error,
        isAuthenticated,  // Add this missing state
        register,
        login,
        logout
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
}

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};