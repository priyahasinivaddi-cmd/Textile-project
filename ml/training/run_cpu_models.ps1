param(
    [int]$Epochs = 8,
    [int]$BatchSize = 32,
    [ValidateSet("b0", "b2")]
    [string[]]$Backbones = @("b0", "b2")
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$pythonExe = Join-Path $projectRoot "backend\.venv\Scripts\python.exe"
$statusPath = Join-Path $projectRoot "ml\artifacts\multitask\cpu_training_status.json"
$logPath = Join-Path $projectRoot "ml\artifacts\multitask\cpu_training.log"
$trainer = Join-Path $projectRoot "ml\training\train_multitask.py"

function Write-Status([string]$state, [string]$backbone, [string]$message) {
    $status = @{
        state = $state
        backbone = $backbone
        message = $message
        updated_at = [DateTime]::UtcNow.ToString("o")
    } | ConvertTo-Json
    Set-Content -LiteralPath $statusPath -Value $status -Encoding UTF8
}

Set-Location $projectRoot
$env:PYTHONUNBUFFERED = "1"
try {
    foreach ($backbone in $Backbones) {
        Write-Status "running" $backbone "Training EfficientNet-$($backbone.ToUpper()) on CPU"
        $ErrorActionPreference = "Continue"
        & $pythonExe -u $trainer --backbone $backbone --epochs $Epochs --batch-size $BatchSize --allow-cpu *>> $logPath
        $ErrorActionPreference = "Stop"
        if ($LASTEXITCODE -ne 0) { throw "EfficientNet-$backbone exited with code $LASTEXITCODE" }
    }
    $completedBackbones = $Backbones -join ","
    Write-Status "complete" $completedBackbones "Requested CPU training runs completed"
} catch {
    Write-Status "failed" $backbone $_.Exception.Message
    throw
}
