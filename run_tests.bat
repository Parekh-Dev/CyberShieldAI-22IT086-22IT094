@echo off
echo ===================================
echo CyberShield AI - Test Runner
echo Running all tests: %date% %time%
echo ===================================
echo.

echo Running Backend Tests (Python unittest)...
echo -----------------------------------
python -m unittest tests/backend/test_authentication.py
if %errorlevel% neq 0 (
  echo Backend tests FAILED!
  set TESTS_PASSED=false
) else (
  echo Backend tests PASSED!
  set TESTS_PASSED=true
)
echo.

echo Frontend Tests (Jest)...
echo -----------------------------------
echo NOTE: To run frontend tests, Jest would need to be installed and configured.
echo The frontend test file is available at tests/frontend/LoginForm.test.js
echo This test file uses Jest (equivalent to TestNG) and React Testing Library.
echo.

echo ===================================
echo Test Summary
echo ===================================
if "%TESTS_PASSED%"=="false" (
  echo Some tests failed! Check the output above for details.
  exit /b 1
) else (
  echo All backend tests passed successfully!
  exit /b 0
)
