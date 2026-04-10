$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$targets = Get-CimInstance Win32_Process |
    Where-Object {
        $_.CommandLine -and
        $_.CommandLine -like "*api.main:app*" -and
        $_.CommandLine -like "*$root*"
    }

if (-not $targets) {
    Write-Output "No project API process found."
    exit 0
}

foreach ($target in $targets) {
    try {
        Stop-Process -Id $target.ProcessId -Force -ErrorAction Stop
        Write-Output ("Stopped PID={0}" -f $target.ProcessId)
    } catch {
        Write-Output ("Failed to stop PID={0}: {1}" -f $target.ProcessId, $_.Exception.Message)
    }
}
