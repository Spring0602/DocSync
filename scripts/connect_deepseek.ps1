# Run in your current PowerShell terminal; never put an API key in this file.
[CmdletBinding()]
param()

$secureKey = Read-Host 'Enter your DeepSeek API key (hidden input)' -AsSecureString
$keyPointer = [IntPtr]::Zero
$plainKey = $null
$headers = $null
try {
    $keyPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)
    $plainKey = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($keyPointer).Trim()
    if ([string]::IsNullOrWhiteSpace($plainKey)) {
        Write-Host 'No key entered. Current environment was not changed.' -ForegroundColor Yellow
        return
    }

    $headers = @{ Authorization = 'Bearer ' + $plainKey }
    Write-Host 'Checking authentication with DeepSeek /models ...'
    $response = Invoke-RestMethod -Uri 'https://api.deepseek.com/models' -Method Get -Headers $headers -TimeoutSec 30 -ErrorAction Stop
    $modelIds = @($response.data | ForEach-Object { $_.id } | Where-Object { $_ })
    if ($modelIds.Count -eq 0) {
        Write-Host 'No model list returned. Current environment was not changed.' -ForegroundColor Yellow
        return
    }

    $env:DOCSYNC_API_KEY = $plainKey
    Write-Host 'Connected. DOCSYNC_API_KEY is set for this terminal and its child processes.' -ForegroundColor Green
    Write-Host 'Available models:'
    $modelIds | ForEach-Object { Write-Host ('  ' + $_) }
    Write-Host 'No chat request was sent. Run DocSync commands in this same terminal.'
    Write-Host 'To clear the key: Remove-Item Env:DOCSYNC_API_KEY'
}
catch {
    # Do not print raw exceptions or response bodies: they may contain credentials.
    $status = $null
    if ($null -ne $_.Exception.Response) {
        try { $status = [int]$_.Exception.Response.StatusCode } catch { }
    }
    if ($null -ne $status) {
        Write-Host ('Connection failed (HTTP ' + $status + '). Check key validity and service access.') -ForegroundColor Red
    }
    else {
        Write-Host 'Connection failed or timed out. Check network/proxy access and retry.' -ForegroundColor Red
    }
    Write-Host 'Current environment was not changed; an earlier key, if present, is still set.'
}
finally {
    if ($null -ne $headers) { $headers.Clear() }
    $plainKey = $null
    if ($keyPointer -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($keyPointer)
    }
    if ($null -ne $secureKey) { $secureKey.Dispose() }
}