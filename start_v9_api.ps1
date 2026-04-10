$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $root ".venv\Scripts\python.exe"
$logDir = Join-Path $root ".tmp\server"
$stdoutLog = Join-Path $logDir "uvicorn.stdout.log"
$stderrLog = Join-Path $logDir "uvicorn.stderr.log"

if (-not (Test-Path $python)) {
    throw "Missing virtual environment Python: $python"
}

New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$existing = Get-CimInstance Win32_Process |
    Where-Object {
        $_.CommandLine -and
        $_.CommandLine -like "*api.main:app*" -and
        $_.CommandLine -like "*$root*"
    }

if ($existing) {
    Write-Output "API already running."
    $existing | Select-Object ProcessId, Name, CommandLine
    exit 0
}

$process = Start-Process `
    -FilePath $python `
    -ArgumentList "-m", "uvicorn", "api.main:app", "--host", "127.0.0.1", "--port", "8000" `
    -WorkingDirectory $root `
    -RedirectStandardOutput $stdoutLog `
    -RedirectStandardError $stderrLog `
    -PassThru

Write-Output "Started API process."
Write-Output ("PID={0}" -f $process.Id)
Write-Output ("STDOUT={0}" -f $stdoutLog)
Write-Output ("STDERR={0}" -f $stderrLog)
