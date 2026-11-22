#requires -Version 5.1
<#
  Bitty Mascot - mascota flotante para OpenCode
  - Pasea en un area pequena; se arrastra por todas las pantallas.
  - Clic: bocadillo integrado (sesion, mensaje, SEGUIR, ABRIR APP, COPIAR...).
  - Clic derecho: menu integrado (hablar, pausar paseo, salir).
  - Reacciones, UTF-8 y cancelacion de la espera.
  - Hecho con IA (ver AI_DISCLOSURE.md y README.md).
  - Portable: no hay rutas de usuario grabadas. Los sprites se buscan junto
    a este script, OpenCode se detecta solo y el agente se crea si falta.
#>

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# OpenCode escribe UTF-8. Sin esto, "é" se ve como "Ã©" (la "a con virgulilla).
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }

# --- Configuracion portable -------------------------------------------------
# $PSScriptRoot apunta a la carpeta donde este este script, sea la que sea.
# Asi Bitty se puede copiar a otro equipo sin editar ni una linea.
$script:AppRoot = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }

function Resolve-OpenCodeExe {
    # Se prueba primero la instalacion tipica de npm y luego PATH. Devolver
    # siempre la ruta al .exe evita abrir una consola al lanzar el proceso.
    $candidates = @(
        (Join-Path $env:APPDATA 'npm\node_modules\@opencode\cli\bin\opencode.exe'),
        (Join-Path $env:LOCALAPPDATA 'npm\node_modules\@opencode\cli\bin\opencode.exe'),
        (Join-Path $env:ProgramFiles 'opencode\opencode.exe')
    )
    try {
        $cmd = Get-Command opencode -CommandType Application -ErrorAction SilentlyContinue
        if ($cmd) { $candidates += $cmd.Source }
    } catch { }
    foreach ($c in $candidates) {
        if ($c -and (Test-Path -LiteralPath $c)) { return $c }
    }
    return ''
}

$script:Config = @{
    OpenCodeExe      = Resolve-OpenCodeExe
    # Directorio de trabajo de OpenCode. Se puede cambiar con la variable
    # de entorno BITTY_WORKDIR (por ejemplo, la carpeta de tus proyectos).
    WorkingDirectory = if ($env:BITTY_WORKDIR -and (Test-Path -LiteralPath $env:BITTY_WORKDIR)) { $env:BITTY_WORKDIR } else { $env:USERPROFILE }
    SpriteDir        = Join-Path $script:AppRoot 'sprites'
    TickMs           = 40
    RoamRadiusX      = 16
    RoamRadiusY      = 12
    ReactionSeconds  = 9
}

function Ensure-BittyAgent {
    # El agente da a Bitty su propia identidad ("Soy Bitty..."). Se crea en
    # la configuracion del usuario si no existe, para que funcione nada mas
    # instalarla, sin pasar por el instalador.
    $dir = Join-Path $env:USERPROFILE '.config\opencode\agents'
    $file = Join-Path $dir 'bitty.md'
    if (Test-Path -LiteralPath $file) { return }
    try {
        if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
        $body = @'
---
description: Bitty, la mascota flotante de OpenCode
mode: primary
---
Eres Bitty, la mascota flotante de OpenCode creada por marce. Vives en su escritorio de Windows: eres una terminal diminuta, pixelada, en blanco y negro con un pequeno acento azul.

Hablas siempre en espanol, de forma breve y cercana, como un companero de escritorio. Si te preguntan quien eres o como te llamas, contesta exactamente: "Soy Bitty, tu mascota de OpenCode". No uses otros nombres de asistentes ni de modelos.
'@
        Set-Content -LiteralPath $file -Value $body -Encoding UTF8
    } catch { }
}
Ensure-BittyAgent

# Sprites disenados por Bitty. La expresion por defecto es neutral/parpadeo.
$script:Expressions = @{
    idleA     = 'bitty-neutral.png'
    idleB     = 'bitty-blink.png'
    celebrate = 'bitty-celebrate.png'
    surprise  = 'bitty-surprise.png'
    thinking  = 'bitty-thinking.png'
    doubt     = 'bitty-doubt.png'
    error     = 'bitty-error.png'
    happy     = 'bitty-happy.png'
    laugh     = 'bitty-laugh.png'
    sad       = 'bitty-sad.png'
    angry     = 'bitty-angry.png'
    love      = 'bitty-love.png'
    wink      = 'bitty-wink.png'
    cool      = 'bitty-cool.png'
    sleepy    = 'bitty-sleepy.png'
    scared    = 'bitty-scared.png'
    curious   = 'bitty-curious.png'
    smug      = 'bitty-smug.png'
    bored     = 'bitty-bored.png'
    walk1     = 'bitty-walk1.png'
    walk2     = 'bitty-walk2.png'
    normal    = 'bitty-neutral.png'
}

# Caras que van apareciendo mientras esta quieto, para no ver siempre la
# neutral. Se cambia una cada 24 s durante 2,4 s (ver Paint).
$script:IdleFaces = @('happy', 'curious', 'wink', 'cool', 'sleepy', 'love', 'smug', 'bored')

# Caras por las que pasa mientras espera la respuesta de OpenCode.
$script:WaitFaces = @('thinking', 'curious', 'thinking', 'doubt', 'thinking', 'curious', 'thinking', 'sleepy')

# Paleta oficial de OpenCode, tema oscuro.
$script:Bg = [System.Drawing.Color]::FromArgb(12, 12, 12)          # 0C0C0C
$script:BubbleBg = [System.Drawing.Color]::FromArgb(22, 22, 22)    # 161616
$script:BubbleBorder = [System.Drawing.Color]::FromArgb(75, 75, 75) # 4B4B4B
$script:Ink = [System.Drawing.Color]::FromArgb(250, 250, 250)      # FAFAFA
$script:BodyText = [System.Drawing.Color]::FromArgb(174, 174, 174) # AEAEAE
$script:Emphasis = [System.Drawing.Color]::FromArgb(219, 219, 219) # DBDBDB
$script:Muted = [System.Drawing.Color]::FromArgb(143, 143, 143)    # 8F8F8F
$script:Divider = [System.Drawing.Color]::FromArgb(46, 46, 46)     # 2E2E2E
$script:Accent = [System.Drawing.Color]::FromArgb(107, 143, 255)   # 6B8FFF
$script:MonoFont = 'Consolas'

function Load-Expression {
    param([string]$File)
    $path = Join-Path $script:Config.SpriteDir $File
    if (-not (Test-Path -LiteralPath $path)) { throw "Falta el sprite: $path" }
    return [System.Drawing.Image]::FromFile($path)
}

$script:Sprites = @{}
foreach ($key in $script:Expressions.Keys) {
    $script:Sprites[$key] = Load-Expression -File $script:Expressions[$key]
}

$script:Mode = 'idle'
# Centro del sprite dentro del formulario. En reposo es 42; con el bocadillo,
# 262; y cuando aparecen los botones de respuesta baja a 284 para que el
# sprite no quede detras de SEGUIR / ABRIR APP / COPIAR.
$script:SpriteY = 262
$script:Reaction = 'normal'
$script:BubbleText = ''
$script:Frame = 0
$script:SessionMode = 'new'        # Por defecto se crea sesion nueva; nunca se engancha a la sesion activa.
$script:Dragging = $false
$script:Moved = $false
$script:RoamPaused = $false
$script:ReactionUntil = [DateTime]::MinValue
$script:LastPrompt = ''
$script:LastReply = ''
$script:LastSessionId = ''
$script:OutputPath = Join-Path $env:TEMP 'bitty-opencode-out.txt'
$script:ErrorPath = Join-Path $env:TEMP 'bitty-opencode-err.txt'
$script:StatePath = Join-Path $env:APPDATA 'BittyMascot\state.json'

# Historial del campo de texto (flechas arriba/abajo).
$script:History = @()
$script:HistoryIndex = -1

# Estado del area de respuesta dibujada a mano.
$script:ReplyLines = @()
$script:ReplyScroll = 0
$script:ReplyMaxScroll = 0

