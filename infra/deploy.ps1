[CmdletBinding()]
param(
    [string]$ResourceGroup = "ai-sathi-prod",
    [string]$Location      = "southeastasia",
    [string]$RepoRoot      = (Get-Location).Path
)

$ErrorActionPreference = "Stop"

function Read-PlainSecret([string]$Prompt) {
    $secure = Read-Host -Prompt $Prompt -AsSecureString
    $bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    return [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr)
}

$Suffix = -join ((48..57) + (97..122) | Get-Random -Count 5 | ForEach-Object {[char]$_})

$PostgresPassword = Read-PlainSecret "PostgreSQL admin password (min 12 chars)"
$WaPhoneNumberId   = Read-PlainSecret "WhatsApp WA_PHONE_NUMBER_ID"
$WaAccessToken     = Read-PlainSecret "WhatsApp WA_ACCESS_TOKEN"
$WaWebhookVerify   = Read-PlainSecret "WhatsApp WA_WEBHOOK_VERIFY_TOKEN (you choose this string)"
$WaAppSecret       = Read-PlainSecret "WhatsApp WA_APP_SECRET"
$SarvamApiKey      = Read-PlainSecret "Sarvam SARVAM_API_KEY"

Write-Host "==== Phase 1: deploying infrastructure (placeholder app image) ===="
az group create --name $ResourceGroup --location $Location | Out-Null

$DeployOutput = az deployment group create `
    --resource-group $ResourceGroup `
    --template-file "$PSScriptRoot/main.bicep" `
    --parameters "$PSScriptRoot/main.parameters.json" `
    --parameters uniqueSuffix=$Suffix `
                 postgresAdminPassword=$PostgresPassword `
                 waPhoneNumberId=$WaPhoneNumberId `
                 waAccessToken=$WaAccessToken `
                 waWebhookVerifyToken=$WaWebhookVerify `
                 waAppSecret=$WaAppSecret `
                 sarvamApiKey=$SarvamApiKey `
    | ConvertFrom-Json

$AcrLoginServer = $DeployOutput.properties.outputs.acrLoginServer.value
$AcrName = $AcrLoginServer.Split('.')[0]

Write-Host "==== Phase 2: building and pushing the application image ===="

$AppDockerfile = Join-Path $RepoRoot "services/gateway/Dockerfile"

if (-not (Test-Path $AppDockerfile)) {
    Write-Host "Dockerfile not found under $RepoRoot." -ForegroundColor Yellow
    Write-Host "Re-run this script from the repo root, or build/push manually:"
    Write-Host "  az acr build --registry $AcrName --image ai-sathi-app:latest --file services/gateway/Dockerfile ."
    Write-Host "Then: az containerapp update --name ai-sathi-app --resource-group $ResourceGroup --image $AcrLoginServer/ai-sathi-app:latest"
    exit 0
}

az acr build --registry $AcrName --image "ai-sathi-app:latest" --file $AppDockerfile $RepoRoot

Write-Host "==== Pointing the container app at the real image ===="
az containerapp update `
    --name ai-sathi-app `
    --resource-group $ResourceGroup `
    --image "$AcrLoginServer/ai-sathi-app:latest" | Out-Null

$AppUrl = $DeployOutput.properties.outputs.appUrl.value
Write-Host ""
Write-Host "==== Done ====" -ForegroundColor Green
Write-Host "App URL: $AppUrl"
Write-Host "Set the Meta WhatsApp webhook callback URL to: $AppUrl/webhook/whatsapp"
Write-Host "Verify with: curl $AppUrl/health"
Write-Host ""
Write-Host "Remaining manual steps:"
Write-Host "  1. Run migrations/*.sql against Postgres (including the new 0007_webhook_dedup.sql)"
Write-Host "  2. Confirm the storage account container 'aisathi-assets' exists (created by Bicep already)"
Write-Host "  3. Set a Sarvam spend cap on the Sarvam dashboard"
