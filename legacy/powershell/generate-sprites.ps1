Add-Type -AssemblyName System.Drawing

# Los sprites se generan siempre dentro de la carpeta "sprites" junto a este
# script, sea donde sea que se haya descargado el proyecto.
$root = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
$dir = Join-Path $root 'sprites'
New-Item -ItemType Directory -Path $dir -Force | Out-Null

# Paleta oficial de OpenCode (tema oscuro, escala de grises).
$bg     = [System.Drawing.Color]::FromArgb(12, 12, 12)    # 0C0C0C fondo
$panel  = [System.Drawing.Color]::FromArgb(22, 22, 22)    # 161616 panel
$subtle = [System.Drawing.Color]::FromArgb(26, 26, 26)    # 1A1A1A relleno
$shade  = [System.Drawing.Color]::FromArgb(75, 75, 75)    # 4B4B4B sombra
$muted  = [System.Drawing.Color]::FromArgb(174, 174, 174) # AEAEAE texto
$ink    = [System.Drawing.Color]::FromArgb(238, 238, 238) # EEEEEE trazo
$bright = [System.Drawing.Color]::FromArgb(250, 250, 250) # FAFAFA enfasis
$blue   = [System.Drawing.Color]::FromArgb(107, 143, 255) # 6B8FFF unico acento

function Rect($g, $c, [int]$x, [int]$y, [int]$w, [int]$h) {
    $b = New-Object System.Drawing.SolidBrush($c)
    $g.FillRectangle($b, $x, $y, $w, $h)
    $b.Dispose()
}
function HLine($g, $c, [int]$x, [int]$y, [int]$len) { Rect $g $c $x $y $len 2 }
function VLine($g, $c, [int]$x, [int]$y, [int]$len) { Rect $g $c $x $y 2 $len }

