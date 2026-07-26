param name string
param location string
param tenantId string = subscription().tenantId

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
@secure()
param databaseUrl string
@secure()
param redisPassword string
@secure()
param minioRootUser string
@secure()
param minioRootPassword string

resource kv 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: name
  location: location
  properties: {
    tenantId: tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
  }
}

resource secretWaPhoneNumberId 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: kv
  name: 'wa-phone-number-id'
  properties: { value: waPhoneNumberId }
}
resource secretWaAccessToken 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: kv
  name: 'wa-access-token'
  properties: { value: waAccessToken }
}
resource secretWaWebhookVerifyToken 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: kv
  name: 'wa-webhook-verify-token'
  properties: { value: waWebhookVerifyToken }
}
resource secretWaAppSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: kv
  name: 'wa-app-secret'
  properties: { value: waAppSecret }
}
resource secretSarvamApiKey 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: kv
  name: 'sarvam-api-key'
  properties: { value: sarvamApiKey }
}
resource secretDatabaseUrl 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: kv
  name: 'database-url'
  properties: { value: databaseUrl }
}
resource secretRedisPassword 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: kv
  name: 'redis-password'
  properties: { value: redisPassword }
}
resource secretMinioRootUser 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: kv
  name: 'minio-root-user'
  properties: { value: minioRootUser }
}
resource secretMinioRootPassword 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: kv
  name: 'minio-root-password'
  properties: { value: minioRootPassword }
}

output id string = kv.id
output name string = kv.name
output uri string = kv.properties.vaultUri
