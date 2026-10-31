$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Archive = Join-Path $Root ".source/agentic-ml-department-source.tar.xz"

if (-not (Test-Path $Archive)) {
  throw "Missing source archive: $Archive"
}

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
