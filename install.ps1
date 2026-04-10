$ErrorActionPreference = "Stop"

$Repo = "zhiqli1993/knowledge-base"
$InstallDir = if ($env:KB_INSTALL_DIR) { $env:KB_INSTALL_DIR } else { Join-Path $env:LOCALAPPDATA "Programs\kb\bin" }
$Arch = switch ($env:PROCESSOR_ARCHITECTURE) {
    "AMD64" { "x64" }
    default { throw "Unsupported Windows architecture: $env:PROCESSOR_ARCHITECTURE" }
}

$Asset = "kb-windows-$Arch.zip"
$Url = "https://github.com/$Repo/releases/latest/download/$Asset"
$TempDir = Join-Path ([System.IO.Path]::GetTempPath()) ("kb-install-" + [System.Guid]::NewGuid().ToString("N"))

New-Item -ItemType Directory -Force -Path $TempDir | Out-Null
try {
    New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
    $ArchivePath = Join-Path $TempDir $Asset
    Invoke-WebRequest -Uri $Url -OutFile $ArchivePath
    Expand-Archive -Path $ArchivePath -DestinationPath $TempDir -Force

    $BundleDir = Join-Path $TempDir "kb-windows-$Arch"
    foreach ($Binary in @("kb.exe", "kb-http.exe", "kb-mcp.exe")) {
        Copy-Item -Path (Join-Path $BundleDir $Binary) -Destination (Join-Path $InstallDir $Binary) -Force
    }

    $UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $PathEntries = @()
    if ($UserPath) {
        $PathEntries = $UserPath.Split(';', [System.StringSplitOptions]::RemoveEmptyEntries)
    }
    if ($PathEntries -notcontains $InstallDir) {
        $NewUserPath = if ($UserPath) { "$UserPath;$InstallDir" } else { $InstallDir }
        [Environment]::SetEnvironmentVariable("Path", $NewUserPath, "User")
        $env:Path = "$InstallDir;$env:Path"
        Write-Host "Added $InstallDir to your user PATH. Open a new terminal if commands are not found immediately."
    }
    else {
        Write-Host "$InstallDir is already present in your user PATH."
    }

    Write-Host "Installed kb, kb-http, and kb-mcp to $InstallDir"
    Write-Host "Prerequisites: install Git and Ollama, then run 'ollama pull nomic-embed-text'."
}
finally {
    if (Test-Path $TempDir) {
        Remove-Item -Path $TempDir -Recurse -Force
    }
}