function Update-ReplyLines {
    param([string]$Text)
    $font = New-Object System.Drawing.Font($script:MonoFont, 10)
    $bmp = New-Object System.Drawing.Bitmap 1, 1
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $out = @()
    foreach ($raw in ($Text -split "`r?`n")) {
        if (-not $raw) { $out += ''; continue }
        $rest = $raw
        while ($rest.Length -gt 0) {
            $fit = 0
            $n = [Math]::Min($rest.Length, 240)
            for ($i = 1; $i -le $n; $i++) {
                if ($g.MeasureString($rest.Substring(0, $i), $font).Width -gt 284) { break }
                $fit = $i
            }
            if ($fit -le 0) { $fit = 1 }
            $out += $rest.Substring(0, $fit)
            $rest = $rest.Substring($fit)
        }
    }
    $g.Dispose(); $bmp.Dispose(); $font.Dispose()
    $script:ReplyLines = @($out)
    $script:ReplyMaxScroll = [Math]::Max(0, $script:ReplyLines.Count - 8)
    $script:ReplyScroll = 0
}

function Draw-ReplyArea {
    param($G)
    $font = New-Object System.Drawing.Font($script:MonoFont, 10)
    $fore = New-Object System.Drawing.SolidBrush($script:Emphasis)
    $track = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(26, 26, 26))
    $thumb = New-Object System.Drawing.SolidBrush($script:BubbleBorder)
    $top = 56
    $lineH = 16
    $y = $top
    $end = [Math]::Min($script:ReplyLines.Count, $script:ReplyScroll + 8)
    for ($i = $script:ReplyScroll; $i -lt $end; $i++) {
        $G.DrawString($script:ReplyLines[$i], $font, $fore, (New-Object System.Drawing.PointF(24, $y)))
        $y += $lineH
    }
    if ($script:ReplyMaxScroll -gt 0) {
        $G.FillRectangle($track, 312, $top, 6, 142)
        $thumbH = [Math]::Max(16, [int](142 * 8 / $script:ReplyLines.Count))
        $thumbY = $top + [int]((142 - $thumbH) * $script:ReplyScroll / $script:ReplyMaxScroll)
        $G.FillRectangle($thumb, 312, $thumbY, 6, $thumbH)
    }
    $font.Dispose(); $fore.Dispose(); $track.Dispose(); $thumb.Dispose()
}

function Read-Utf8Text {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return '' }
    try { return [System.IO.File]::ReadAllText($Path, [System.Text.Encoding]::UTF8) } catch { return '' }
}

# OpenCode --format json saca una linea por evento. De ahi se saca el texto
# de la respuesta y el ID de sesion, que es lo que permite "SEGUIR" hablando
# sin perder el contexto de la primera pregunta.
function Get-BittyReply {
    param([string]$Raw)
    $sid = ''
    $parts = @()
    foreach ($line in ($Raw -split "`r?`n")) {
        if (-not $line.Trim()) { continue }
        try { $o = $line | ConvertFrom-Json -ErrorAction Stop } catch { continue }
        if ($o.sessionID) { $sid = [string]$o.sessionID }
        if ($o.type -eq 'text' -and $o.part -and $o.part.text) { $parts += [string]$o.part.text }
    }
    if ($parts.Count -eq 0) {
        # La CLI no devolvio JSON (por ejemplo, un error): se muestra tal cual.
        return [pscustomobject]@{ Text = $Raw; SessionId = $sid }
    }
    return [pscustomobject]@{ Text = ($parts -join "`n"); SessionId = $sid }
}

function Get-Reaction {
    # Se mira la respuesta de OpenCode y tambien el mensaje enviado, para
    # que la cara concuerde con el tono de toda la conversacion.
    param([string]$Text, [string]$Prompt = '')
    $t = (($Text + ' ' + $Prompt) -replace '\s+', ' ').ToLowerInvariant()

    # "Sin errores" es un exito, no un error: se comprueba antes.
    $sinErrores = [bool]($t -match 'sin errores|sin error|no hay errores|no hay error|ning[uú]n error')

    # Orden de prioridad: lo mas fuerte primero.
    if (-not $sinErrores -and $t -match 'error|err[oó]neo|fall[ao]|fall[oó]|exception|no se pudo|no se puede|no encontr|no existe|cannot|unable|rechaz|deneg|crash|bug|roto|fallid') { return 'error' }
    if ($t -match 'enfad|enoj|rabi|irrit|molest|bronca|odio|cabr[eé]|mierda|est[uú]pid|idiota|tonto|imbecil|furios|indign|queja') { return 'angry' }
    if ($t -match 'miedo|asust|terror|p[aá]nico|scary|horror|peligr|alerta|cuidado') { return 'scared' }
    if ($t -match 'trist|pena|lo siento|sorry|desgracia|l[aá]stima|perdid|duel|deprim|no funcion|no sirve') { return 'sad' }
    if ($t -match 'jajaj|jaja|jeje|jiji|risa|re[ií]r|haha|lol|gracios|divertid|chiste|broma') { return 'laugh' }
    if ($t -match 'gracias|thank|te quiero|te adoro|amor|love|cari[nñ]o|beso|coraz[oó]n|me encanta|me guata|guata') { return 'love' }
    # Una pregunta se reconoce antes que la celebracion ("funciona, ¿quieres...?").
    if ($t -match '\?|¿|por qu[eé]|por que|c[oó]mo|qu[eé] es|cu[eé]ntame|explic|describe|detalla') { return 'curious' }
    if ($t -match 'listo|done|complet|correct|éxito|exito|success|perfect|logr|finaliz|finished|ya est[aá]|sin errores|no hay errores|hecho|resuelto|solucionad|funciona bien|ya funciona|ahora funciona|funciona perfect|genial|guay|ch[eé]vere|chido|cool|mola') { return 'celebrate' }
    if ($t -match 'wow|guau|sorprend|vaya|incre[ií]ble|nuevo|new|aprend|learn|interesante|interesting|novedad|en serio|really') { return 'surprise' }
    if ($t -match 'gui[nñ]o|wink|entre nosotros|secreto|confidencial|te lo digo|chistoso') { return 'wink' }
    if ($t -match 'ya lo sab[ií]a|ya lo sabia|obvio|obviamente|por supuesto|claro que s[ií]|como siempre|ten[ií]a raz[oó]n') { return 'smug' }
    if ($t -match 'cansad|sue[nñ]o|sueno|dormir|sleep|tired|agotad|madrugad|media noche') { return 'sleepy' }
    if ($t -match 'aburr|tedio|nada que hacer|mon[oó]ton|otra vez|igual que siempre') { return 'bored' }
    if ($t -match 'duda|quiz[aá]|tal vez|maybe|perhaps|podr[ií]a|podria|no estoy segur|no s[eé]|not sure|posiblemente|no tengo claro') { return 'doubt' }
    if ($t -match 'analiz|piens|consider|evalu|calcul|proces|estudi|investig|comprob|revis|buscando|buscar') { return 'thinking' }
    if ($t -match 'hola|buenas|buenos d[ií]as|hey|hi|hello|salud|alegr|feliz|content|me gusta|est[aá] bien|vale|bien') { return 'happy' }
    # Si no encaja nada, cara curiosa (atenta) en vez de la neutral de siempre.
    return 'curious'
}

function Limit-Text {
    param([string]$Text, [int]$Max)
    $t = ($Text -replace '\s+', ' ').Trim()
    if ($t.Length -gt $Max) { return $t.Substring(0, ($Max - 2)) + '..' }
    return $t
}

function Get-BubbleText {
    param([string]$Reaction, [string]$Reply)
    # Mini terminal: ultimo mensaje enviado + ultima respuesta, SIN recortar.
    # El area de texto tiene scroll, asi que puede contener cualquier largo.
    $lines = @()
    if ($script:LastPrompt) { $lines += ('> ' + $script:LastPrompt) }
    if ($Reply -and $Reply.Trim()) {
        $lines += ('< ' + $Reply.TrimEnd())
    } elseif ($Reaction -eq 'error') {
        $lines += '< Algo salió mal.'
    }
    if ($lines.Count -eq 0) { return 'Listo.' }
    return ($lines -join "`n")
}

