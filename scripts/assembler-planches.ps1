param([string]$Frames, [string]$Meta, [string]$OutDir, [string[]]$Familles = @("boucles", "entrees_sorties", "reactions", "couches"), [int]$Cell = 256)
# Assemble une planche PNG transparente par famille : une ligne par action, images 0 / milieu / fin.
Add-Type -AssemblyName System.Drawing
$info = Get-Content $Meta -Raw -Encoding UTF8 | ConvertFrom-Json
$labelW = 210
foreach ($fam in $Familles) {
    $names = @($info.PSObject.Properties | Where-Object { $_.Value.famille -eq $fam } | ForEach-Object { $_.Name })
    if ($names.Count -eq 0) { continue }
    $bmp = New-Object System.Drawing.Bitmap ($labelW + 3 * $Cell), (28 + $names.Count * $Cell)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.Clear([System.Drawing.Color]::Transparent)
    $g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAlias
    $font = New-Object System.Drawing.Font "Segoe UI", 12, ([System.Drawing.FontStyle]::Bold)
    $small = New-Object System.Drawing.Font "Segoe UI", 10
    $brush = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 34, 64, 95))
    $i = 0
    foreach ($t in "image 0", "milieu", "fin") { $g.DrawString($t, $small, $brush, ($labelW + $i * $Cell + 8), 6); $i++ }
    $row = 0
    foreach ($n in $names) {
        $y = 28 + $row * $Cell
        $g.DrawString($n, $font, $brush, 6, ($y + $Cell / 2 - 22))
        $g.DrawString(("{0} s" -f $info.$n.duree), $small, $brush, 6, ($y + $Cell / 2 + 2))
        for ($k = 0; $k -lt 3; $k++) {
            $p = Join-Path $Frames ("{0}_{1}.png" -f $n, $k)
            if (Test-Path $p) { $im = [System.Drawing.Image]::FromFile($p); $g.DrawImage($im, ($labelW + $k * $Cell), $y, $Cell, $Cell); $im.Dispose() }
        }
        $row++
    }
    $bmp.Save((Join-Path $OutDir ("planche-{0}.png" -f $fam)), [System.Drawing.Imaging.ImageFormat]::Png)
    $g.Dispose(); $bmp.Dispose()
}
