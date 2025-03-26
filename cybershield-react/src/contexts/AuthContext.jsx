import { createContext, useState, useContext } from 'react';
import { authService } from '../config/api';
const AuthContext = createContext();

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

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

    const login = async (email, password) => {
        setLoading(true);
        setError(null);
        
        try {
            const data = await authService.login(email, password);
            setUser(data);
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

    const logout = () => {
        setUser(null);
        setError(null);
    };

    const value = {
        user,
        loading,
        error,
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