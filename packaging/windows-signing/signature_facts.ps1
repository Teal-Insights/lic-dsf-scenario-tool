# Read-only Windows protocol. No signing, execution-policy changes or secret use.
param([Parameter(Mandatory=$true)][string]$LiteralTarget)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
try {
    Add-Type -AssemblyName System.Security
    $raw = [System.IO.File]::ReadAllBytes($LiteralTarget)
    if ($raw.Length -lt 512 -or $raw[0] -ne 77 -or $raw[1] -ne 90) { throw 'invalid' }
    $pe = [BitConverter]::ToUInt32($raw, 60)
    if ($pe + 264 -gt $raw.Length -or [BitConverter]::ToUInt32($raw, $pe) -ne 17744) { throw 'invalid' }
    if ([BitConverter]::ToUInt16($raw, $pe + 4) -ne 34404 -or [BitConverter]::ToUInt16($raw, $pe + 24) -ne 523) { throw 'invalid' }
    $offset = [BitConverter]::ToUInt32($raw, $pe + 24 + 112 + 32)
    $size = [BitConverter]::ToUInt32($raw, $pe + 24 + 112 + 36)
    if ($offset -eq 0 -or $size -lt 8 -or $offset % 8 -ne 0 -or $offset + $size -gt $raw.Length) { throw 'invalid' }
    $length = [BitConverter]::ToUInt32($raw, $offset)
    if ($length -lt 9 -or $length -gt $size -or (($length + 7) -band -8) -ne $size) { throw 'ambiguous' }
    if ([BitConverter]::ToUInt16($raw, $offset + 4) -ne 512 -or [BitConverter]::ToUInt16($raw, $offset + 6) -ne 2) { throw 'invalid' }
    $cmsBytes = New-Object byte[] ($length - 8)
    [Array]::Copy($raw, $offset + 8, $cmsBytes, 0, $cmsBytes.Length)
    $cms = New-Object System.Security.Cryptography.Pkcs.SignedCms
    $cms.Decode($cmsBytes)
    if ($cms.SignerInfos.Count -ne 1) { throw 'ambiguous' }
    $nested = @($cms.SignerInfos[0].UnsignedAttributes | Where-Object { $_.Oid.Value -eq '1.3.6.1.4.1.311.2.4.1' }).Count
    if ($nested -ne 0) { throw 'ambiguous' }
    $signature = Get-AuthenticodeSignature -LiteralPath $LiteralTarget
    if ($null -eq $signature.SignerCertificate -or $null -eq $cms.SignerInfos[0].Certificate) { throw 'invalid' }
    if ($signature.SignerCertificate.Thumbprint -cne $cms.SignerInfos[0].Certificate.Thumbprint) { throw 'ambiguous' }
    $eku = @($signature.SignerCertificate.EnhancedKeyUsageList | Where-Object { $_.ObjectId -eq '1.3.6.1.5.5.7.3.3' }).Count -gt 0
    [ordered]@{
        status = $signature.Status.ToString()
        signature_type = $signature.SignatureType.ToString()
        subject = $signature.SignerCertificate.Subject
        issuer = $signature.SignerCertificate.Issuer
        thumbprint = $signature.SignerCertificate.Thumbprint
        code_signing_eku = [bool]$eku
        timestamp_present = ($null -ne $signature.TimeStamperCertificate)
        embedded_signature_count = 1
        primary_signer_count = $cms.SignerInfos.Count
        nested_signature_count = $nested
    } | ConvertTo-Json -Compress
    exit 0
} catch {
    [Console]::Error.WriteLine('SIGNATURE_FACTS_UNAVAILABLE')
    exit 1
}
