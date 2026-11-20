param([string]$Images, [string]$OutDir, [int]$Cell = 420, [int]$ParPlanche = 4)
# Assemble les planches de validation des saisons et fêtes : une ligne par thème (tenue, objet sorti, animation spéciale).
Add-Type -AssemblyName System.Drawing
$cat = Get-Content (Join-Path $Images "catalogue.json") -Raw -Encoding UTF8 | ConvertFrom-Json
$labelW = 250; $capH = 44
$fond = [System.Drawing.Color]::FromArgb(255, 251, 246, 241)
$marine = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 20, 45, 90))
$gris = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 95, 110, 130))
$fTitre = New-Object System.Drawing.Font "Segoe UI", 19, ([System.Drawing.FontStyle]::Bold)
$fCap = New-Object System.Drawing.Font "Segoe UI", 11.5, ([System.Drawing.FontStyle]::Bold)
$fPetit = New-Object System.Drawing.Font "Segoe UI", 10.5
$centre = New-Object System.Drawing.StringFormat; $centre.Alignment = [System.Drawing.StringAlignment]::Center
$themes = @($cat | Where-Object { Test-Path (Join-Path $Images ("{0}_0.png" -f $_.cle)) })
$groupes = @{ "fetes" = @($themes | Where-Object { $_.tenue.Count -gt 0 }); "saisons" = @($themes | Where-Object { $_.tenue.Count -eq 0 }) }
foreach ($g in "fetes", "saisons") {
    $liste = $groupes[$g]; $n = 0
    for ($i = 0; $i -lt $liste.Count; $i += $ParPlanche) {
        $n++; $lot = @($liste[$i..([math]::Min($i + $ParPlanche, $liste.Count) - 1)])
        $bmp = New-Object System.Drawing.Bitmap ($labelW + 3 * $Cell), ($lot.Count * ($Cell + $capH))
        $gr = [System.Drawing.Graphics]::FromImage($bmp); $gr.Clear($fond)
        $gr.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAlias
        $row = 0
        foreach ($t in $lot) {
            $y = $row * ($Cell + $capH)
            $gr.DrawString($t.titre, $fTitre, $marine, (New-Object System.Drawing.RectangleF 14, ($y + $Cell / 2 - 60), ($labelW - 20), 80))
            $gr.DrawString($t.periode, $fPetit, $gris, (New-Object System.Drawing.RectangleF 16, ($y + $Cell / 2 + 20), ($labelW - 20), 50))
            for ($k = 0; $k -lt 3; $k++) {
                $p = Join-Path $Images ("{0}_{1}.png" -f $t.cle, $k)
                if (Test-Path $p) { $im = [System.Drawing.Image]::FromFile($p); $gr.DrawImage($im, ($labelW + $k * $Cell), $y, $Cell, $Cell); $im.Dispose() }
                $gr.DrawString($t.legendes[$k], $fCap, $(if ($k -eq 0) { $gris } else { $marine }), (New-Object System.Drawing.RectangleF ($labelW + $k * $Cell), ($y + $Cell + 4), $Cell, $capH), $centre)
            }
            $row++
        }
        $nom = if ($groupes[$g].Count -le $ParPlanche) { "planche-$g.png" } else { "planche-$g-$n.png" }
        $bmp.Save((Join-Path $OutDir $nom), [System.Drawing.Imaging.ImageFormat]::Png)
        $gr.Dispose(); $bmp.Dispose()
    }
}
