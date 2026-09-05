$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

. (Join-Path $PSScriptRoot "Common-BackupFunctions.ps1")

$projectRoot = Get-ProjectRoot
$settings = Get-BackupSettings -ProjectRoot $projectRoot

$secretFile = Resolve-ConfiguredPath `
    -ProjectRoot $projectRoot `
    -PathValue ([string]$settings.Encryption.SecretFile)

$secretDir = Split-Path $secretFile -Parent
New-Item -ItemType Directory -Force -Path $secretDir | Out-Null

Write-Host ""
Write-Host "Initialize Backup Encryption"
Write-Host "============================"
Write-Host ""
Write-Host "This passphrase encrypts 7-Zip backup archives."
Write-Host "Store a separate authorized offline copy of the passphrase."
Write-Host "The DPAPI secret file alone is NOT sufficient if this PC is destroyed."
Write-Host ""

$secure = Read-Host "Enter backup encryption passphrase" -AsSecureString
$confirm = Read-Host "Confirm backup encryption passphrase" -AsSecureString

function Convert-SecureStringToPlainText {
    param([Security.SecureString]$SecureString)

    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecureString)

    try {
        return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
    }
    finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
    }
}

$plain = Convert-SecureStringToPlainText $secure
$plainConfirm = Convert-SecureStringToPlainText $confirm

if ([string]::IsNullOrWhiteSpace($plain)) {
    throw "Passphrase cannot be empty."
}

if ($plain -ne $plainConfirm) {
    throw "Passphrases do not match."
}

Add-Type -AssemblyName System.Security

$plainBytes = [Text.Encoding]::UTF8.GetBytes($plain)

$protectedBytes = [System.Security.Cryptography.ProtectedData]::Protect(
    $plainBytes,
    $null,
    [System.Security.Cryptography.DataProtectionScope]::LocalMachine
)

[Convert]::ToBase64String($protectedBytes) |
    Set-Content -Path $secretFile -Encoding ASCII

try {
    $acl = Get-Acl $secretFile
    $acl.SetAccessRuleProtection($true, $false)

    foreach ($rule in @($acl.Access)) {
        $acl.RemoveAccessRule($rule) | Out-Null
    }

    $systemRule = New-Object System.Security.AccessControl.FileSystemAccessRule(
        "SYSTEM",
        "FullControl",
        "Allow"
    )

    $adminsRule = New-Object System.Security.AccessControl.FileSystemAccessRule(
        "BUILTIN\Administrators",
        "FullControl",
        "Allow"
    )

    $userRule = New-Object System.Security.AccessControl.FileSystemAccessRule(
        [System.Security.Principal.WindowsIdentity]::GetCurrent().Name,
        "FullControl",
        "Allow"
    )

    $acl.AddAccessRule($systemRule)
    $acl.AddAccessRule($adminsRule)
    $acl.AddAccessRule($userRule)
    Set-Acl -Path $secretFile -AclObject $acl
}
catch {
    Write-Warning (
        "Secret was created but ACL hardening could not be completed: " +
        $_.Exception.Message
    )
}

$plain = $null
$plainConfirm = $null

Write-Host ""
Write-Host "Backup encryption secret created:"
Write-Host $secretFile
Write-Host ""
Write-Host "Next:"
Write-Host "1. Install 7-Zip."
Write-Host "2. Copy backup-settings.example.json to backup-settings.local.json."
Write-Host "3. Set Encryption.Enabled to true."
Write-Host "4. Run Invoke-DatabaseBackup.ps1 once and verify success."
