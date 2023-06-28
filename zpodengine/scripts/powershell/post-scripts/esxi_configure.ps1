Param (
    [String]$zPodHostname = $(throw "-zPodHostname required"),
    [string]$zBoxHostname = $(throw "-zBoxHostname required"),
    [string]$zPodFactory = $(throw "-zPodFactory required"),
    [String]$zPodPassword = $(throw "-zPodPassword required")
)

$PSStyle.OutputRendering = 'PlainText'
$ProgressPreference = "SilentlyContinue"

# Load zPod Required Libraries
$LIB_DIR = "/zpodengine/scripts/powershell/lib"
. "$($LIB_DIR)/utils.ps1"

# Connect to host
Retry-Command -ScriptBlock { Connect-VIServer -Server $zPodHostname -User root -Password $zPodPassword }

# NFS
Retry-Command -ScriptBlock { Get-VMHost | New-Datastore -NFS -Name "NFS-01" -Path "/FILER/STORAGE01/NFS-01" -NfsHost $zBoxHostname }

# Set to Connected (not maintenance mode)
Retry-Command -ScriptBlock { Get-VMHost | Set-VMHost -State "Connected" | Out-Null }

# Disconnect from host
Retry-Command -ScriptBlock { Disconnect-VIServer -Server * -Force -Confirm:$false }
