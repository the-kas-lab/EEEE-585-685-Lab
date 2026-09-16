<#
.SYNOPSIS
    Keeps the SSC-32(U) USB-serial adapter attached to WSL2, so the lab2
    container sees /dev/ttyUSB0 without a rebuild.

.DESCRIPTION
    Docker Desktop runs containers inside the WSL2 VM, which has no USB stack
    of its own: a device plugged into Windows is invisible there until
    usbipd-win forwards it. This script watches for the arm's USB-serial
    adapter and attaches it the moment it appears -- on first plug, after a
    replug, after a different port is used, and after `wsl --shutdown` or a
    reboot drops the attachment.

    All WSL2 distros share one kernel and one /dev, so an attach made here is
    visible to Docker Desktop's `docker-desktop` distro and therefore inside
    the container, live. The container does NOT need to be restarted.

    Run it once with -Setup (as Administrator) per machine, then run it
    without arguments whenever you are working on the lab.

.PARAMETER Setup
    One-time, requires Administrator. Registers an AutoBind policy for each
    hardware ID so that later attaches need no elevation.

.PARAMETER HardwareId
    VID:PID pairs to watch for. The defaults cover the USB-serial chips these
    adapters ship with: FTDI FT232R/FT231X/FT2232 (the SSC-32U's own),
    Silicon Labs CP210x, WCH CH340/CH341, Prolific PL2303.

.PARAMETER Once
    Attach whatever is plugged in right now, then exit instead of watching.

.PARAMETER IntervalSeconds
    Seconds between polls while watching. Default 2.

.EXAMPLE
    # One time per machine, in an elevated PowerShell:
    .\attach-arm.ps1 -Setup

.EXAMPLE
    # Every lab session, in a normal (non-elevated) PowerShell:
    .\attach-arm.ps1
#>
[CmdletBinding()]
param(
    [switch] $Setup,
    [switch] $Once,
    [int]    $IntervalSeconds = 2,
    [string[]] $HardwareId = @(
        '0403:6001',  # FTDI FT232R -- the SSC-32U's own, and most serial cables
        '0403:6015',  # FTDI FT231X
        '0403:6010',  # FTDI FT2232
        '10c4:ea60',  # Silicon Labs CP2102/CP2109
        '1a86:7523',  # WCH CH340
        '1a86:5523',  # WCH CH341
        '067b:2303'   # Prolific PL2303
    )
)

$ErrorActionPreference = 'Stop'

# usbipd writes its progress lines ("info: Using WSL distribution ...") to
# stderr even on success. Windows PowerShell 5.1 wraps a native command's
# stderr in ErrorRecords, which under `$ErrorActionPreference = 'Stop'` aborts
# the script on a perfectly successful attach. Redirecting stderr to a file
# consumes those records instead, so the exit code stays the only verdict.
function Invoke-Usbipd {
    param([Parameter(ValueFromRemainingArguments = $true)] [string[]] $Arguments)

    # Local to this function: the redirect below parks those ErrorRecords in a
    # file, but the preference still decides whether they terminate first.
    $ErrorActionPreference = 'Continue'

    $errFile = [System.IO.Path]::GetTempFileName()
    try {
        $stdout = (& usbipd @Arguments 2>$errFile | Out-String)
        $code = $LASTEXITCODE
        $stderr = (Get-Content -LiteralPath $errFile -Raw -ErrorAction SilentlyContinue)
        return [pscustomobject]@{
            ExitCode = $code
            Output   = (($stdout + "`n" + $stderr)).Trim()
        }
    } finally {
        Remove-Item -LiteralPath $errFile -Force -ErrorAction SilentlyContinue
    }
}

function Test-Admin {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($id)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Assert-Usbipd {
    if ($null -eq (Get-Command usbipd -ErrorAction SilentlyContinue)) {
        Write-Host 'usbipd-win is not installed.' -ForegroundColor Red
        Write-Host '  Install it, then open a NEW PowerShell window:'
        Write-Host '    winget install usbipd' -ForegroundColor Yellow
        Write-Host '  Then restart WSL so its driver loads:'
        Write-Host '    wsl --shutdown' -ForegroundColor Yellow
        exit 1
    }
}

# usbipd reports each device's InstanceId like USB\VID_0403&PID_6001\A5XK3RJT.
# Pull the VID:PID back out so we match the chip rather than the physical port
# -- students move the cable between ports, and the BUSID moves with it.
function Get-UsbipdDevices {
    $raw = (Invoke-Usbipd state).Output
    if ([string]::IsNullOrWhiteSpace($raw)) { return @() }

    $out = @()
    foreach ($d in ($raw | ConvertFrom-Json).Devices) {
        $m = [regex]::Match($d.InstanceId, 'VID_([0-9A-Fa-f]{4})&PID_([0-9A-Fa-f]{4})')
        if (-not $m.Success) { continue }
        $out += [pscustomobject]@{
            BusId       = $d.BusId
            HardwareId  = ($m.Groups[1].Value + ':' + $m.Groups[2].Value).ToLower()
            Description = $d.Description
            # ClientIPAddress is non-null exactly when the device is attached to
            # a client -- that is how `usbipd list` decides to print "Attached".
            Attached    = ($null -ne $d.ClientIPAddress)
        }
    }
    return $out
}

function Invoke-Setup {
    if (-not (Test-Admin)) {
        Write-Host '-Setup needs Administrator.' -ForegroundColor Red
        Write-Host '  Right-click PowerShell -> Run as Administrator, then rerun:'
        Write-Host '    .\attach-arm.ps1 -Setup' -ForegroundColor Yellow
        exit 1
    }

    $existing = (Invoke-Usbipd policy list).Output

    foreach ($hw in $HardwareId) {
        if ($existing -match [regex]::Escape($hw)) {
            Write-Host "  already allowed: $hw" -ForegroundColor DarkGray
            continue
        }
        $r = Invoke-Usbipd policy add --effect Allow --operation AutoBind --hardware-id $hw
        if ($r.ExitCode -eq 0) {
            Write-Host "  AutoBind allowed: $hw" -ForegroundColor Green
        } else {
            Write-Host "  could not add a policy for ${hw}: $($r.Output)" -ForegroundColor Yellow
        }
    }

    Write-Host ''
    Write-Host 'Setup done. From now on run this script WITHOUT -Setup and' -ForegroundColor Green
    Write-Host 'without Administrator:' -ForegroundColor Green
    Write-Host '    .\attach-arm.ps1' -ForegroundColor Yellow
}

# usbipd needs a running WSL distro to attach into. Docker Desktop normally
# keeps `docker-desktop` up, but start something if nothing is running.
function Start-WslIfStopped {
    $running = (& wsl.exe -l --running -q 2>$null) -join ''
    if ([string]::IsNullOrWhiteSpace($running)) {
        Write-Host 'No WSL distro running -- starting one...' -ForegroundColor DarkGray
        & wsl.exe -- true 2>$null | Out-Null
    }
}

function Invoke-Watch {
    Start-WslIfStopped

    Write-Host "Watching for the arm's USB-serial adapter." -ForegroundColor Cyan
    Write-Host "Hardware IDs: $($HardwareId -join ', ')" -ForegroundColor DarkGray
    Write-Host 'Plug the SSC-32(U) in at any time. Press Ctrl+C to stop.' -ForegroundColor DarkGray
    Write-Host ''

    # Only print when the picture changes, so an idle watcher stays quiet.
    $announced = @{}

    while ($true) {
        $matched = @(Get-UsbipdDevices | Where-Object { $HardwareId -contains $_.HardwareId })
        $stamp = Get-Date -Format 'HH:mm:ss'

        if ($matched.Count -eq 0) {
            if (-not $announced.ContainsKey('none')) {
                Write-Host "$stamp  waiting -- no adapter plugged in" -ForegroundColor DarkGray
                $announced = @{ none = $true }
            }
        }

        foreach ($dev in $matched) {
            $key = "$($dev.BusId)/$($dev.HardwareId)"

            if ($dev.Attached) {
                if (-not $announced.ContainsKey($key)) {
                    Write-Host "$stamp  attached  $($dev.HardwareId) on $($dev.BusId) -- $($dev.Description)" -ForegroundColor Green
                    Write-Host '           verify inside WSL:  wsl ls -l /dev/ttyUSB*' -ForegroundColor DarkGray
                    $announced = @{ $key = $true }
                }
                continue
            }

            Write-Host "$stamp  found $($dev.HardwareId) on $($dev.BusId), attaching..." -ForegroundColor Cyan
            $announced = @{}

            Start-WslIfStopped
            $r = Invoke-Usbipd attach --wsl --busid $dev.BusId

            if ($r.ExitCode -ne 0) {
                Write-Host $r.Output -ForegroundColor Yellow
                if ($r.Output -match 'not shared|administrator|policy|bind') {
                    Write-Host "  That device is not shared yet. Run the one-time setup once," -ForegroundColor Yellow
                    Write-Host "  in an elevated PowerShell:  .\attach-arm.ps1 -Setup" -ForegroundColor Yellow
                }
            }
        }

        if ($Once) { break }
        Start-Sleep -Seconds $IntervalSeconds
    }
}

Assert-Usbipd

if ($Setup) {
    Invoke-Setup
} else {
    Invoke-Watch
}
