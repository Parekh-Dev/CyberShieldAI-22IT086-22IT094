import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

// Instead of importing and mocking a specific API service,
// let's create a mock component for demonstration purposes

// Mock LoginForm component for testing
const LoginForm = () => {
  const [email, setEmail] = React.useState('');
  const [password, setPassword] = React.useState('');
  const [emailError, setEmailError] = React.useState('');
  const [passwordError, setPasswordError] = React.useState('');
  const [isSubmitting, setIsSubmitting] = React.useState(false);

  const validateEmail = (email) => {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
  };

  const validatePassword = (password) => {
    return password.length >= 8;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    let isValid = true;
    
    if (!validateEmail(email)) {
      setEmailError('Please enter a valid email address');
      isValid = false;
    } else {
      setEmailError('');
    }
    
    if (!validatePassword(password)) {
      setPasswordError('Password must be at least 8 characters long');
      isValid = false;
    } else {
      setPasswordError('');
    }
    
    if (isValid) {
      setIsSubmitting(true);
      // In a real component, this would call an API
      console.log('Form submitted with:', { email, password });
      setTimeout(() => {
        setIsSubmitting(false);
      }, 1000);
    }
  };

  return (
    <form onSubmit={handleSubmit} data-testid="login-form">
      <div>
        <label htmlFor="email">Email</label>
        <input
          id="email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Email"
          aria-label="Email"
        />
        {emailError && <span className="error">{emailError}</span>}
      </div>
      <div>
        <label htmlFor="password">Password</label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          aria-label="Password"
        />
        {passwordError && <span className="error">{passwordError}</span>}
      </div>
      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Logging in...' : 'Login'}
      </button>
    </form>
  );
};

// Mock login function for testing
const mockLogin = jest.fn();

describe('LoginForm Component', () => {
  test('renders login form correctly', () => {
    render(<LoginForm />);
    
    // Check if form elements are present
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument();
  });

  test('validates email input', async () => {
    render(<LoginForm />);
    
    // Find email input
    const emailInput = screen.getByLabelText(/email/i);
    
    // Enter invalid email and submit form
    fireEvent.change(emailInput, { target: { value: 'invalid-email' } });
    fireEvent.submit(screen.getByTestId('login-form'));
    
    // Check for error message
    expect(await screen.findByText(/valid email/i)).toBeInTheDocument();
    
    // Enter valid email
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.submit(screen.getByTestId('login-form'));
    
    // Error should be gone for email
    expect(screen.queryByText(/valid email/i)).not.toBeInTheDocument();
  });

  test('validates password field is not empty', async () => {
    render(<LoginForm />);
    
    // Find password input
    const passwordInput = screen.getByLabelText(/password/i);
    
    // Enter short password and submit form
    fireEvent.change(passwordInput, { target: { value: 'short' } });
    fireEvent.submit(screen.getByTestId('login-form'));
    
    // Check for error message
    expect(await screen.findByText(/8 characters/i)).toBeInTheDocument();
    
    // Enter valid password
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    fireEvent.submit(screen.getByTestId('login-form'));
    
    // Error should be gone for password
    expect(screen.queryByText(/8 characters/i)).not.toBeInTheDocument();
  });

  test('submits form with valid data', async () => {
    // Create a spy on console.log
    jest.spyOn(console, 'log').mockImplementation(() => {});
    
    render(<LoginForm />);
    
    // Find inputs
    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    
    // Fill form with valid data
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    
    // Submit form
    fireEvent.submit(screen.getByTestId('login-form'));
    
    // Check if console.log was called with form data
    expect(console.log).toHaveBeenCalledWith(
      'Form submitted with:',
      expect.objectContaining({
        email: 'test@example.com',
        password: 'password123'
      })
    );
    
    // Restore console.log
    console.log.mockRestore();
  });
});
