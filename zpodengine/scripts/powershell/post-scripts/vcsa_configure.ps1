Param (
  [String]$zPodHostname = $(throw "-zPodHostname required"),
  [String]$zPodUsername = $(throw "-zPodUsername required"),
  [String]$zPodPassword = $(throw "-zPodPassword required"),
  [String[]]$zPodESXiList = $(throw "-zPodESXiList required"),
  [Parameter(Mandatory=$false)]
  [String]$license_esxi,
  [Parameter(Mandatory=$false)]
  [String]$license_vcenter,
  [Parameter(Mandatory=$false)]
  [String]$license_vsan,
  [Parameter(Mandatory=$false)]
  [String]$license_tanzu
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


Write-Host "Add & Assign vSphere Licenses..."
$si = Get-View $global:DefaultVIServer

# Add licenses to vCenter
$licmgr = $licmgr = Get-View $si.Content.LicenseManager
$licmgrassign = Get-View $licmgr.LicenseAssignmentManager


if (-not [string]::IsNullOrEmpty($license_vcenter)) {
  $licmgr.AddLicense($license_vcenter, $null)
  $licmgrassign.UpdateAssignedLicense($global:DefaultVIServer.InstanceUuid, $license_vcenter, $null)
}

if (-not [string]::IsNullOrEmpty($license_esxi)) {
  $licmgr.AddLicense($license_esxi, $null)

  # Assign ESXi License
  foreach ($esxihost in Get-VMHost) {
    $esxiview = Get-View $esxihost
    $licmgrassign.UpdateAssignedLicense($esxiview.Config.Host.Value, $license_esxi, $null)
  }
}

if (-not [string]::IsNullOrEmpty($license_vsan)) {
  $licmgr.AddLicense($license_vsan, $null)
}

if (-not [string]::IsNullOrEmpty($license_tanzu)) {
  $licmgr.AddLicense($license_tanzu, $null)
}


# Disable ESXi autocustomization (William Lam templates) (this should not happen but it does ...)
Get-VMHost | Get-AdvancedSetting -Name UserVars.vGhettoSetup | Set-AdvancedSetting -Value 1 -Confirm:$false
Get-VMHost | Get-AdvancedSetting -Name UserVars.VMwareESXiGuestCustom | Set-AdvancedSetting -Value 1 -Confirm:$false

# Disable ESXi autocustomization (Timo Sugliani templates) (this should not happen but it does ...)
Get-VMHost | Get-AdvancedSetting -Name UserVars.NestedCustomizationSetup | Set-AdvancedSetting -Value 1 -Confirm:$false


Write-Host "Configuration Done !"