import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
// Note: This assumes you have a SecurityDashboard component in your project
// If the path is different, adjust accordingly
import SecurityDashboard from '../../src/components/SecurityDashboard';

// Mock API service
jest.mock('../../src/services/api', () => ({
  getDashboardData: jest.fn(),
  getSecurityMetrics: jest.fn()
}));

describe('SecurityDashboard Component', () => {
  beforeEach(() => {
    // Setup mock API responses
    const { getDashboardData, getSecurityMetrics } = require('../../src/services/api');
    
    getDashboardData.mockResolvedValue({
      threatCount: 145,
      lastScanDate: '2023-03-15T10:30:00Z',
      securityScore: 85,
      recentAlerts: [
        { id: 1, type: 'intrusion', severity: 'high', timestamp: '2023-03-15T09:45:00Z' },
        { id: 2, type: 'malware', severity: 'medium', timestamp: '2023-03-14T22:13:00Z' }
      ]
    });
    
    getSecurityMetrics.mockResolvedValue({
      dailyStats: [
        { date: '2023-03-15', threats: 12 },
        { date: '2023-03-14', threats: 8 },
        { date: '2023-03-13', threats: 15 }
      ]
    });
  });

  test('renders loading state initially', () => {
    render(<SecurityDashboard />);
    
    // Check for loading indicator
    expect(screen.getByText(/loading|fetching data/i)).toBeInTheDocument();
  });

  test('renders dashboard with security data', async () => {
    render(<SecurityDashboard />);
    
    // Wait for data to load
    await waitFor(() => {
      expect(screen.queryByText(/loading|fetching data/i)).not.toBeInTheDocument();
    });
    
    // Check if key metrics are displayed
    expect(screen.getByText(/145/)).toBeInTheDocument(); // Threat count
    expect(screen.getByText(/85/)).toBeInTheDocument(); // Security score
    
    // Check if recent alerts are displayed
    expect(screen.getByText(/intrusion/i)).toBeInTheDocument();
    expect(screen.getByText(/malware/i)).toBeInTheDocument();
    expect(screen.getByText(/high/i)).toBeInTheDocument();
    expect(screen.getByText(/medium/i)).toBeInTheDocument();
  });

  test('renders error state when API fails', async () => {
    // Mock API failure
    const { getDashboardData } = require('../../src/services/api');
    getDashboardData.mockRejectedValue(new Error('API Error'));
    
    render(<SecurityDashboard />);
    
    // Wait for error state
    await waitFor(() => {
      expect(screen.queryByText(/error|failed|could not load/i)).toBeInTheDocument();
    });
  });
});
