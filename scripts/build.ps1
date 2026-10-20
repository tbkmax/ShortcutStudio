$ErrorActionPreference = 'Stop'

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
$spec = Join-Path $projectRoot 'Shortcut Studio.spec'
$output = Join-Path $projectRoot 'dist\Shortcut Studio.exe'

if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    throw "Python virtual environment not found: $python"
}
if (-not (Test-Path -LiteralPath $spec -PathType Leaf)) {
    throw "PyInstaller spec not found: $spec"
}

# Keep unrelated tools on the host PATH from supplying incompatible Qt dependencies.
$previousPath = $env:PATH
$windowsRoot = $env:SystemRoot
$env:PATH = @(
    (Join-Path $projectRoot '.venv\Scripts')
    (Join-Path $windowsRoot 'System32')
    $windowsRoot
) -join [IO.Path]::PathSeparator

Push-Location $projectRoot
try {
    & $python -m PyInstaller --noconfirm --clean --workpath '.pyinstaller-build' --distpath 'dist' $spec
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller failed with exit code $LASTEXITCODE"
    }
    if (-not (Test-Path -LiteralPath $output -PathType Leaf)) {
        throw "Build did not create $output"
    }

    & $python (Join-Path $PSScriptRoot 'verify_build.py') $output
    if ($LASTEXITCODE -ne 0) {
        throw "Archive verification failed with exit code $LASTEXITCODE"
    }
    Write-Output "Built $output"
}
finally {
    Pop-Location
    $env:PATH = $previousPath
}