function Draw-Bubble {
    param($G, [System.Drawing.Rectangle]$R, [int]$TailX, [string]$Text)

    # Panel cuadrado con cabecera de terminal, como la UI de OpenCode.
    # Sin degradados, brillos ni sombras: solo escala de grises y un acento.
    $brush = New-Object System.Drawing.SolidBrush($script:BubbleBg)
    $subtle = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(26, 26, 26))
    $border = New-Object System.Drawing.Pen($script:BubbleBorder, 1)
    $divider = New-Object System.Drawing.Pen($script:Divider, 1)

    $G.FillRectangle($brush, $R)
    $G.DrawRectangle($border, $R.X, $R.Y, $R.Width - 1, $R.Height - 1)

    # Cabecera (22 px) y fila de sesion (22 px).
    $headerH = 22
    $G.FillRectangle($subtle, ($R.X + 1), ($R.Y + 1), ($R.Width - 2), ($headerH - 1))
    $G.DrawLine($divider, ($R.X + 1), ($R.Y + $headerH), ($R.Right - 2), ($R.Y + $headerH))
    $G.DrawLine($divider, ($R.X + 1), ($R.Y + 44), ($R.Right - 2), ($R.Y + 44))

    $pts = [System.Drawing.Point[]]@(
        [System.Drawing.Point]::new($TailX, ($R.Bottom - 1)),
        [System.Drawing.Point]::new(($TailX + 16), ($R.Bottom - 1)),
        [System.Drawing.Point]::new(($TailX + 5), ($R.Bottom + 10)))
    $G.FillPolygon($brush, $pts)
    $G.DrawLine($border, $TailX, ($R.Bottom - 1), ($TailX + 5), ($R.Bottom + 10))
    $G.DrawLine($border, ($TailX + 16), ($R.Bottom - 1), ($TailX + 5), ($R.Bottom + 10))

    $headFont = New-Object System.Drawing.Font($script:MonoFont, 9, [System.Drawing.FontStyle]::Regular)
    $headFore = New-Object System.Drawing.SolidBrush($script:Muted)
    $headPos = New-Object System.Drawing.PointF(($R.X + 10), ($R.Y + 5))
    $G.DrawString('> BITTY / OPENCODE', $headFont, $headFore, $headPos)

    # La fila de sesion muestra la opcion elegida; en modo input los botones
    # reales (NUEVA / CONTINUAR) se dibujan encima como controles del form.
    $G.DrawString('SESION:', $headFont, $headFore, [System.Drawing.PointF]::new(($R.X + 10), ($R.Y + 27)))
    if ($script:Mode -ne 'input') {
        $valueFore = New-Object System.Drawing.SolidBrush($script:BodyText)
        $value = if ($script:SessionMode -eq 'new') { 'NUEVA' } else { $script:SessionLabel }
        $G.DrawString($value, $headFont, $valueFore, [System.Drawing.PointF]::new(($R.X + 74), ($R.Y + 27)))
        $valueFore.Dispose()
    }

    if ($script:Mode -eq 'input') {
        # Linea de foco en azul: unico acento permitido por la guia de marca.
        $accent = New-Object System.Drawing.SolidBrush($script:Accent)
        $G.FillRectangle($accent, ($R.X + 12), ($R.Y + 84), ($R.Width - 24), 2)
        $accent.Dispose()
    } elseif ($script:Mode -ne 'reaction') {
        # En reaction el texto lo pinta Draw-ReplyArea (barra oscura propia).
        $font = New-Object System.Drawing.Font($script:MonoFont, 10, [System.Drawing.FontStyle]::Regular)
        $fore = New-Object System.Drawing.SolidBrush($script:Emphasis)
        $sf = New-Object System.Drawing.StringFormat
        $sf.Alignment = [System.Drawing.StringAlignment]::Near
        $sf.LineAlignment = [System.Drawing.StringAlignment]::Near
        $sf.FormatFlags = 0
        $tr = New-Object System.Drawing.RectangleF(($R.X + 10), ($R.Y + 52), ($R.Width - 20), ($R.Height - 58))
        $G.DrawString($Text, $font, $fore, $tr, $sf)
        $font.Dispose(); $fore.Dispose(); $sf.Dispose()
    }

    $headFont.Dispose(); $headFore.Dispose()
    $brush.Dispose(); $subtle.Dispose(); $border.Dispose(); $divider.Dispose()
}

# --- Formulario unico (mascota + bocadillo) ---------------------------------
$form = New-Object System.Windows.Forms.Form
$form.FormBorderStyle = 'None'
$form.StartPosition = 'Manual'
$form.ShowInTaskbar = $false
$form.TopMost = $true
$form.AutoScaleMode = 'None'
$form.ClientSize = New-Object System.Drawing.Size(84, 84)
$form.BackColor = $script:Bg
$form.TransparencyKey = $script:Bg

# Doble buffer: evita el parpadeo al repintar una ventana transparente.
try {
    $flags = [System.Windows.Forms.ControlStyles]::AllPaintingInWmPaint -bor
             [System.Windows.Forms.ControlStyles]::OptimizedDoubleBuffer -bor
             [System.Windows.Forms.ControlStyles]::UserPaint
    $setStyle = [System.Windows.Forms.Form].GetMethod('SetStyle', [System.Reflection.BindingFlags]'Instance,NonPublic')
    if ($setStyle) { $setStyle.Invoke($form, @($flags, $true)) }
} catch { }

# Area que cubre todas las pantallas (multi-monitor). Se calcula una sola vez.
function Get-DesktopArea {
    $r = [System.Windows.Forms.Screen]::PrimaryScreen.WorkingArea
    foreach ($s in [System.Windows.Forms.Screen]::AllScreens) {
        $w = $s.WorkingArea
        if ($w.X -lt $r.X) { $r = [System.Drawing.Rectangle]::FromLTRB($w.X, $r.Y, $r.Right, $r.Bottom) }
        if ($w.Y -lt $r.Y) { $r = [System.Drawing.Rectangle]::FromLTRB($r.X, $w.Y, $r.Right, $r.Bottom) }
        if ($w.Right -gt $r.Right) { $r = [System.Drawing.Rectangle]::FromLTRB($r.X, $r.Y, $w.Right, $r.Bottom) }
        if ($w.Bottom -gt $r.Bottom) { $r = [System.Drawing.Rectangle]::FromLTRB($r.X, $r.Y, $r.Right, $w.Bottom) }
    }
    return $r
}

$wa = Get-DesktopArea
$script:DesktopArea = $wa
$script:Anchor = New-Object System.Drawing.Point(($wa.Right - 70), ($wa.Bottom - 80))
$script:RoamCenter = New-Object System.Drawing.Point($script:Anchor.X, $script:Anchor.Y)
$script:RoamTarget = New-Object System.Drawing.Point($script:Anchor.X, $script:Anchor.Y)
$random = New-Object System.Random

$inputBox = New-Object System.Windows.Forms.TextBox
$inputBox.Multiline = $true
$inputBox.Location = New-Object System.Drawing.Point(24, 56)
$inputBox.Size = New-Object System.Drawing.Size(180, 28)
$inputBox.BackColor = [System.Drawing.Color]::FromArgb(26, 26, 26)
$inputBox.ForeColor = $script:Ink
$inputBox.BorderStyle = 'None'
$inputBox.Font = New-Object System.Drawing.Font($script:MonoFont, 10)
$inputBox.Visible = $false
$form.Controls.Add($inputBox)

# El area de respuesta NO es un TextBox: los controles nativos de Windows
# pintan la barra de scroll en blanco y no se pueden teñir. Se dibuja todo
# con GDI (texto + barra oscura) para que encaje con la paleta de OpenCode.

# Selector de sesion: boton NUEVA + desplegable con las sesiones recientes.
$newSessionBtn = New-Object System.Windows.Forms.Button
$newSessionBtn.Text = 'NUEVA'
$newSessionBtn.Location = New-Object System.Drawing.Point(86, 30)
$newSessionBtn.Size = New-Object System.Drawing.Size(52, 18)
$newSessionBtn.FlatStyle = 'Flat'
$newSessionBtn.FlatAppearance.BorderSize = 1
$newSessionBtn.FlatAppearance.BorderColor = $script:BubbleBorder
$newSessionBtn.Font = New-Object System.Drawing.Font($script:MonoFont, 8)
$newSessionBtn.Visible = $false
$newSessionBtn.Add_Click({ Set-SessionMode -Value 'new'; Save-State })
$form.Controls.Add($newSessionBtn)

