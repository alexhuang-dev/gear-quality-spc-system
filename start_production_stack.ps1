$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $root ".venv\Scripts\python.exe"
$logDir = Join-Path $root ".tmp\production"

if (-not (Test-Path $python)) {
    throw "Missing virtual environment Python: $python"
}

New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$services = @(
    @{
        Name = "api.main:app"
        Match = "*api.main:app*"
        File = $python
        Args = @("-m", "uvicorn", "api.main:app", "--host", "127.0.0.1", "--port", "8000")
        Stdout = Join-Path $logDir "api.stdout.log"
        Stderr = Join-Path $logDir "api.stderr.log"
    },
    @{
        Name = "services.auto_runner"
        Match = "*services.auto_runner*"
        File = $python
        Args = @("-m", "services.auto_runner", "--watch")
        Stdout = Join-Path $logDir "auto_runner.stdout.log"
        Stderr = Join-Path $logDir "auto_runner.stderr.log"
    },
    @{
        Name = "dashboard.streamlit_app"
        Match = "*dashboard\\streamlit_app.py*"
        File = $python
        Args = @("-m", "streamlit", "run", "dashboard\\streamlit_app.py", "--server.headless", "true", "--server.port", "8501")
        Stdout = Join-Path $logDir "dashboard.stdout.log"
        Stderr = Join-Path $logDir "dashboard.stderr.log"
    }
)

foreach ($service in $services) {
    $existing = Get-CimInstance Win32_Process |
        Where-Object {
            $_.CommandLine -and
            $_.CommandLine -like $service.Match -and
            $_.CommandLine -like "*$root*"
        }

    if ($existing) {
        Write-Output ("Already running: {0}" -f $service.Name)
        $existing | Select-Object ProcessId, Name, CommandLine
        continue
    }

    $process = Start-Process `
        -FilePath $service.File `
        -ArgumentList $service.Args `
        -WorkingDirectory $root `
        -RedirectStandardOutput $service.Stdout `
        -RedirectStandardError $service.Stderr `
        -PassThru

    Write-Output ("Started {0} PID={1}" -f $service.Name, $process.Id)
}

Write-Output "Production stack startup requested."
