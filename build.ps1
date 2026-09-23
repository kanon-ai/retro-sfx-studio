$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
cmake -S . -B native-build -A x64
if ($LASTEXITCODE -ne 0) { throw 'CMake configure failed' }
cmake --build native-build --config Release
if ($LASTEXITCODE -ne 0) { throw 'Native build failed' }
New-Item -ItemType Directory -Path bin -Force | Out-Null
Copy-Item -LiteralPath native-build\Release\retro_render.exe -Destination bin\retro_render.exe
python -m PyInstaller --noconfirm --clean --onedir --name RetroSFX --add-data 'static;static' --add-binary 'bin/retro_render.exe;bin' --add-data 'vendor/ymfm/LICENSE;licenses' --add-data 'licenses;licenses' launcher.py
if ($LASTEXITCODE -ne 0) { throw 'Packaging failed' }
Copy-Item -LiteralPath README.md,MCP_SETUP.md,THIRD_PARTY.md,DISCLAIMER.md,LICENSE -Destination dist\RetroSFX
