targetScope = 'resourceGroup'

@description('Azure region')
param location string = 'southeastasia'

@description('Short unique suffix to keep globally-unique names collision-free')
param uniqueSuffix string

@secure()
param postgresAdminPassword string
param postgresAdminUser string = 'aisathi_admin'

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

@description('Set after the first deployment once the real image exists in ACR (see deploy.ps1). Defaults to a placeholder so the template is valid on first apply.')
param appImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

var acrName      = 'aisathiacr${uniqueSuffix}'
var storageName  = 'aisathist${uniqueSuffix}'
var postgresName = 'aisathi-pg-${uniqueSuffix}'
var keyVaultName = 'aisathi-kv-${uniqueSuffix}'
var logWorkspace = 'aisathi-logs'
var envName      = 'aisathi-env'

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
    azureStorageConnectionString: storage.outputs.connectionString
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
    acrLoginServer: acr.outputs.loginServer
    acrName: acr.outputs.name
    keyVaultName: keyvault.outputs.name
    keyVaultUri: keyvault.outputs.uri
    appImage: appImage
    waPhoneNumberId: waPhoneNumberId
  }
}

output acrLoginServer string = acr.outputs.loginServer
output appUrl string = 'https://${apps.outputs.appFqdn}'
output postgresFqdn string = postgres.outputs.fqdn
output keyVaultName string = keyvault.outputs.name
output storageAccountName string = storage.outputs.accountName