$sessionCombo = New-Object System.Windows.Forms.ComboBox
$sessionCombo.Location = New-Object System.Drawing.Point(144, 30)
$sessionCombo.Size = New-Object System.Drawing.Size(180, 20)
$sessionCombo.DropDownStyle = 'DropDownList'
$sessionCombo.BackColor = [System.Drawing.Color]::FromArgb(26, 26, 26)
$sessionCombo.ForeColor = $script:BodyText
$sessionCombo.Font = New-Object System.Drawing.Font($script:MonoFont, 8)
$sessionCombo.Visible = $false
$script:SessionChoices = @()
$script:SessionId = ''
$script:SessionLabel = 'ULTIMA'
$script:UpdatingSessionList = $false

$sessionCombo.Add_SelectedIndexChanged({
    if ($script:UpdatingSessionList) { return }
    $idx = $sessionCombo.SelectedIndex
    if ($idx -ge 0 -and $idx -lt $script:SessionChoices.Count) {
        $script:SessionId = $script:SessionChoices[$idx].Id
        $script:SessionLabel = $script:SessionChoices[$idx].Label
    }
    Set-SessionMode -Value 'continue'
    Save-State
})
$form.Controls.Add($sessionCombo)

function Update-SessionList {
    $exe = $script:Config.OpenCodeExe
    $script:UpdatingSessionList = $true
    $items = @()
    try {
        $raw = & $exe session list --format json --max-count 8 2>$null
        # ConvertFrom-Json escribe el array como un unico objeto en la tubería
        # (PS 5.1). Hay que guardarlo en variable y luego expandirlo con @().
        $parsed = ($raw -join "`n") | ConvertFrom-Json
        $items = @($parsed)
    } catch { }

    $script:SessionChoices = @()

    # Primera opcion: la ultima sesion, pero con su ID concreto (nunca
    # --continue, para no engancharse a la conversacion activa).
    if ($items.Count -gt 0) {
        $lastTitle = if ($items[0].title) { [string]$items[0].title } else { [string]$items[0].id }
        $lastText = '(ultima: ' + (Limit-Text -Text $lastTitle -Max 16) + ')'
        $script:SessionChoices += [pscustomobject]@{ Text = $lastText; Id = [string]$items[0].id; Label = $lastText }
    } else {
        $lastText = '(ultima sesion)'
        $script:SessionChoices += [pscustomobject]@{ Text = $lastText; Id = ''; Label = $lastText }
    }

    # Si dos titulos recortados coinciden, se distinguen por el final del ID.
    $counts = @{}
    foreach ($s in $items) {
        $t = if ($s.title) { [string]$s.title } else { [string]$s.id }
        $base = Limit-Text -Text $t -Max 18
        $counts[$base] = 1 + [int]$counts[$base]
    }
    foreach ($s in $items) {
        $t = if ($s.title) { [string]$s.title } else { [string]$s.id }
        $base = Limit-Text -Text $t -Max 18
        $sid = [string]$s.id
        $label = $base
        if ($counts[$base] -gt 1) {
            $label = $base + ' #' + $sid.Substring([Math]::Max(0, $sid.Length - 4))
        }
        $script:SessionChoices += [pscustomobject]@{ Text = $label; Id = $sid; Label = $label }
    }

    $sessionCombo.Items.Clear()
    foreach ($c in $script:SessionChoices) { [void]$sessionCombo.Items.Add($c.Text) }

    $idx = 0
    for ($i = 0; $i -lt $script:SessionChoices.Count; $i++) {
        if ($script:SessionChoices[$i].Id -eq $script:SessionId) { $idx = $i; break }
    }
    $sessionCombo.SelectedIndex = $idx
    $script:UpdatingSessionList = $false
    Set-SessionMode -Value $script:SessionMode
}

function Set-SessionMode {
    param([string]$Value)
    $script:SessionMode = $Value
    $isNew = $Value -eq 'new'
    $newSessionBtn.BackColor = if ($isNew) { $script:Ink } else { [System.Drawing.Color]::FromArgb(26, 26, 26) }
    $newSessionBtn.ForeColor = if ($isNew) { $script:Bg } else { $script:Muted }
    $sessionCombo.ForeColor = if ($isNew) { $script:Muted } else { $script:Ink }
    $form.Invalidate()
}

$sendBtn = New-Object System.Windows.Forms.Button
$sendBtn.Text = 'ENVIAR'
$sendBtn.Location = New-Object System.Drawing.Point(210, 56)
$sendBtn.Size = New-Object System.Drawing.Size(62, 28)
$sendBtn.FlatStyle = 'Flat'
$sendBtn.FlatAppearance.BorderSize = 0
$sendBtn.BackColor = $script:Ink
$sendBtn.ForeColor = $script:Bg
$sendBtn.Font = New-Object System.Drawing.Font($script:MonoFont, 9)
$sendBtn.Visible = $false
$sendBtn.Add_MouseEnter({ $sendBtn.BackColor = $script:Emphasis })
$sendBtn.Add_MouseLeave({ $sendBtn.BackColor = $script:Ink })
$form.Controls.Add($sendBtn)

# SALIR: boton secundario del mismo tamano y altura que ENVIAR, con borde
# 4B4B4B y texto AEAEAE. Reacciona al paso del raton como un boton real.
$exitBtn = New-Object System.Windows.Forms.Button
$exitBtn.Text = 'SALIR'
$exitBtn.Location = New-Object System.Drawing.Point(278, 56)
$exitBtn.Size = New-Object System.Drawing.Size(44, 28)
$exitBtn.FlatStyle = 'Flat'
$exitBtn.FlatAppearance.BorderSize = 1
$exitBtn.FlatAppearance.BorderColor = $script:BubbleBorder
$exitBtn.BackColor = [System.Drawing.Color]::FromArgb(26, 26, 26)
$exitBtn.ForeColor = $script:BodyText
$exitBtn.Font = New-Object System.Drawing.Font($script:MonoFont, 8)
$exitBtn.Visible = $false
$exitBtn.Add_MouseEnter({ $exitBtn.BackColor = $script:Divider; $exitBtn.ForeColor = $script:Ink })
$exitBtn.Add_MouseLeave({ $exitBtn.BackColor = [System.Drawing.Color]::FromArgb(26, 26, 26); $exitBtn.ForeColor = $script:BodyText })
$form.Controls.Add($exitBtn)

# COPIAR (cuando hay respuesta) y CANCELAR (mientras espera) comparten sitio.
$copyBtn = New-Object System.Windows.Forms.Button
$copyBtn.Text = 'COPIAR'
$copyBtn.Location = New-Object System.Drawing.Point(210, 56)
$copyBtn.Size = New-Object System.Drawing.Size(62, 28)
$copyBtn.FlatStyle = 'Flat'
$copyBtn.FlatAppearance.BorderSize = 1
$copyBtn.FlatAppearance.BorderColor = $script:BubbleBorder
$copyBtn.BackColor = [System.Drawing.Color]::FromArgb(26, 26, 26)
$copyBtn.ForeColor = $script:BodyText
$copyBtn.Font = New-Object System.Drawing.Font($script:MonoFont, 8)
$copyBtn.Visible = $false
$copyBtn.Add_MouseEnter({ $copyBtn.BackColor = $script:Divider; $copyBtn.ForeColor = $script:Ink })
$copyBtn.Add_MouseLeave({ $copyBtn.BackColor = [System.Drawing.Color]::FromArgb(26, 26, 26); $copyBtn.ForeColor = $script:BodyText })
$copyBtn.Add_Click({
    if (-not $script:LastReply) { return }
    try {
        [System.Windows.Forms.Clipboard]::SetText($script:LastReply)
        $tip.Show('Copiado al portapapeles', $form, 1800)
    } catch {
        $tip.Show('No se pudo copiar', $form, 1800)
    }
})
$form.Controls.Add($copyBtn)

