import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
// Note: This assumes you have a LoginForm component in your project
// If the path is different, adjust accordingly
import LoginForm from '../../src/components/LoginForm';

// Mock API service
jest.mock('../../src/services/api', () => ({
  login: jest.fn()
}));

describe('LoginForm Component', () => {
  test('renders login form correctly', () => {
    render(<LoginForm />);
    
    // Check if form elements are present
    expect(screen.getByLabelText(/email/i) || screen.getByPlaceholderText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i) || screen.getByPlaceholderText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in|login|log in/i })).toBeInTheDocument();
  });

  test('validates email input', async () => {
    render(<LoginForm />);
    
    // Find email input (by label or placeholder)
    const emailInput = screen.getByLabelText(/email/i) || screen.getByPlaceholderText(/email/i);
    
    // Enter invalid email and trigger validation
    fireEvent.change(emailInput, { target: { value: 'invalid-email' } });
    fireEvent.blur(emailInput);
    
    // Wait for validation error
    await waitFor(() => {
      const errorMessage = screen.queryByText(/invalid|not valid|incorrect format/i);
      expect(errorMessage).toBeInTheDocument();
    });
    
    // Enter valid email
    fireEvent.change(emailInput, { target: { value: 'valid@example.com' } });
    fireEvent.blur(emailInput);
    
    // Error should disappear
    await waitFor(() => {
      const errorMessage = screen.queryByText(/invalid|not valid|incorrect format/i);
      expect(errorMessage).not.toBeInTheDocument();
    });
  });

  test('validates password field is not empty', async () => {
    render(<LoginForm />);
    
    // Find password input
    const passwordInput = screen.getByLabelText(/password/i) || screen.getByPlaceholderText(/password/i);
    
    // Focus and blur without entering value
    fireEvent.focus(passwordInput);
    fireEvent.blur(passwordInput);
    
    // Check for required field error
    await waitFor(() => {
      const errorMessage = screen.queryByText(/required|cannot be empty/i);
      expect(errorMessage).toBeInTheDocument();
    });
    
    // Enter password
    fireEvent.change(passwordInput, { target: { value: 'Password123!' } });
    fireEvent.blur(passwordInput);
    
    // Error should disappear
    await waitFor(() => {
      const errorMessage = screen.queryByText(/required|cannot be empty/i);
      expect(errorMessage).not.toBeInTheDocument();
    });
  });

  test('submits form with valid data', async () => {
    // Mock successful login
    const mockLogin = require('../../src/services/api').login;
    mockLogin.mockResolvedValue({ success: true });
    
    render(<LoginForm />);
    
    // Find form elements
    const emailInput = screen.getByLabelText(/email/i) || screen.getByPlaceholderText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i) || screen.getByPlaceholderText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in|login|log in/i });
    
    // Fill form with valid data
    fireEvent.change(emailInput, { target: { value: 'user@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'Password123!' } });
    
    // Submit form
    fireEvent.click(submitButton);
    
    // Check if API was called with correct values
    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith(
        expect.objectContaining({
          email: 'user@example.com',
          password: 'Password123!'
        })
      );
    });
  });
});
