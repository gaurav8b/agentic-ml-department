$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$PartsDirectory = Join-Path $Root ".source/parts"
$Archive = Join-Path $Root ".source/agentic-ml-department-source.tar.xz"

$Parts = Get-ChildItem -Path $PartsDirectory -Filter "*.b64" | Sort-Object Name
if ($Parts.Count -ne 14) {
  throw "Expected 14 numbered archive parts under .source/parts; found $($Parts.Count)."
}

$Base64 = ($Parts | ForEach-Object { (Get-Content -Path $_.FullName -Raw).Trim() }) -join ""
$Bytes = [Convert]::FromBase64String($Base64)
[IO.File]::WriteAllBytes($Archive, $Bytes)

Push-Location $Root
try {
  $Expected = ((Get-Content -Path "CHECKSUMS.txt" | Select-Object -First 1) -split '\s+')[0].ToLowerInvariant()
  $Actual = (Get-FileHash -Algorithm SHA256 -Path $Archive).Hash.ToLowerInvariant()
  if ($Actual -ne $Expected) {
    throw "Archive checksum mismatch. Expected $Expected; got $Actual."
  }
  tar -xJf $Archive -C $Root
  Write-Host "Source extracted to: $(Join-Path $Root 'agentic-ml-department')"
  Write-Host "Next: Set-Location agentic-ml-department; Copy-Item .env.example .env; docker compose up --build -d"
}
finally {
  Pop-Location
}
