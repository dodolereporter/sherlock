param([string]$Frames, [string]$Catalogue, [string]$Out, [int]$W = 720, [int]$H = 720)
# Prépare les images de la vidéo de contrôle des saisons et fêtes : chaque image d'animation est posée sur un fond clair
# avec le nom du thème et de l'animation. Les images numérotées sont écrites dans $Out (v_00001.jpg, ...).
Add-Type -AssemblyName System.Drawing
New-Item -ItemType Directory -Force $Out | Out-Null
$cat = Get-Content $Catalogue -Raw -Encoding UTF8 | ConvertFrom-Json
$fond = [System.Drawing.Color]::FromArgb(255, 251, 246, 241)
$marine = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 20, 45, 90))
$gris = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 95, 110, 130))
$fTitre = New-Object System.Drawing.Font "Segoe UI", 26, ([System.Drawing.FontStyle]::Bold)
$fCap = New-Object System.Drawing.Font "Segoe UI", 17, ([System.Drawing.FontStyle]::Bold)
$fPetit = New-Object System.Drawing.Font "Segoe UI", 13
$centre = New-Object System.Drawing.StringFormat; $centre.Alignment = [System.Drawing.StringAlignment]::Center
$enc = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object { $_.MimeType -eq "image/jpeg" }
$ep = New-Object System.Drawing.Imaging.EncoderParameters 1
$ep.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter ([System.Drawing.Imaging.Encoder]::Quality, [long]92)
$ordre = @($cat | Where-Object { $_.tenue.Count -eq 0 }) + @($cat | Where-Object { $_.tenue.Count -gt 0 })
$n = 0
foreach ($t in $ordre) {
    foreach ($clip in @(@("a", 1, "L'objet qu'il sort"), @("b", 2, "L'animation spéciale"))) {
        $files = @(Get-ChildItem $Frames -Filter ("{0}_{1}_*.png" -f $t.cle, $clip[0]) | Sort-Object Name)
        if ($files.Count -eq 0) { continue }
        $liste = @($files) + @($files[-1]) * 10                    # courte pause à la fin de chaque animation
        foreach ($f in $liste) {
            $bmp = New-Object System.Drawing.Bitmap $W, $H
            $g = [System.Drawing.Graphics]::FromImage($bmp); $g.Clear($fond)
            $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
            $g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAlias
            $im = [System.Drawing.Image]::FromFile($f.FullName); $g.DrawImage($im, (($W - 600) / 2), 70, 600, 600); $im.Dispose()
            $g.DrawString($t.titre, $fTitre, $marine, (New-Object System.Drawing.RectangleF 0, 14, $W, 50), $centre)
            $g.DrawString($t.legendes[$clip[1]], $fCap, $marine, (New-Object System.Drawing.RectangleF 0, ($H - 62), $W, 34), $centre)
            $g.DrawString($clip[2], $fPetit, $gris, (New-Object System.Drawing.RectangleF 0, ($H - 30), $W, 26), $centre)
            $n++
            $bmp.Save((Join-Path $Out ("v_{0:00000}.jpg" -f $n)), $enc, $ep)
            $g.Dispose(); $bmp.Dispose()
        }
    }
}
"$n images"
