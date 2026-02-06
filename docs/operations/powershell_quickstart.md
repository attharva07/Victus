# Victus Local PowerShell Quickstart (Layer 2)

## 1) Start server
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn apps.local.main:app --host 127.0.0.1 --port 8000
```

## 2) Health
```powershell
Invoke-RestMethod -Method GET -Uri "http://127.0.0.1:8000/health"
```

## 3) Bootstrap status
```powershell
Invoke-RestMethod -Method GET -Uri "http://127.0.0.1:8000/bootstrap/status"
```

## 4) First-time bootstrap init (run once only)
```powershell
$bootstrapBody = @{ username = "admin"; password = "change-me-now-123" } | ConvertTo-Json
Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8000/bootstrap/init" -ContentType "application/json" -Body $bootstrapBody
```

## 5) Login and capture token
```powershell
$loginBody = @{ username = "admin"; password = "change-me-now-123" } | ConvertTo-Json
$login = Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8000/login" -ContentType "application/json" -Body $loginBody
$token = $login.access_token
$headers = @{ Authorization = "Bearer $token" }
```

## 6) Verify session
```powershell
Invoke-RestMethod -Method GET -Uri "http://127.0.0.1:8000/me" -Headers $headers
```

## 7) Orchestrate examples

### Memory add
```powershell
$body = @{ text = "remember buy oat milk" } | ConvertTo-Json
Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8000/orchestrate" -Headers $headers -ContentType "application/json" -Body $body
```

### Memory search
```powershell
$body = @{ text = "recall oat milk" } | ConvertTo-Json
Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8000/orchestrate" -Headers $headers -ContentType "application/json" -Body $body
```

### Finance add
```powershell
$body = @{ text = "spent 4.25 on coffee" } | ConvertTo-Json
Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8000/orchestrate" -Headers $headers -ContentType "application/json" -Body $body
```

### Finance summary
```powershell
$body = @{ text = "finance summary" } | ConvertTo-Json
Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8000/orchestrate" -Headers $headers -ContentType "application/json" -Body $body
```

### Files write
```powershell
$body = @{ text = "write to notes.txt: hello from powershell" } | ConvertTo-Json
Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8000/orchestrate" -Headers $headers -ContentType "application/json" -Body $body
```

### Files read
```powershell
$body = @{ text = "read file notes.txt" } | ConvertTo-Json
Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8000/orchestrate" -Headers $headers -ContentType "application/json" -Body $body
```

### Files list
```powershell
$body = @{ text = "list files" } | ConvertTo-Json
Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8000/orchestrate" -Headers $headers -ContentType "application/json" -Body $body
```

### Camera status (gated)
```powershell
$body = @{ text = "camera status" } | ConvertTo-Json
Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8000/orchestrate" -Headers $headers -ContentType "application/json" -Body $body
```
