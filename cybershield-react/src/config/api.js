const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

    export const authService = {
        register: async (email, password) => {
            const formData = new FormData();
            formData.append('email', email);
            formData.append('password', password);
    
            const response = await fetch(`${API_URL}/auth/email/register`, {
                method: 'POST',
                body: formData,
            });
    
            const data = await response.json();
    
            if (!response.ok) {
                throw new Error(data.detail || 'Registration failed');
            }
    
            return data;
        },
    
        login: async (email, password) => {
            const formData = new FormData();
            formData.append('email', email);
            formData.append('password', password);
    
            const response = await fetch(`${API_URL}/auth/email/login`, {
                method: 'POST',
                body: formData,
            });
    
            const data = await response.json();
    
            if (!response.ok) {
                throw new Error(data.detail || 'Login failed');
            }
    
            return data;
        }
};

export const contentService = {
    analyzeText: async (content) => {
        try {
            const response = await fetch(`${API_URL}/analyze`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ content }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Analysis failed');
            }

            return {
                success: true,
                data: {
                    isHateSpeech: data.is_hate_speech,
                    confidence: data.confidence,
                    categories: data.categories
                }
            };
        } catch (error) {
            console.error('Analysis error:', error);
            return {
                success: false,
                message: error.message || 'Failed to analyze content'
            };
        }
    }
};