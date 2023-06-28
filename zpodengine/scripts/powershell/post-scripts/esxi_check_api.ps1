Param (
    [String]$zPodHostname = $(throw "-zPodHostname required"),
    [String]$zPodPassword = $(throw "-zPodPassword required")
)

$PSStyle.OutputRendering = 'PlainText'
$ProgressPreference = "SilentlyContinue"

# Load zPod Required Libraries
$LIB_DIR = "/zpodengine/scripts/powershell/lib"
. "$($LIB_DIR)/utils.ps1"

# Connect to host
Retry-Command -ScriptBlock { Connect-VIServer -Server $zPodHostname -User root -Password $zPodPassword }

# The initial connection / access of the API happens before the ESXi services are restarted.
# This makes VIM API calls fail.
# Powershell can't manage the session handle that it had before the connection and doesn't reconnect properly.
Write-Host "Sleeping 20s ..."
Start-Sleep -Seconds 20

# Disconnect from host
Retry-Command -ScriptBlock { Disconnect-VIServer -Server $zPodHostname -Force -Confirm:$false }