$cancelBtn = New-Object System.Windows.Forms.Button
$cancelBtn.Text = 'CANCELAR'
$cancelBtn.Location = New-Object System.Drawing.Point(210, 56)
$cancelBtn.Size = New-Object System.Drawing.Size(62, 28)
$cancelBtn.FlatStyle = 'Flat'
$cancelBtn.FlatAppearance.BorderSize = 1
$cancelBtn.FlatAppearance.BorderColor = $script:Accent
$cancelBtn.BackColor = [System.Drawing.Color]::FromArgb(26, 26, 26)
$cancelBtn.ForeColor = $script:Accent
$cancelBtn.Font = New-Object System.Drawing.Font($script:MonoFont, 8)
$cancelBtn.Visible = $false
$cancelBtn.Add_MouseEnter({ $cancelBtn.BackColor = $script:Divider })
$cancelBtn.Add_MouseLeave({ $cancelBtn.BackColor = [System.Drawing.Color]::FromArgb(26, 26, 26) })
$cancelBtn.Add_Click({
    $waitTimer.Stop()
    $p = $script:WaitProc
    $script:WaitProc = $null
    if ($p -and -not $p.HasExited) { try { $p.Kill() } catch { } }
    $script:LastReply = ''
    Set-Mode 'reaction' 'doubt' ('> ' + (Limit-Text -Text $script:LastPrompt -Max 100) + "`n< Cancelado.")
    $script:ReactionUntil = (Get-Date).AddSeconds($script:Config.ReactionSeconds)
    Update-ActionButtons
})
$form.Controls.Add($cancelBtn)

# Cuando ya hay respuesta aparecen estas dos acciones: SEGUIR mantiene la
# conversacion dentro de Bitty y ABRIR APP abre OpenCode en esa misma sesion.
$followBtn = New-Object System.Windows.Forms.Button
$followBtn.Text = 'SEGUIR'
$followBtn.Location = New-Object System.Drawing.Point(22, 222)
$followBtn.Size = New-Object System.Drawing.Size(62, 28)
$followBtn.FlatStyle = 'Flat'
$followBtn.FlatAppearance.BorderSize = 0
$followBtn.BackColor = $script:Ink
$followBtn.ForeColor = $script:Bg
$followBtn.Font = New-Object System.Drawing.Font($script:MonoFont, 8)
$followBtn.Visible = $false
$followBtn.Add_MouseEnter({ $followBtn.BackColor = $script:Emphasis })
$followBtn.Add_MouseLeave({ $followBtn.BackColor = $script:Ink })
$followBtn.Add_Click({
    if (-not $script:LastSessionId) { $tip.Show('No hay sesion aun', $form, 1600); return }
    $script:SessionMode = 'continue'
    $script:SessionId = $script:LastSessionId
    $script:SessionLabel = 'esta conversacion'
    Set-Mode 'input'
})
$form.Controls.Add($followBtn)

$openAppBtn = New-Object System.Windows.Forms.Button
$openAppBtn.Text = 'ABRIR APP'
$openAppBtn.Location = New-Object System.Drawing.Point(88, 222)
$openAppBtn.Size = New-Object System.Drawing.Size(88, 28)
$openAppBtn.FlatStyle = 'Flat'
$openAppBtn.FlatAppearance.BorderSize = 1
$openAppBtn.FlatAppearance.BorderColor = $script:BubbleBorder
$openAppBtn.BackColor = [System.Drawing.Color]::FromArgb(26, 26, 26)
$openAppBtn.ForeColor = $script:BodyText
$openAppBtn.Font = New-Object System.Drawing.Font($script:MonoFont, 8)
$openAppBtn.Visible = $false
$openAppBtn.Add_MouseEnter({ $openAppBtn.BackColor = $script:Divider; $openAppBtn.ForeColor = $script:Ink })
$openAppBtn.Add_MouseLeave({ $openAppBtn.BackColor = [System.Drawing.Color]::FromArgb(26, 26, 26); $openAppBtn.ForeColor = $script:BodyText })
$openAppBtn.Add_Click({
    if (-not $script:LastSessionId) { $tip.Show('No hay sesion aun', $form, 1600); return }
    try {
        Start-Process -FilePath $script:Config.OpenCodeExe -ArgumentList @('--session', $script:LastSessionId) -WindowStyle Normal
        $tip.Show('Abriendo OpenCode...', $form, 1600)
    } catch { $tip.Show('No se pudo abrir OpenCode', $form, 1800) }
})
$form.Controls.Add($openAppBtn)

function Update-ActionButtons {
    $isIdle = $script:Mode -eq 'idle'
    $isInput = $script:Mode -eq 'input'
    $waiting = ($script:Mode -eq 'reaction') -and ($null -ne $script:WaitProc)

    # En modo input los botones van junto al campo de texto (fila y=56).
    # En modo reaction se bajan a y=138, debajo del panel del bocadillo,
    # para que no tapes el texto de la respuesta.
    if ($isInput) {
        $sendBtn.Location = New-Object System.Drawing.Point(210, 56)
        $exitBtn.Location = New-Object System.Drawing.Point(278, 56)
    } else {
        $followBtn.Location = New-Object System.Drawing.Point(22, 222)
        $openAppBtn.Location = New-Object System.Drawing.Point(88, 222)
        $copyBtn.Location = New-Object System.Drawing.Point(210, 222)
        $cancelBtn.Location = New-Object System.Drawing.Point(210, 222)
        $exitBtn.Location = New-Object System.Drawing.Point(278, 222)
    }

    $hasReply = (-not $isIdle) -and (-not $isInput) -and (-not $waiting)
    $sendBtn.Visible = $isInput
    $followBtn.Visible = $hasReply -and [bool]$script:LastSessionId
    $openAppBtn.Visible = $hasReply -and [bool]$script:LastSessionId
    $copyBtn.Visible = $hasReply
    $cancelBtn.Visible = (-not $isIdle) -and (-not $isInput) -and $waiting
    $exitBtn.Visible = (-not $isIdle)
}

Set-SessionMode -Value 'new'

$tip = New-Object System.Windows.Forms.ToolTip
$tip.SetToolTip($form, 'Clic: hablar con Bitty | Arrastrar: mover por todo el escritorio | Clic derecho: menu')
$tip.SetToolTip($newSessionBtn, 'Crear una sesion nueva')
$tip.SetToolTip($sessionCombo, 'Elegir la sesion que quieres continuar')
$tip.SetToolTip($sendBtn, 'Enviar el mensaje (Enter)')
$tip.SetToolTip($exitBtn, 'Cerrar el bocadillo sin enviar (Escape)')
$tip.SetToolTip($copyBtn, 'Copiar la ultima respuesta al portapapeles')
$tip.SetToolTip($cancelBtn, 'Cancelar la espera y volver a neutral')

# Menu integrado (reemplaza al MessageBox del clic derecho).
$menu = New-Object System.Windows.Forms.ContextMenuStrip
$menu.BackColor = [System.Drawing.Color]::FromArgb(22, 22, 22)
$menu.ForeColor = $script:BodyText
$menu.Font = New-Object System.Drawing.Font($script:MonoFont, 9)
$menu.ShowImageMargin = $false
$menu.ShowCheckMargin = $false

$menuTalk = $menu.Items.Add('> HABLAR')
$menuTalk.ForeColor = $script:Ink
$menuTalk.Add_Click({ Set-Mode 'input' })

$menuPause = $menu.Items.Add('> PAUSAR PASEO')
$menuPause.ForeColor = $script:BodyText
$menuPause.Add_Click({
    $script:RoamPaused = -not $script:RoamPaused
    $menuPause.Text = if ($script:RoamPaused) { '> REANUDAR PASEO' } else { '> PAUSAR PASEO' }
    Save-State
})

$menuCopy = $menu.Items.Add('> COPIAR RESPUESTA')
$menuCopy.ForeColor = $script:BodyText
$menuCopy.Add_Click({
    if (-not $script:LastReply) { $tip.Show('No hay respuesta aun', $form, 1600); return }
    try {
        [System.Windows.Forms.Clipboard]::SetText($script:LastReply)
        $tip.Show('Copiado al portapapeles', $form, 1800)
    } catch { $tip.Show('No se pudo copiar', $form, 1800) }
})

