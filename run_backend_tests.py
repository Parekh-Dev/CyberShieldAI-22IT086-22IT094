"""
CyberShield AI - Backend Test Runner
Run all backend tests in the tests/backend directory
"""

import unittest
import sys
import os

def run_tests():
    """Run all backend tests"""
    print('=' * 70)
    print('CyberShield AI - Running Backend Tests')
    print('=' * 70)
    
    # Configure test discovery
    test_loader = unittest.TestLoader()
    
    # Discover and load tests
    base_dir = os.path.abspath(os.path.dirname(__file__))
    test_dir = os.path.join(base_dir, 'tests', 'backend')
    test_suite = test_loader.discover(test_dir, pattern='test_*.py')
    
    # Run tests
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # Print summary
    print('\n' + '=' * 70)
    print('Test Summary:')
    print(f'  Ran {result.testsRun} tests')
    print(f'  Failures: {len(result.failures)}')
    print(f'  Errors: {len(result.errors)}')
    print('=' * 70)
    
    # Exit with error code if tests fail
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    sys.exit(run_tests())
