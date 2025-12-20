import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiService } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Check for token on mount
        const token = localStorage.getItem('token');
        if (token) {
            // Validate token or just trust it for now (ideally verify with /me)
            apiService.getMe(token)
                .then(res => setUser(res.data))
                .catch(() => {
                    localStorage.removeItem('token');
                    setUser(null);
                })
                .finally(() => setLoading(false));
        } else {
            setLoading(false);
        }
    }, []);

    const login = async (email, password) => {
        try {
            const res = await apiService.login(email, password);
            // Backend returns { access_token, token_type }
            const token = res.data.access_token;
            localStorage.setItem('token', token);

            // Fetch user details
            const userRes = await apiService.getMe();
            setUser(userRes.data);
            return true;
        } catch (e) {
            console.error("Login failed", e);
            throw e;
        }
    };

    const register = async (email, password) => {
        await apiService.register(email, password);
        // Auto login after register
        return login(email, password);
    }

    const logout = () => {
        localStorage.removeItem('token');
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{ user, login, register, logout, loading }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);