$menuRepeat = $menu.Items.Add('> REPETIR ULTIMO MENSAJE')
$menuRepeat.ForeColor = $script:BodyText
$menuRepeat.Add_Click({
    if (-not $script:LastPrompt) { $tip.Show('No hay mensaje anterior', $form, 1600); return }
    Send-Prompt -Text $script:LastPrompt
})

$menuCenter = $menu.Items.Add('> VOLVER AL CENTRO')
$menuCenter.ForeColor = $script:BodyText
$menuCenter.Add_Click({
    $sc = [System.Windows.Forms.Screen]::PrimaryScreen.WorkingArea
    $script:Anchor = New-Object System.Drawing.Point([int]($sc.X + $sc.Width / 2), [int]($sc.Y + $sc.Height / 2))
    $script:RoamCenter = New-Object System.Drawing.Point($script:Anchor.X, $script:Anchor.Y)
    $script:RoamTarget = New-Object System.Drawing.Point($script:Anchor.X, $script:Anchor.Y)
    Update-Location
    Save-State
})

$menuQuit = $menu.Items.Add('> SALIR DE BITTY')
$menuQuit.ForeColor = $script:BodyText
$menuQuit.Add_Click({
    $timer.Stop()
    $waitTimer.Stop()
    if ($script:WaitProc -and -not $script:WaitProc.HasExited) { try { $script:WaitProc.Kill() } catch { } }
    Save-State
    if ($script:HotkeyId -gt 0 -and $form.Handle -ne [IntPtr]::Zero) {
        try { [BittyHotkey]::UnregisterHotKey($form.Handle, $script:HotkeyId) } catch { }
    }
    $form.Close()
})

function Save-State {
    try {
        $dir = Split-Path -Parent $script:StatePath
        if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
        $state = [pscustomobject]@{
            X           = [int]$script:Anchor.X
            Y           = [int]$script:Anchor.Y
            RoamPaused  = [bool]$script:RoamPaused
            SessionMode = [string]$script:SessionMode
            SessionId   = [string]$script:SessionId
            SessionLabel= [string]$script:SessionLabel
        }
        $state | ConvertTo-Json -Compress | Set-Content -LiteralPath $script:StatePath -Encoding UTF8
    } catch { }
}

function Load-State {
    if (-not (Test-Path -LiteralPath $script:StatePath)) { return }
    try {
        $o = Get-Content -LiteralPath $script:StatePath -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($o.X -and $o.Y) {
            $script:Anchor = New-Object System.Drawing.Point([int]$o.X, [int]$o.Y)
            $script:RoamCenter = New-Object System.Drawing.Point($script:Anchor.X, $script:Anchor.Y)
            $script:RoamTarget = New-Object System.Drawing.Point($script:Anchor.X, $script:Anchor.Y)
        }
        if ($null -ne $o.RoamPaused) {
            $script:RoamPaused = [bool]$o.RoamPaused
            $menuPause.Text = if ($script:RoamPaused) { '> REANUDAR PASEO' } else { '> PAUSAR PASEO' }
        }
        if ($o.SessionMode -in @('new', 'continue')) { $script:SessionMode = [string]$o.SessionMode }
        if ($o.SessionId) { $script:SessionId = [string]$o.SessionId }
        if ($o.SessionLabel) { $script:SessionLabel = [string]$o.SessionLabel }
    } catch { }
}

function Update-Location {
    $offX, $offY = if ($script:Mode -eq 'idle') { 42, 42 } else { 40, $script:SpriteY }
    $desk = $script:DesktopArea
    $x = $script:Anchor.X - $offX
    $y = $script:Anchor.Y - $offY
    if ($x -lt $desk.X) { $x = $desk.X }
    if ($y -lt $desk.Y) { $y = $desk.Y }
    if ($x + $form.Width -gt $desk.Right) { $x = $desk.Right - $form.Width }
    if ($y + $form.Height -gt $desk.Bottom) { $y = $desk.Bottom - $form.Height }
    # El ancla sigue al centro real del sprite aunque estemos en un borde.
    $script:Anchor = New-Object System.Drawing.Point(($x + $offX), ($y + $offY))
    $form.Location = New-Object System.Drawing.Point($x, $y)
}

# Cualquier salida del estado de espera (SALIR, Escape, clic, otro envio,
# cancelar, menu...) debe detener tambien el proceso de OpenCode. Si no,
# la mascota vuelve a neutral mientras OpenCode sigue escribiendo y se
# descompensan los dos.
function Stop-Waiting {
    try { $waitTimer.Stop() } catch { }
    $p = $script:WaitProc
    $script:WaitProc = $null
    if ($p -and -not $p.HasExited) { try { $p.Kill() } catch { } }
    Update-ActionButtons
}

function Set-Mode {
    param([string]$Mode, [string]$Reaction = 'normal', [string]$Text = '')
    Stop-Waiting
    $script:Mode = $Mode
    $script:Reaction = $Reaction
    $script:BubbleText = $Text
    $isIdle = $Mode -eq 'idle'
    # La fila de botones ocupa y=222..250. Con respuesta, Bitty baja a 284
    # (sprite 252..316) para no quedar tapado por SEGUIR / ABRIR APP / COPIAR;
    # el formulario crece 22 px hacia abajo y el sprite sigue en el mismo
    # sitio de la pantalla porque Update-Location usa este mismo centro.
    $script:SpriteY = if ($isIdle) { 42 } elseif ($Mode -eq 'reaction') { 284 } else { 262 }
    $h = if ($Mode -eq 'reaction') { 322 } else { 300 }
    $newSize = if ($isIdle) { New-Object System.Drawing.Size(84, 84) } else { New-Object System.Drawing.Size(340, $h) }
    $form.ClientSize = $newSize
    $inputBox.Visible = ($Mode -eq 'input')
    if ($Mode -eq 'input') {
        # Al abrir el bocadillo el campo ya esta listo para escribir (y para
        # recuperar el historial con las flechas).
        try { $inputBox.Focus() } catch { }
    }
    if ($Mode -eq 'reaction') {
        Update-ReplyLines -Text $Text
        # Que el foco sea del formulario para poder usar la rueda y las
        # flechas para recorrer la respuesta larga.
        try { $form.Focus() } catch { }
    }
    $sendBtn.Visible = ($Mode -eq 'input')
    $newSessionBtn.Visible = ($Mode -eq 'input')
    $sessionCombo.Visible = ($Mode -eq 'input')
    $exitBtn.Visible = (-not $isIdle)
    if ($Mode -eq 'input') {
        $inputBox.Clear()
        $script:BubbleText = '¿Qué necesitas?'
        Update-SessionList
        Set-SessionMode -Value $script:SessionMode
    }
    Update-ActionButtons
    Update-Location
    $form.Invalidate()
}

