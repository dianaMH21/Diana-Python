$ErrorActionPreference = "Stop"

Set-Location -LiteralPath $PSScriptRoot

$email = Read-Host "CRM email"
$securePassword = Read-Host "CRM password" -AsSecureString
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)

try {
    $password = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
}
finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
}

$env:DASHBOARD_DATA_SOURCE = "api"
$env:CRM_EMAIL = $email
$env:CRM_PASSWORD = $password

if (-not $env:CRM_FILTERS) {
    $env:CRM_FILTERS = ""
}

python -m streamlit run app.py
