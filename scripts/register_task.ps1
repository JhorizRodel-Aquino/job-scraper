<#
.SYNOPSIS
    Registers (or re-registers) a Windows Task Scheduler entry that runs
    `job-scraper scrape` on a daily schedule.

.DESCRIPTION
    This script is NOT run automatically as part of setup. Review it, then
    run it yourself from an elevated PowerShell prompt when you're ready to
    schedule the crawler:

        .\scripts\register_task.ps1

    It assumes the project venv lives at .venv\Scripts\python.exe relative
    to the repo root. Adjust -StartTime / -TaskName as you like.

.PARAMETER StartTime
    Daily run time, 24h "HH:mm" format. Default: 06:00.

.PARAMETER TaskName
    Name of the scheduled task. Default: JobScraperDailyRun.
#>

param(
    [string]$StartTime = "06:00",
    [string]$TaskName = "JobScraperDailyRun"
)

$RepoRoot = Split-Path -Parent $PSScriptRoot
$PythonExe = Join-Path $RepoRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $PythonExe)) {
    Write-Error "Venv python not found at $PythonExe. Create it first: python -m venv .venv"
    exit 1
}

$Action = New-ScheduledTaskAction `
    -Execute $PythonExe `
    -Argument "-m job_scraper scrape" `
    -WorkingDirectory $RepoRoot

$Trigger = New-ScheduledTaskTrigger -Daily -At $StartTime

$Settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -DontStopOnIdleEnd `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30)

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Description "Runs job-scraper's scrape command daily to refresh the local job listings DB." `
    -Force

Write-Host "Registered scheduled task '$TaskName' to run daily at $StartTime."
Write-Host "View/manage it in Task Scheduler, or: Get-ScheduledTask -TaskName $TaskName"
