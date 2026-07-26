param location string
param envName string
param logAnalyticsWorkspaceId string
@secure()
param logAnalyticsWorkspaceKey string

param acrLoginServer string
param acrName string

param keyVaultName string
param keyVaultUri string

param appImage string
param waPhoneNumberId string

resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${envName}-identity'
  location: location
}

resource keyVaultRef 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: keyVaultName
}

var keyVaultSecretsUserRoleId = '4633458b-17de-408a-b874-0445c86b69e6'
resource kvRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVaultRef.id, identity.id, keyVaultSecretsUserRoleId)
  scope: keyVaultRef
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', keyVaultSecretsUserRoleId)
    principalId: identity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource acrRef 'Microsoft.ContainerRegistry/registries@2023-07-01' existing = {
  name: acrName
}

var acrPullRoleId = '7f951dda-4ed3-4680-a7ca-43fe172d538d'
resource acrRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(acrRef.id, identity.id, acrPullRoleId)
  scope: acrRef
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', acrPullRoleId)
    principalId: identity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource env 'Microsoft.App/managedEnvironments@2023-11-02-preview' = {
  name: envName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsWorkspaceId
        sharedKey: logAnalyticsWorkspaceKey
      }
    }
  }
}

var appSecrets = [
  { name: 'wa-access-token', keyVaultUrl: '${keyVaultUri}secrets/wa-access-token', identity: identity.id }
  { name: 'wa-webhook-verify-token', keyVaultUrl: '${keyVaultUri}secrets/wa-webhook-verify-token', identity: identity.id }
  { name: 'wa-app-secret', keyVaultUrl: '${keyVaultUri}secrets/wa-app-secret', identity: identity.id }
  { name: 'sarvam-api-key', keyVaultUrl: '${keyVaultUri}secrets/sarvam-api-key', identity: identity.id }
  { name: 'database-url', keyVaultUrl: '${keyVaultUri}secrets/database-url', identity: identity.id }
  { name: 'azure-storage-connection-string', keyVaultUrl: '${keyVaultUri}secrets/azure-storage-connection-string', identity: identity.id }
]

var appEnv = [
  { name: 'WA_PHONE_NUMBER_ID', value: waPhoneNumberId }
  { name: 'WA_ACCESS_TOKEN', secretRef: 'wa-access-token' }
  { name: 'WA_WEBHOOK_VERIFY_TOKEN', secretRef: 'wa-webhook-verify-token' }
  { name: 'WA_APP_SECRET', secretRef: 'wa-app-secret' }
  { name: 'DATABASE_URL', secretRef: 'database-url' }
  { name: 'SARVAM_API_KEY', secretRef: 'sarvam-api-key' }
  { name: 'AZURE_STORAGE_CONNECTION_STRING', secretRef: 'azure-storage-connection-string' }
  { name: 'AZURE_STORAGE_CONTAINER', value: 'aisathi-assets' }
  { name: 'USE_LOCAL_MODELS', value: 'false' }
  { name: 'DEBUG', value: 'false' }
  { name: 'MAX_MESSAGES_PER_HOUR', value: '30' }
]

resource app 'Microsoft.App/containerApps@2023-11-02-preview' = {
  name: 'ai-sathi-app'
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${identity.id}': {}
    }
  }
  properties: {
    managedEnvironmentId: env.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
      }
      registries: [
        {
          server: acrLoginServer
          identity: identity.id
        }
      ]
      secrets: appSecrets
    }
    template: {
      containers: [
        {
          name: 'app'
          image: appImage
          resources: {
            cpu: json('0.5')
            memory: '1.0Gi'
          }
          env: appEnv
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 1
      }
    }
  }
  dependsOn: [
    kvRoleAssignment
    acrRoleAssignment
  ]
}

output appFqdn string = app.properties.configuration.ingress.fqdn
output identityId string = identity.id
