targetScope = 'resourceGroup'

@description('Azure region — southeastasia per requirement')
param location string = 'southeastasia'

@description('Short unique suffix, e.g. 5 random lowercase/digits, to keep globally-unique names collision-free')
param uniqueSuffix string

@secure()
param postgresAdminPassword string
param postgresAdminUser string = 'kothkori_admin'

@secure()
param waPhoneNumberId string
@secure()
param waAccessToken string
@secure()
param waWebhookVerifyToken string
@secure()
param waAppSecret string
@secure()
param sarvamApiKey string

@description('Set after the first deployment once images exist in ACR (see deploy.ps1). Defaults to a placeholder so the template is valid on first apply.')
param gatewayImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
param workerImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

var acrName        = 'aisathiacr${uniqueSuffix}'
var storageName    = 'aisathist${uniqueSuffix}'
var postgresName   = 'aisathi-pg-${uniqueSuffix}'
var keyVaultName   = 'aisathi-kv-${uniqueSuffix}'
var logWorkspace   = 'aisathi-logs'
var envName        = 'aisathi-env'

var redisPassword = uniqueString(resourceGroup().id, 'redis', uniqueSuffix)
var minioRootUser = 'aisathi_minio'
var minioRootPassword = uniqueString(resourceGroup().id, 'minio', uniqueSuffix)

module acr 'modules/acr.bicep' = {
  name: 'acr'
  params: {
    name: acrName
    location: location
  }
}

module storage 'modules/storage.bicep' = {
  name: 'storage'
  params: {
    name: storageName
    location: location
  }
}

module postgres 'modules/postgres.bicep' = {
  name: 'postgres'
  params: {
    name: postgresName
    location: location
    adminUser: postgresAdminUser
    adminPassword: postgresAdminPassword
  }
}

var databaseUrl = 'postgresql+asyncpg://${postgresAdminUser}:${postgresAdminPassword}@${postgres.outputs.fqdn}:5432/${postgres.outputs.databaseName}?ssl=require'

module keyvault 'modules/keyvault.bicep' = {
  name: 'keyvault'
  params: {
    name: keyVaultName
    location: location
    waPhoneNumberId: waPhoneNumberId
    waAccessToken: waAccessToken
    waWebhookVerifyToken: waWebhookVerifyToken
    waAppSecret: waAppSecret
    sarvamApiKey: sarvamApiKey
    databaseUrl: databaseUrl
    redisPassword: redisPassword
    minioRootUser: minioRootUser
    minioRootPassword: minioRootPassword
  }
}

module logs 'modules/loganalytics.bicep' = {
  name: 'logs'
  params: {
    name: logWorkspace
    location: location
  }
}

module apps 'modules/containerapps.bicep' = {
  name: 'apps'
  params: {
    location: location
    envName: envName
    logAnalyticsWorkspaceId: logs.outputs.workspaceId
    logAnalyticsWorkspaceKey: logs.outputs.workspaceKey
    storageAccountName: storage.outputs.accountName
    fileShareName: storage.outputs.fileShareName
    storageAccountKey: storage.outputs.accountKey
    acrLoginServer: acr.outputs.loginServer
    acrName: acr.outputs.name
    keyVaultName: keyvault.outputs.name
    keyVaultUri: keyvault.outputs.uri
    gatewayImage: gatewayImage
    workerImage: workerImage
    waPhoneNumberId: waPhoneNumberId
  }
}

output acrLoginServer string = acr.outputs.loginServer
output gatewayUrl string = 'https://${apps.outputs.gatewayFqdn}'
output minioUrl string = 'https://${apps.outputs.minioFqdn}'
output postgresFqdn string = postgres.outputs.fqdn
output keyVaultName string = keyvault.outputs.name
