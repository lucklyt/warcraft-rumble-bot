$rootPath = $PSScriptRoot
$appName = "warcraft_rumble_bot"
Write-Host ("root path is " + $rootPath)
$distPath = Join-Path  $rootPath "dist"
$mainPath = Join-Path  $rootPath "app_cfg_ui.py"
$staticPath = Join-Path  $rootPath "static"
$iconPath = Join-Path  $staticPath "rumble.ico"
if ($IsMacOS) {
    $distAppPath = Join-Path  $distPath ($appName + ".app")
    $exePath = Join-Path  $distAppPath "Contents/MacOS"
    Write-Host ("current system is MacOS, output app directory is " +$exePath)
}else{
    $exePath = Join-Path  $distPath $appName
    Write-Host ("current system is Windows, output app directory is " +$exePath)
}
$distConfDir = Join-Path  $exePath "conf"
$distConfFile = Join-Path  $distConfDir "app.yaml"


Remove-Item -Path  $distPath -Recurse -Force
python setup.py build_ext --inplace
pyinstaller --noconfirm --onedir --windowed --icon $iconPath  --name $appName  --log-level "INFO" --collect-data "cnocr" --collect-data "nicegui" $mainPath
Copy-Item -Path $staticPath -Destination $exePath -Recurse
New-Item -Path $exePath -Name "conf" -ItemType "directory"
Copy-Item  (Join-Path $rootPath "conf/app.yaml") -Destination $distConfDir
$fileContent = Get-Content -Encoding UTF8 -Path $distConfFile
$fileContent = $fileContent -replace "receiver: .*", "receiver: "
$fileContent = $fileContent -replace "level: .*", "level: INFO"
$fileContent = $fileContent -replace "path: .*", "path: "
$fileContent = $fileContent -replace "code: .*", "code: "
$fileContent = $fileContent -replace "capture_file_name: .*", "capture_file_name: screen"
$fileContent = $fileContent -replace "refresh_task: .*", "refresh_task: false"
$fileContent | Set-Content -Encoding UTF8 -Path $distConfFile
Remove-Item -Path (Join-Path $rootPath "conf"), (Join-Path $rootPath "emulator"), (Join-Path $rootPath "mail"), `
 (Join-Path $rootPath "process_control"), (Join-Path $rootPath "detect") `
-Include *.c, *.pyd, *.so -Recurse
if ($IsMacOS) {
    Remove-Item -Path  (Join-Path $distPath $appName) -Recurse -Force
    create-dmg --overwrite $distAppPath
}