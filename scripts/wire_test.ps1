param(
  [string]$WebBaseUrl = "http://127.0.0.1:8000",
  [string]$AdminPassword = "victus"
)

$env:WEB_BASE_URL = $WebBaseUrl
$env:VICTUS_ADMIN_PASSWORD = $AdminPassword

Push-Location "$PSScriptRoot\..\apps\web"
try {
  npm run test:wire
  if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
  }
}
finally {
  Pop-Location
}
