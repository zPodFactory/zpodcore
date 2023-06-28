Param (
    [String]$zPodHostname = $(throw "-zPodHostname required"),
    [String]$zPodUsername = $(throw "-zPodUsername required"),
    [String]$zPodPassword = $(throw "-zPodPassword required"),
    [String[]]$zPodESXiList = $(throw "-zPodESXiList required")
)

$PSStyle.OutputRendering = 'PlainText'
$ProgressPreference = "SilentlyContinue"

$retry = 30

while (1) {
  $vi = Connect-VIServer -Server $zPodHostname -User $zPodUsername -Password $zPodPassword -ErrorAction SilentlyContinue
  if ($vi -or $retry -lt 1) {
    break
  }

  Write-Host "Waiting for vcsa to be accessible. Sleeping 10s... - [Remaining retries: $($retry)]"
  Start-Sleep -Seconds 10
  $retry--
}

# Fetch the only vCenter Folder
$folder = Get-Folder

# Create a new Datacenter
Write-Host "Create Datacenter..."
New-Datacenter -Name "Datacenter" -Location $folder

# Create a new Cluster
Write-Host "Create Cluster without EVC and FullyAutomated DRS..."
New-Cluster -Name "Cluster" -Location "Datacenter" -DRSEnabled -DRSAutomationLevel "FullyAutomated" -HAEnabled

Write-Host "Set Advanced Settings..."
# Setup some adv variables to avoid warning messages with a single NFS Datastore
New-AdvancedSetting -Entity "Cluster" -type ClusterHA -Name "das.ignoreRedundantNetWarning" -Value "true" -force -Confirm:$false
New-AdvancedSetting -Entity "Cluster" -type ClusterHA -Name "das.ignoreInsufficientHbDatastore" -Value "true" -force -Confirm:$false

Write-Host "Add Hosts to Cluster..."
# Loop through ESXi list and add them to Cluster
foreach ($esxi in $zPodESXiList) {
    Add-VMHost -Name $esxi -Location "Cluster" -User root -Password $zPodPassword -Force
}

Write-Host "Set vmk0 as vMotion enabled interface..."
# Reconfigure vmk0 for vMotion & HA
Get-Cluster "Cluster" | Get-VMHost | Get-VMHostNetworkAdapter -Name "vmk0" |  Set-VMHostNetworkAdapter -VMotionEnabled $true -Confirm:$false
Write-Host "Reconfigure Hosts for HA"
Get-Cluster "Cluster" | Get-VMhost | %{ $_.ExtensionData.ReconfigureHostForDAS() }

# Disable Coredump warnings
Get-VMHost | Get-AdvancedSetting -Name UserVars.SuppressCoredumpWarning | Set-AdvancedSetting -Value 1 -Confirm:$false

# Set VMware vSphere Licenses
# in zPod 2.0 this will be based on the zcli setting f"license_{component_uid}" key/values

# $vcsaLicense = $env:LICENSE_VCSA
# $esxiLicense = $env:LICENSE_ESXI
# $vsanLicense = $env:LICENSE_VSAN

# Write-Host "Add & Assign vSphere Licenses..."
# $si = Get-View $global:DefaultVIServer

# Add licenses to vCenter
# $licmgr = get-view $si.Content.LicenseManager
# $licmgr.AddLicense($vcsaLicense, $null)
# $licmgr.AddLicense($esxiLicense, $null)
# $licmgr.AddLicense($vsanLicense, $null)

# Assign vCenter License
# $licmgrassign = Get-View $licmgr.LicenseAssignmentManager
# $licmgrassign.UpdateAssignedLicense($global:DefaultVIServer.InstanceUuid, $vcsaLicense, $null)

# Assign ESXi License
# foreach ($esxihost in get-vmhost) {
#     $esxiview = Get-View $esxihost
#     $licmgrassign.UpdateAssignedLicense($esxiview.Config.Host.Value, $esxiLicense, $null)
# }

# Disable ESXi autocustomization (William Lam templates) (this should not happen but it does ...)
Get-VMHost | Get-AdvancedSetting -Name UserVars.vGhettoSetup | Set-AdvancedSetting -Value 1 -Confirm:$false
Get-VMHost | Get-AdvancedSetting -Name UserVars.VMwareESXiGuestCustom | Set-AdvancedSetting -Value 1 -Confirm:$false

# Disable ESXi autocustomization (Timo Sugliani templates) (this should not happen but it does ...)
Get-VMHost | Get-AdvancedSetting -Name UserVars.NestedCustomizationSetup | Set-AdvancedSetting -Value 1 -Confirm:$false


Write-Host "Configuration Done !"