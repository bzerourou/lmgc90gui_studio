# Install LMGC90 GUI Studio (core + engine + gui[qt])
# Run from the studio root:  .\install.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

Write-Host "==> reinstall lmgc90_core (editable, no cache)" -ForegroundColor Cyan
pip install --force-reinstall --no-deps -e "$Root\lmgc90_core"
pip install -e "$Root\lmgc90_core"

Write-Host "==> lmgc90_engine" -ForegroundColor Cyan
pip install -e "$Root\lmgc90_engine"

Write-Host "==> lmgc90_gui[qt]" -ForegroundColor Cyan
pip install -e "$Root\lmgc90_gui[qt]"

Write-Host "==> verify ForLoop export" -ForegroundColor Cyan
python -c "from lmgc90_core import ForLoop, Project; from lmgc90_engine import EngineSession; from lmgc90_gui import ProjectController; print('OK', ForLoop)"

Write-Host "Done. Launch with:  lmgc90-gui" -ForegroundColor Green
