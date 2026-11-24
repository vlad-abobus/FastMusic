param(
    [string]$Name = "FastMusic",
    [switch]$Windowed
)

$ErrorActionPreference = "Stop"

# --- ffmpeg download ---
$ffmpegPath = "ffmpeg.exe"
if (-not (Test-Path $ffmpegPath)) {
    Write-Host "Downloading ffmpeg..." -ForegroundColor Yellow
    $url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
    $zip = "$env:TEMP\ffmpeg.zip"
    try {
        Invoke-WebRequest -Uri $url -OutFile $zip -UseBasicParsing
        Expand-Archive -Path $zip -DestinationPath "$env:TEMP\ffmpeg-extract" -Force
        $exe = Get-ChildItem -Path "$env:TEMP\ffmpeg-extract" -Recurse -Filter "ffmpeg.exe" | Select-Object -First 1
        if ($exe) {
            Copy-Item -Path $exe.FullName -Destination $ffmpegPath -Force
            $size = (Get-Item $ffmpegPath).Length / 1MB -as [int]
            Write-Host "ffmpeg.exe downloaded ($size MB)" -ForegroundColor Green
        }
        Remove-Item -Recurse -Force "$env:TEMP\ffmpeg-extract" -ErrorAction SilentlyContinue
    } catch {
        Write-Warning "Failed to download ffmpeg: $_"
        Write-Warning "yt-dlp will only work if ffmpeg is installed on the system"
    }
    if (Test-Path $zip) { Remove-Item -Force $zip -ErrorAction SilentlyContinue }
}

# --- PyInstaller ---
$PyInstaller = ".venv\Scripts\pyinstaller.exe"
if (-not (Test-Path $PyInstaller)) {
    Write-Host "Installing PyInstaller..." -ForegroundColor Yellow
    .\.venv\Scripts\pip.exe install pyinstaller
}

$spec = "FastMusic.spec"
if (-not (Test-Path $spec)) {
    Write-Error "Spec file not found: $spec"
    exit 1
}

# clean old builds
foreach ($dir in "build", "dist") {
    if (Test-Path $dir) {
        Remove-Item -Recurse -Force $dir
    }
}

if ($Windowed) {
    Write-Host "Mode: no console (windowed)" -ForegroundColor Cyan
    (Get-Content $spec) -replace "console=True", "console=False" | Set-Content $spec
} else {
    Write-Host "Mode: with console" -ForegroundColor Cyan
    (Get-Content $spec) -replace "console=False", "console=True" | Set-Content $spec
}

Write-Host "Running PyInstaller..." -ForegroundColor Cyan
& $PyInstaller $spec --noconfirm

if ($LASTEXITCODE -eq 0) {
    $exePath = "dist\$Name.exe"
    if (Test-Path $exePath) {
        $size = (Get-Item $exePath).Length / 1MB -as [int]
        Write-Host "Done: $exePath ($size MB)" -ForegroundColor Green
    }
} else {
    Write-Error "PyInstaller failed (code $LASTEXITCODE)"
    exit $LASTEXITCODE
}
