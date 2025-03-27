Write-Host "(Note: You'll see a redirect response if working correctly)"
Write-Host "Testing HTTP on port 3000..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:3000" -MaximumRedirection 0 -ErrorAction SilentlyContinue
    Write-Host "Response: $($response.StatusCode)" -ForegroundColor Cyan
} catch {
    if ($_.Exception.Response.StatusCode.value__ -eq 301) {
        Write-Host "HTTP correctly redirects to HTTPS (301)" -ForegroundColor Green
    } else {
        Write-Host "HTTP Error: $_" -ForegroundColor Red
    }
}


Write-Host "`nTrying to connect to HTTPS directly..." -ForegroundColor Yellow
try {
    # Ignore certificate errors for self-signed cert
    [System.Net.ServicePointManager]::ServerCertificateValidationCallback = {$true}
    $response = Invoke-WebRequest -Uri "https://localhost" -ErrorAction Stop
    Write-Host "Success! HTTPS connection works" -ForegroundColor Green
    Write-Host "Status code: $($response.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "HTTPS Error: $_" -ForegroundColor Red
}