function Draw-Bitty {
    param([string]$Name)

    # 64x64 reales, todos los bloques de 2px: ningun escalado posterior.
    $bmp = New-Object System.Drawing.Bitmap(64, 64, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::None
    $g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::Default
    $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::NearestNeighbor
    $g.Clear($bg)

    # Terminal: marco claro (mismo trazo de 4px del logo) + interior oscuro.
    Rect $g $ink 8 8 48 4
    Rect $g $ink 8 52 48 4
    Rect $g $ink 8 8 4 48
    Rect $g $ink 52 8 4 48
    Rect $g $panel 12 12 40 40

    # Bloque interior del logo, en la parte baja.
    Rect $g $shade 20 44 24 8

    # Antena / cursor parpadeante arriba.
    Rect $g $ink 30 2 4 6

    switch ($Name) {
        'neutral' {
            Rect $g $bright 20 22 8 10; Rect $g $bright 36 22 8 10
            Rect $g $panel 22 28 2 2;   Rect $g $panel 38 28 2 2
            Rect $g $blue 28 40 8 2
        }
        'blink' {
            HLine $g $bright 20 26 8; HLine $g $bright 36 26 8
            Rect $g $blue 28 40 8 2
        }
        'celebrate' {
            # ojos ^ ^
            HLine $g $bright 20 25 4; VLine $g $bright 20 21 4
            HLine $g $bright 38 25 4; VLine $g $bright 42 21 4
            Rect $g $bright 26 38 12 6; Rect $g $panel 28 40 8 2
            Rect $g $bright 12 18 4 4; Rect $g $bright 48 18 4 4
        }
        'surprise' {
            Rect $g $bright 20 20 8 14; Rect $g $bright 36 20 8 14
            Rect $g $panel 22 26 2 2;   Rect $g $panel 38 26 2 2
            Rect $g $bright 28 38 8 8
        }
        'thinking' {
            Rect $g $bright 20 22 8 10
            HLine $g $bright 36 26 8
            Rect $g $panel 22 28 2 2
            Rect $g $muted 24 40 4 2; Rect $g $muted 30 38 4 2; Rect $g $muted 36 40 4 2
            Rect $g $blue 48 16 4 4
        }
        'doubt' {
            HLine $g $muted 20 18 8
            Rect $g $bright 20 22 8 10; Rect $g $bright 36 22 8 10
            Rect $g $panel 22 28 2 2;   Rect $g $panel 38 28 2 2
            Rect $g $muted 30 42 8 2
        }
        'error' {
            HLine $g $bright 20 24 8; VLine $g $bright 23 22 2
            HLine $g $bright 36 24 8; VLine $g $bright 39 22 2
            HLine $g $bright 20 30 8; HLine $g $bright 36 30 8
            Rect $g $bright 28 40 8 2
            Rect $g $bright 46 14 4 6; Rect $g $bright 46 22 4 2
        }
        'happy' {
            Rect $g $bright 20 22 8 10; Rect $g $bright 36 22 8 10
            Rect $g $panel 22 28 2 2;   Rect $g $panel 38 28 2 2
            HLine $g $bright 26 42 12
            VLine $g $bright 26 38 4; VLine $g $bright 36 38 4
        }
        'laugh' {
            HLine $g $bright 20 25 4; VLine $g $bright 20 21 4
            HLine $g $bright 38 25 4; VLine $g $bright 42 21 4
            Rect $g $bright 24 36 16 10; Rect $g $panel 26 38 12 6
            Rect $g $blue 16 24 4 4; Rect $g $blue 44 24 4 4
        }
        'sad' {
            Rect $g $muted 20 20 4 2; Rect $g $muted 24 18 4 2
            Rect $g $muted 36 18 4 2; Rect $g $muted 40 20 4 2
            Rect $g $bright 20 24 8 8; Rect $g $bright 36 24 8 8
            Rect $g $panel 22 28 2 2; Rect $g $panel 38 28 2 2
            HLine $g $bright 26 38 12
            VLine $g $bright 26 38 4; VLine $g $bright 36 38 4
            Rect $g $blue 44 30 4 6
        }
        'angry' {
            Rect $g $muted 20 18 4 2; Rect $g $muted 24 20 4 2
            Rect $g $muted 36 20 4 2; Rect $g $muted 40 18 4 2
            Rect $g $bright 30 20 4 2
            HLine $g $bright 20 25 8; HLine $g $bright 36 25 8
            HLine $g $bright 26 42 8
        }
        'love' {
            Rect $g $bright 18 22 4 2; Rect $g $bright 24 22 4 2
            Rect $g $bright 18 24 10 4; Rect $g $bright 20 28 6 2
            Rect $g $bright 22 30 2 2
            Rect $g $bright 36 22 4 2; Rect $g $bright 42 22 4 2
            Rect $g $bright 36 24 10 4; Rect $g $bright 38 28 6 2
            Rect $g $bright 40 30 2 2
            HLine $g $bright 26 42 12
            VLine $g $bright 26 38 4; VLine $g $bright 36 38 4
        }
        'wink' {
            Rect $g $bright 20 22 8 10
            Rect $g $panel 22 28 2 2
            HLine $g $bright 36 26 8
            HLine $g $bright 26 42 12
            VLine $g $bright 26 40 2; VLine $g $bright 36 40 2
        }
        'cool' {
            Rect $g $bright 16 20 12 6; Rect $g $shade 18 22 8 2
            Rect $g $bright 36 20 12 6; Rect $g $shade 38 22 8 2
            HLine $g $bright 28 21 8
            HLine $g $bright 26 42 10
            VLine $g $bright 34 38 4
        }
        'sleepy' {
            HLine $g $muted 20 22 8; HLine $g $bright 20 26 8
            HLine $g $muted 36 22 8; HLine $g $bright 36 26 8
            Rect $g $bright 28 38 8 6; Rect $g $panel 28 38 8 2
            Rect $g $muted 44 14 8 2; Rect $g $muted 48 16 4 2
            Rect $g $muted 46 18 4 2; Rect $g $muted 44 20 8 2
        }
        'scared' {
            HLine $g $muted 18 18 10; HLine $g $muted 36 18 10
            Rect $g $bright 20 22 6 8; Rect $g $bright 38 22 6 8
            Rect $g $panel 22 26 2 2; Rect $g $panel 40 26 2 2
            Rect $g $bright 26 40 12 4; Rect $g $panel 28 42 8 2
        }
        'curious' {
            HLine $g $muted 20 18 8
            Rect $g $bright 20 22 8 10; Rect $g $bright 36 22 8 10
            Rect $g $panel 22 28 2 2; Rect $g $panel 38 28 2 2
            Rect $g $bright 28 40 8 4
            Rect $g $blue 46 16 4 4
        }
        'smug' {
            HLine $g $muted 36 18 8
            HLine $g $bright 20 26 8; HLine $g $bright 36 26 8
            HLine $g $bright 26 42 10
            VLine $g $bright 34 38 4
        }
        'bored' {
            HLine $g $muted 20 22 8; HLine $g $bright 20 26 8
            HLine $g $muted 36 22 8; HLine $g $bright 36 26 8
            HLine $g $bright 28 42 8
            Rect $g $blue 46 40 4 2
        }
        # Dos frames de paso: se alternan mientras Bitty pasea.
        'walk1' {
            Rect $g $panel 20 44 24 8
            Rect $g $shade 20 44 8 8; Rect $g $shade 36 44 8 8
            Rect $g $bright 20 22 8 10; Rect $g $bright 36 22 8 10
            Rect $g $panel 22 28 2 2; Rect $g $panel 38 28 2 2
            Rect $g $blue 28 40 8 2
        }
        'walk2' {
            Rect $g $panel 20 44 24 8
            Rect $g $shade 24 44 8 8; Rect $g $shade 32 44 8 8
            Rect $g $bright 20 22 8 10; Rect $g $bright 36 22 8 10
            Rect $g $panel 22 28 2 2; Rect $g $panel 38 28 2 2
            Rect $g $blue 28 40 8 2
        }
    }

    $path = Join-Path $dir ("bitty-$Name.png")
    $bmp.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
    "Generado: $path"
    $g.Dispose(); $bmp.Dispose()
}

foreach ($n in @('neutral','blink','celebrate','surprise','thinking','doubt','error',
                 'happy','laugh','sad','angry','love','wink','cool','sleepy',
                 'scared','curious','smug','bored','walk1','walk2')) {
    Draw-Bitty -Name $n
}
