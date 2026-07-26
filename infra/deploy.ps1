<#
============================================================================
 AI-SATHI — Bicep deployment wrapper
 Two phases, because the Container Apps in main.bicep need images that
 can't exist until the ACR they're pushed to already exists:

   Phase 1: az deployment group create   -> creates everything, gateway/
            worker start on a placeholder "hello world" image so the
            template is valid on a from-scratch subscription.
   Phase 2: az acr build (gateway + worker) -> az containerapp update
            -> apps now run your actual code.

 Run from the repository root.
============================================================================
#>

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

Write-Host "==== Phase 1: deploying infrastructure (placeholder app images) ===="
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

Write-Host "==== Phase 2: building and pushing application images ===="

$GatewayDockerfile = Join-Path $RepoRoot "services/gateway/Dockerfile"
$OrchestratorDockerfile = Join-Path $RepoRoot "services/orchestrator/Dockerfile"

if (-not (Test-Path $GatewayDockerfile) -or -not (Test-Path $OrchestratorDockerfile)) {
    Write-Host "Dockerfiles not found under $RepoRoot." -ForegroundColor Yellow
    Write-Host "Re-run this script from the repo root, or build/push manually:"
    Write-Host "  az acr build --registry $AcrName --image ai-sathi-gateway:latest --file services/gateway/Dockerfile ."
    Write-Host "  az acr build --registry $AcrName --image ai-sathi-worker:latest --file services/orchestrator/Dockerfile ."
    Write-Host "Then: az containerapp update --name ai-sathi-gateway --resource-group $ResourceGroup --image $AcrLoginServer/ai-sathi-gateway:latest"
    Write-Host "      az containerapp update --name ai-sathi-worker  --resource-group $ResourceGroup --image $AcrLoginServer/ai-sathi-worker:latest"
    exit 0
}

az acr build --registry $AcrName --image "ai-sathi-gateway:latest" --file $GatewayDockerfile $RepoRoot
az acr build --registry $AcrName --image "ai-sathi-worker:latest" --file $OrchestratorDockerfile $RepoRoot

Write-Host "==== Pointing the container apps at the real images ===="
az containerapp update `
    --name ai-sathi-gateway `
    --resource-group $ResourceGroup `
    --image "$AcrLoginServer/ai-sathi-gateway:latest" | Out-Null

az containerapp update `
    --name ai-sathi-worker `
    --resource-group $ResourceGroup `
    --image "$AcrLoginServer/ai-sathi-worker:latest" | Out-Null

$GatewayUrl = $DeployOutput.properties.outputs.gatewayUrl.value
Write-Host ""
Write-Host "==== Done ====" -ForegroundColor Green
Write-Host "Gateway URL: $GatewayUrl"
Write-Host "Set the Meta WhatsApp webhook callback URL to: $GatewayUrl/webhook/whatsapp"
Write-Host "Verify with: curl $GatewayUrl/health"
Write-Host ""
Write-Host "Remaining manual steps — see ../README-deployment.md:"
Write-Host "  1. Create the MinIO bucket, then lock its ingress to internal"
Write-Host "  2. Run migrations/*.sql against Postgres"
Write-Host "  3. Fix the REDIS_URL interpolation gap flagged in modules/containerapps.bicep"
