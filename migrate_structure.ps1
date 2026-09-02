# Migration script: move DDD structure to Clean Architecture layout.
$ErrorActionPreference = "Stop"

# Ensure clean state
if (Test-Path "src/backend") { throw "src/backend still exists" }

function Ensure-Dir($path) {
    if (-not (Test-Path $path)) { New-Item -ItemType Directory -Path $path | Out-Null }
}

function Move-File($src, $dst) {
    $dir = Split-Path $dst -Parent
    Ensure-Dir $dir
    if (Test-Path $src) { git mv $src $dst } else { Write-Host "MISSING: $src" }
}

# --- New package roots ---
foreach ($d in @(
    "src/domain",
    "src/application/dto", "src/application/exceptions", "src/application/interfaces",
    "src/application/services", "src/application/use_cases",
    "src/config",
    "src/infrastructures/database", "src/infrastructures/di_containers", "src/infrastructures/external",
    "src/infrastructures/cache", "src/infrastructures/files", "src/infrastructures/models",
    "src/infrastructures/observability", "src/infrastructures/repositories",
    "src/infrastructures/security", "src/infrastructures/web",
    "src/presentation/http/api", "src/presentation/http/middleware",
    "src/tests"
)) { Ensure-Dir $d }

# Copy-move helpers for __init__.py creation
function Write-Init($path) {
    Set-Content -Path $path -Value "" -Encoding utf8
}