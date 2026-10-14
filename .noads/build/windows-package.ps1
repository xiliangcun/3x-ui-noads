$ErrorActionPreference="Stop"
Compress-Archive -Path .\x-ui -DestinationPath "x-ui-windows-amd64.zip"
$hash = (Get-FileHash x-ui-windows-amd64.zip -Algorithm SHA256).Hash.ToLower()
[IO.File]::WriteAllText("$PWD\x-ui-windows-amd64.zip.sha256", "$hash  x-ui-windows-amd64.zip`n")
