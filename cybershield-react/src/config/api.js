const API_URL = '/api';

export const authService = {
    register: async (email, password) => {
        try {
            // Use URLSearchParams for proper form encoding
            const formData = new URLSearchParams();
            formData.append('email', email);
            formData.append('password', password);
    
            const response = await fetch(`${API_URL}/auth/email/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: formData,
            });
    
            // Safe parsing of response
            const text = await response.text();
            let data;
            
            try {
                data = JSON.parse(text);
            } catch (e) {
                console.error("Invalid JSON response:", text.substring(0, 100));
                throw new Error("Server returned invalid response");
            }
    
            if (!response.ok) {
                throw new Error(data.detail || 'Registration failed');
            }
    
            return data;
        } catch (error) {
            console.error("Registration error:", error);
            throw error;
        }
    },
    
    login: async (email, password) => {
        try {
            console.log("Attempting login with:", email);
            
            // Use URLSearchParams for proper form data encoding
            const formData = new URLSearchParams();
            formData.append('email', email);
            formData.append('password', password);
            
            const response = await fetch(`${API_URL}/auth/email/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: formData,
            });
            
            // Get raw response for debugging
            const text = await response.text();
            console.log("Raw API response:", text);
            
            // Try to parse as JSON
            let data;
            try {
                data = JSON.parse(text);
                console.log("Parsed API response structure:", JSON.stringify(data, null, 2));
                // Check fields that might contain token
                console.log("Available top-level fields:", Object.keys(data));
                
                // Adjust the data structure to ensure token is at the top level
                // Example - if token is nested like data.access_token or data.auth.token
                if (!data.token) {
                    if (data.access_token) {
                        data.token = data.access_token;
                    } else if (data.auth && data.auth.token) {
                        data.token = data.auth.token;
                    } else if (data.jwt) {
                        data.token = data.jwt;
                    }
                }
                
            } catch (e) {
                console.error("Failed to parse response:", text);
                throw new Error(`Server returned invalid response: ${text.substring(0, 50)}...`);
            }
            
            // Handle both successful and error responses
            if (!response.ok) {
                const errorMessage = data.detail || JSON.stringify(data) || 'Login failed';
                console.error("Login error from server:", errorMessage);
                throw new Error(errorMessage);
            }
            
            console.log("Login successful:", data);
            return data;
        } catch (error) {
            console.error("Login error:", error);
            throw error;
        }
    },
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

            // Safe parsing of response
            const text = await response.text();
            let data;
            
            try {
                data = JSON.parse(text);
            } catch (e) {
                console.error("Invalid JSON response:", text.substring(0, 100));
                throw new Error("Analysis failed: Invalid response");
            }

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