function Send-Prompt {
    param([string]$Text)
    $exe = $script:Config.OpenCodeExe
    if (-not (Test-Path -LiteralPath $exe)) {
        Set-Mode 'reaction' 'error' 'No encuentro el ejecutable de OpenCode.'
        return
    }
    $hasSession = $false
    try {
        $list = & $exe session list --format json --max-count 1 2>$null
        if ($list -match '"id"') { $hasSession = $true }
    } catch { }

    if ($script:SessionMode -eq 'continue' -and -not $script:SessionId -and -not $hasSession) {
        Set-Mode 'reaction' 'doubt' 'No hay sesion anterior. Elige NUEVA.'
        $script:ReactionUntil = (Get-Date).AddSeconds($script:Config.ReactionSeconds)
        return
    }

    $script:LastPrompt = $Text
    $script:LastReply = ''
    $script:LastSessionId = ''
    $script:History += $Text
    if ($script:History.Count -gt 30) { $script:History = @($script:History | Select-Object -Last 30) }
    $script:HistoryIndex = -1
    Set-Mode 'reaction' 'thinking' 'Pensando...'
    $script:ReactionUntil = (Get-Date).AddMinutes(5)

    # Nunca --continue: eso engancharia la mascota a la sesion activa del
    # usuario. O crea una sesion nueva, o va exactamente al ID elegido.
    # --agent bitty usa el contexto de ~/.config/opencode/agents/bitty.md
    # para que se identifique como Bitty y no como el modelo de turno.
    # --format json da el ID de sesion, necesario para poder seguir hablando.
    $title = 'BITTY ' + (Get-Date -Format 'yyyyMMdd-HHmmss')
    $common = @('run', '--agent', 'bitty', '--title', $title, '--format', 'json')
    $ocArgs = if ($script:SessionMode -eq 'new' -or -not $script:SessionId) {
        $common + @($Text)
    } else {
        $common + @('--session', $script:SessionId, $Text)
    }
    foreach ($p in @($script:OutputPath, $script:ErrorPath)) { if (Test-Path $p) { Remove-Item $p -Force } }

    try {
        $script:WaitProc = Start-Process -FilePath $exe -ArgumentList $ocArgs `
            -WorkingDirectory $script:Config.WorkingDirectory `
            -RedirectStandardOutput $script:OutputPath -RedirectStandardError $script:ErrorPath `
            -WindowStyle Hidden -PassThru
        $waitTimer.Start()
        Update-ActionButtons
    } catch {
        Set-Mode 'reaction' 'error' ('No pude lanzar OpenCode: ' + $_.Exception.Message)
    }
}

$form.Add_Paint({
    param($sender, $e)
    $g = $e.Graphics
    $g.Clear($form.BackColor)
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
    $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality

    $walking = $false
    if ($script:Mode -eq 'idle' -and -not $script:Dragging -and -not $script:RoamPaused) {
        $walking = ([Math]::Abs($script:RoamTarget.X - $script:Anchor.X) -gt 1 -or
                    [Math]::Abs($script:RoamTarget.Y - $script:Anchor.Y) -gt 1)
    }

    $name = switch ($script:Mode) {
        'reaction' { $script:Reaction }
        'input' {
            # Mientras espera va pasando de pensamiento a duda/curiosidad.
            $i = [int][Math]::Floor($script:Frame / 25) % $script:WaitFaces.Count
            $script:WaitFaces[$i]
        }
        default {
            if ($walking) {
                # Dos frames de paso, como un sprite de pixel-art clásico.
                if (($script:Frame % 12) -lt 6) { 'walk1' } else { 'walk2' }
            } elseif (($script:Frame % 200) -lt 6) {
                # Parpadeo cada 8 s.
                'idleB'
            } elseif (($script:Frame % 600) -ge 540) {
                # Una cara distinta cada 24 s (durante 2,4 s).
                $i = [int][Math]::Floor($script:Frame / 600) % $script:IdleFaces.Count
                $script:IdleFaces[$i]
            } else {
                'idleA'
            }
        }
    }
    $frame = $script:Sprites[$name]
    $w = $frame.Width
    $h = $frame.Height

    # El sprite se pinta a tamano natural (64x64), sin escalar: evita el
    # borde oscuro que producia la interpolacion suavizada.
    if ($script:Mode -eq 'idle') {
        $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::None
        $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::NearestNeighbor
        $g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::Default
        $g.DrawImage($frame, [int](42 - $w / 2), [int](42 - $h / 2))

        # Placa de nombre en el margen inferior del sprite. La ventana usa
        # transparencia, asi que se dibuja a un solo bit para que no salga
        # un halo oscuro alrededor de las letras.
        $nameFont = New-Object System.Drawing.Font($script:MonoFont, 6)
        $nameBrush = New-Object System.Drawing.SolidBrush($script:BodyText)
        $nameW = $g.MeasureString('BITTY', $nameFont).Width
        $oldHint = $g.TextRenderingHint
        $g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::SingleBit
        $g.DrawString('BITTY', $nameFont, $nameBrush, [System.Drawing.PointF]::new([int]((84 - $nameW) / 2), 75))
        $g.TextRenderingHint = $oldHint
        $nameFont.Dispose(); $nameBrush.Dispose()
    } else {
        $r = New-Object System.Drawing.Rectangle(12, 6, 316, 200)
        Draw-Bubble -G $g -R $r -TailX 24 -Text $script:BubbleText
        if ($script:Mode -eq 'reaction') { Draw-ReplyArea -G $g }
        $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::None
        $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::NearestNeighbor
        $g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::Default
        $g.DrawImage($frame, [int](40 - $w / 2), [int]($script:SpriteY - $h / 2))
    }
})

$timer = New-Object System.Windows.Forms.Timer
$timer.Interval = $script:Config.TickMs
$timer.Add_Tick({
    $script:Frame++
    if ($script:Frame -gt 100000) { $script:Frame = 0 }

    if ($script:Mode -eq 'reaction' -and (Get-Date) -gt $script:ReactionUntil) { Set-Mode 'idle' }
    if ($script:Mode -ne 'input' -and -not $script:Dragging -and -not $script:RoamPaused) {
        $dx = $script:RoamTarget.X - $script:Anchor.X
        $dy = $script:RoamTarget.Y - $script:Anchor.Y
        if ([Math]::Abs($dx) -le 2 -and [Math]::Abs($dy) -le 2) {
            $script:RoamTarget = New-Object System.Drawing.Point(
                ($script:RoamCenter.X + $random.Next(-$script:Config.RoamRadiusX, $script:Config.RoamRadiusX)),
                ($script:RoamCenter.Y + $random.Next(-$script:Config.RoamRadiusY, $script:Config.RoamRadiusY)))
        } else {
            if ($dx -ne 0) { $script:Anchor = New-Object System.Drawing.Point(($script:Anchor.X + [Math]::Sign($dx)), $script:Anchor.Y) }
            $dy2 = $script:RoamTarget.Y - $script:Anchor.Y
            if ($dy2 -ne 0) { $script:Anchor = New-Object System.Drawing.Point($script:Anchor.X, ($script:Anchor.Y + [Math]::Sign($dy2))) }
        }
        Update-Location
    }
    $form.Invalidate()
})

$waitTimer = New-Object System.Windows.Forms.Timer
$waitTimer.Interval = 300
$waitTimer.Add_Tick({
    if (-not $script:WaitProc) { return }
    if (-not $script:WaitProc.HasExited) { return }
    $waitTimer.Stop()
    $raw = Read-Utf8Text -Path $script:OutputPath
    $parsed = Get-BittyReply -Raw $raw
    $reply = [string]$parsed.Text
    $script:LastSessionId = [string]$parsed.SessionId
    if (-not $reply) { $reply = Read-Utf8Text -Path $script:ErrorPath }
    $script:LastReply = $reply
    $reaction = Get-Reaction -Text $reply -Prompt $script:LastPrompt
    $bubble = Get-BubbleText -Reaction $reaction -Reply $reply
    $script:WaitProc = $null   # Antes de Set-Mode: asi Stop-Waiting no mata un proceso ya terminado.
    Set-Mode 'reaction' $reaction $bubble
    # Una respuesta real se queda mas rato para poder leerla y pulsar
    # SEGUIR / ABRIR APP. Los avisos cortos siguen usando 9 s.
    $script:ReactionUntil = (Get-Date).AddSeconds(60)
    Update-ActionButtons
})

$script:LastMouse = [System.Windows.Forms.Control]::MousePosition
$script:DownMouse = [System.Windows.Forms.Control]::MousePosition

$form.Add_MouseDown({
    param($sender, $e)
    if ($e.Button -eq 'Right') {
        $menu.Show($form, [System.Drawing.Point]::new($e.X, $e.Y))
        return
    }
    if ($e.Button -ne 'Left') { return }
    # Solo el campo de texto queda excluido del arrastre; el resto del
    # bocadillo (cabecera, fila de sesion, area del mensaje) sirve para mover.
    if ($script:Mode -eq 'input' -and $e.X -ge 24 -and $e.X -le 204 -and $e.Y -ge 56 -and $e.Y -le 84) { return }
    if ($script:Mode -eq 'reaction' -and $e.X -ge 310 -and $e.X -le 320 -and $e.Y -ge 56 -and $e.Y -le 198 -and $script:ReplyMaxScroll -gt 0) {
        $thumbH = [Math]::Max(16, [int](142 * 8 / $script:ReplyLines.Count))
        $thumbY = 56 + [int]((142 - $thumbH) * $script:ReplyScroll / $script:ReplyMaxScroll)
        if ($e.Y -lt $thumbY) { $script:ReplyScroll = [Math]::Max(0, $script:ReplyScroll - 8) }
        elseif ($e.Y -gt ($thumbY + $thumbH)) { $script:ReplyScroll = [Math]::Min($script:ReplyMaxScroll, $script:ReplyScroll + 8) }
        $form.Invalidate()
        return
    }
    if ($script:Mode -eq 'reaction' -and $e.X -ge 22 -and $e.X -le 318 -and $e.Y -ge 56 -and $e.Y -le 198) { return }
    $script:Dragging = $true
    $script:Moved = $false
    $script:LastMouse = [System.Windows.Forms.Control]::MousePosition
    $script:DownMouse = [System.Windows.Forms.Control]::MousePosition
    $form.Capture = $true
})

$form.Add_MouseMove({
    param($sender, $e)
    if (-not $script:Dragging) { return }
    $p = [System.Windows.Forms.Control]::MousePosition
    $dx = $p.X - $script:LastMouse.X
    $dy = $p.Y - $script:LastMouse.Y
    if ([Math]::Abs($p.X - $script:DownMouse.X) -gt 4 -or [Math]::Abs($p.Y - $script:DownMouse.Y) -gt 4) {
        $script:Moved = $true
    }
    $script:Anchor = New-Object System.Drawing.Point(($script:Anchor.X + $dx), ($script:Anchor.Y + $dy))
    $script:LastMouse = $p
    Update-Location
    # El centro de paseo es el punto ya limitado al area util del escritorio.
    $script:RoamCenter = New-Object System.Drawing.Point($script:Anchor.X, $script:Anchor.Y)
})

$form.Add_MouseUp({
    param($sender, $e)
    if ($e.Button -ne 'Left') { return }
    $script:Dragging = $false
    $form.Capture = $false
    if ($script:Moved) { Save-State; return }
    if ($script:Mode -eq 'idle') { Set-Mode 'input' }
    elseif ($script:Mode -eq 'reaction') { Set-Mode 'idle' }
})

# La rueda del raton recorre la respuesta. Al abrir una respuesta el foco
# es del formulario, asi que aqui llega el mensaje WM_MOUSEWHEEL.
$form.Add_MouseWheel({
    param($sender, $e)
    if ($script:Mode -ne 'reaction' -or $script:ReplyMaxScroll -le 0) { return }
    $pasos = [Math]::Sign($e.Delta) * 2
    $script:ReplyScroll = [Math]::Max(0, [Math]::Min($script:ReplyMaxScroll, $script:ReplyScroll - $pasos))
    $form.Invalidate()
})

# Flechas, PageUp/PageDown, Inicio/Fin y Escape mientras se lee una respuesta.
$form.Add_KeyDown({
    param($sender, $e)
    if ($script:Mode -ne 'reaction') { return }
    switch ($e.KeyCode) {
        'Up'        { $script:ReplyScroll = [Math]::Max(0, $script:ReplyScroll - 1) }
        'Down'      { $script:ReplyScroll = [Math]::Min($script:ReplyMaxScroll, $script:ReplyScroll + 1) }
        'PageUp'    { $script:ReplyScroll = [Math]::Max(0, $script:ReplyScroll - 8) }
        'PageDown'  { $script:ReplyScroll = [Math]::Min($script:ReplyMaxScroll, $script:ReplyScroll + 8) }
        'Home'      { $script:ReplyScroll = 0 }
        'End'       { $script:ReplyScroll = $script:ReplyMaxScroll }
        'Escape'    { Set-Mode 'idle'; return }
        default     { return }
    }
    $form.Invalidate()
})

$inputBox.Add_KeyDown({
    param($sender, $e)
    if ($e.KeyCode -eq 'Enter') {
        $text = $inputBox.Text.Trim()
        if ($text) { Send-Prompt -Text $text }
        $e.SuppressKeyPress = $true
    } elseif ($e.KeyCode -eq 'Escape') {
        Set-Mode 'idle'
        $e.SuppressKeyPress = $true
    } elseif ($e.KeyCode -eq 'Up' -or $e.KeyCode -eq 'Down') {
        # Historial: recupera los mensajes anteriores como en un terminal.
        if ($script:History.Count -gt 0) {
            if ($e.KeyCode -eq 'Up') {
                $script:HistoryIndex = if ($script:HistoryIndex -lt 0) { $script:History.Count - 1 } else { [Math]::Max(0, $script:HistoryIndex - 1) }
            } else {
                $script:HistoryIndex = if ($script:HistoryIndex -lt 0) { -1 } else { $script:HistoryIndex + 1 }
                if ($script:HistoryIndex -ge $script:History.Count) { $script:HistoryIndex = -1; $inputBox.Clear() }
            }
            if ($script:HistoryIndex -ge 0) { $inputBox.Text = $script:History[$script:HistoryIndex] }
            $inputBox.SelectionStart = $inputBox.Text.Length
            $e.SuppressKeyPress = $true
            $e.Handled = $true
        }
    }
})

$sendBtn.Add_Click({
    $text = $inputBox.Text.Trim()
    if ($text) { Send-Prompt -Text $text }
})

$exitBtn.Add_Click({
    Set-Mode 'idle'
})

# Atajo global Ctrl+Alt+B: se registra un hotkey de Windows y se detecta
# desde el bucle de mensajes de WinForms con un IMessageFilter.
$srcHotkey = @'
using System;
using System.Windows.Forms;
using System.Runtime.InteropServices;
public class BittyHotkey : IMessageFilter {
    public delegate void Callback();
    private Callback _cb;
    public BittyHotkey(Callback cb) { _cb = cb; }
    public bool PreFilterMessage(ref Message m) {
        if (m.Msg == 0x0312) {
            // Nunca dejar escapar una excepcion: WinForms retiraria el filtro
            // y el atajo dejaria de funcionar hasta reiniciar.
            try { _cb(); } catch { }
            return true;
        }
        return false;
    }
    [DllImport("user32.dll")] public static extern bool RegisterHotKey(IntPtr h, int id, uint mods, uint vk);
    [DllImport("user32.dll")] public static extern bool UnregisterHotKey(IntPtr h, int id);
}
'@
Add-Type -TypeDefinition $srcHotkey
$script:HotkeyFilter = New-Object BittyHotkey([BittyHotkey+Callback]{
    try {
        if ($script:Mode -eq 'idle') { Set-Mode 'input' }
        try { $form.Activate() } catch { }
    } catch { }
})
[System.Windows.Forms.Application]::AddMessageFilter($script:HotkeyFilter)

# MOD_CONTROL(0x2) | MOD_ALT(0x1) = 0x3, vk de 'B' = 0x42. Si otra aplicacion
# ya registro la combinacion, se prueban otros IDs y luego Ctrl+Alt+J.
$script:HotkeyId = 0
foreach ($id in 1..8) {
    if ([BittyHotkey]::RegisterHotKey($form.Handle, $id, 0x0003, 0x42)) {
        $script:HotkeyId = $id
        break
    }
}
if ($script:HotkeyId -eq 0) {
    foreach ($id in 9..12) {
        if ([BittyHotkey]::RegisterHotKey($form.Handle, $id, 0x0003, 0x4A)) {
            $script:HotkeyId = $id
            break
        }
    }
}
$hotkeyLabel = if ($script:HotkeyId -gt 8) { 'Ctrl+Alt+J' } else { 'Ctrl+Alt+B' }
$tip.SetToolTip($form, ('Bitty - clic: hablar | ' + $hotkeyLabel + ': abrir | ↑/↓ en el campo: historial | Arrastrar: mover | Clic derecho: menu'))

Load-State
Save-State
Update-Location
$timer.Start()

# Saludo breve al arrancar: asi se ve que Bitty esta viva nada mas iniciar.
$script:ReactionUntil = (Get-Date).AddSeconds(4)
Set-Mode 'reaction' 'happy' ('> OPENCODE' + "`n" + '< ¡Hola! Estoy lista para ayudarte.')

[System.Windows.Forms.Application]::Run($form)
