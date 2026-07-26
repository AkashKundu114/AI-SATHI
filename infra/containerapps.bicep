param location string
param envName string
param logAnalyticsWorkspaceId string
@secure()
param logAnalyticsWorkspaceKey string

param storageAccountName string
param fileShareName string
@secure()
param storageAccountKey string

param acrLoginServer string
param acrName string

param keyVaultName string
param keyVaultUri string

param gatewayImage string
param workerImage string

param waPhoneNumberId string // not secret-worthy on its own, but kept alongside the rest via KV for consistency

// ---------------------------------------------------------------------------
// Managed identity — used by every container app to read Key Vault secrets
// and pull from ACR, so nothing sensitive sits in plaintext env vars or in
// this template's own parameters after deployment.
// ---------------------------------------------------------------------------
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

// ---------------------------------------------------------------------------
// Environment
// ---------------------------------------------------------------------------
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

resource envStorage 'Microsoft.App/managedEnvironments/storages@2023-11-02-preview' = {
  parent: env
  name: 'minio-storage'
  properties: {
    azureFile: {
      accountName: storageAccountName
      accountKey: storageAccountKey
      shareName: fileShareName
      accessMode: 'ReadWrite'
    }
  }
}

// ---------------------------------------------------------------------------
// MinIO — S3-compatible object storage (drop-in for the boto3 S3 client
// already used in shared/storage/s3_client.py; no application code change).
// Ingress is external here only so `mc` on your laptop can create the
// bucket once post-deploy; switch to 'Internal' afterwards (see
// README-deployment.md).
// ---------------------------------------------------------------------------
resource minio 'Microsoft.App/containerApps@2023-11-02-preview' = {
  name: 'ai-sathi-minio'
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
        targetPort: 9000
        transport: 'auto'
      }
      secrets: [
        { name: 'minio-user', keyVaultUrl: '${keyVaultUri}secrets/minio-root-user', identity: identity.id }
        { name: 'minio-password', keyVaultUrl: '${keyVaultUri}secrets/minio-root-password', identity: identity.id }
      ]
    }
    template: {
      containers: [
        {
          name: 'minio'
          image: 'docker.io/minio/minio:latest'
          command: [ 'minio' ]
          args: [ 'server', '/data', '--console-address', ':9001' ]
          resources: {
            cpu: json('0.5')
            memory: '1.0Gi'
          }
          env: [
            { name: 'MINIO_ROOT_USER', secretRef: 'minio-user' }
            { name: 'MINIO_ROOT_PASSWORD', secretRef: 'minio-password' }
          ]
          volumeMounts: [
            { volumeName: 'minio-data', mountPath: '/data' }
          ]
        }
      ]
      volumes: [
        { name: 'minio-data', storageType: 'AzureFile', storageName: envStorage.name }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 1
      }
    }
  }
}

// ---------------------------------------------------------------------------
// Redis — internal ingress only, no persistent volume (see caveat in
// deploy-ai-sathi.ps1 / README-deployment.md: data is lost on restart).
// ---------------------------------------------------------------------------
resource redis 'Microsoft.App/containerApps@2023-11-02-preview' = {
  name: 'ai-sathi-redis'
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
        external: false
        targetPort: 6379
        transport: 'tcp'
      }
      secrets: [
        { name: 'redis-password', keyVaultUrl: '${keyVaultUri}secrets/redis-password', identity: identity.id }
      ]
    }
    template: {
      containers: [
        {
          name: 'redis'
          image: 'docker.io/library/redis:7-alpine'
          command: [ 'redis-server' ]
          args: [ '--requirepass', '$(REDIS_PASSWORD)', '--appendonly', 'yes' ]
          resources: {
            cpu: json('0.25')
            memory: '0.5Gi'
          }
          env: [
            { name: 'REDIS_PASSWORD', secretRef: 'redis-password' }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 1
      }
    }
  }
}

// ---------------------------------------------------------------------------
// Shared env/secret block for gateway + worker (identical config — the
// worker just runs the Celery entrypoint instead of uvicorn, per
// services/orchestrator/Dockerfile's CMD).
// ---------------------------------------------------------------------------
var sharedSecrets = [
  { name: 'wa-access-token', keyVaultUrl: '${keyVaultUri}secrets/wa-access-token', identity: identity.id }
  { name: 'wa-webhook-verify-token', keyVaultUrl: '${keyVaultUri}secrets/wa-webhook-verify-token', identity: identity.id }
  { name: 'wa-app-secret', keyVaultUrl: '${keyVaultUri}secrets/wa-app-secret', identity: identity.id }
  { name: 'sarvam-api-key', keyVaultUrl: '${keyVaultUri}secrets/sarvam-api-key', identity: identity.id }
  { name: 'database-url', keyVaultUrl: '${keyVaultUri}secrets/database-url', identity: identity.id }
  { name: 'redis-password', keyVaultUrl: '${keyVaultUri}secrets/redis-password', identity: identity.id }
  { name: 'minio-user', keyVaultUrl: '${keyVaultUri}secrets/minio-root-user', identity: identity.id }
  { name: 'minio-password', keyVaultUrl: '${keyVaultUri}secrets/minio-root-password', identity: identity.id }
]

var minioFqdn = minio.properties.configuration.ingress.fqdn
var redisFqdn = redis.properties.configuration.ingress.fqdn

var sharedEnv = [
  { name: 'WA_PHONE_NUMBER_ID', value: waPhoneNumberId }
  { name: 'WA_ACCESS_TOKEN', secretRef: 'wa-access-token' }
  { name: 'WA_WEBHOOK_VERIFY_TOKEN', secretRef: 'wa-webhook-verify-token' }
  { name: 'WA_APP_SECRET', secretRef: 'wa-app-secret' }
  { name: 'DATABASE_URL', secretRef: 'database-url' }
  { name: 'REDIS_URL', value: 'redis://:$(REDIS_PASSWORD)@${redisFqdn}:6379/0' }
  { name: 'REDIS_PASSWORD', secretRef: 'redis-password' }
  { name: 'SARVAM_API_KEY', secretRef: 'sarvam-api-key' }
  { name: 'S3_BUCKET', value: 'kotha-khata-assets' }
  { name: 'S3_ENDPOINT_URL', value: 'https://${minioFqdn}' }
  { name: 'AWS_ACCESS_KEY_ID', secretRef: 'minio-user' }
  { name: 'AWS_SECRET_ACCESS_KEY', secretRef: 'minio-password' }
  { name: 'AWS_REGION', value: 'us-east-1' }
  { name: 'USE_LOCAL_MODELS', value: 'false' }
  { name: 'DEBUG', value: 'false' }
]
// NOTE: REDIS_URL above embeds the literal token "$(REDIS_PASSWORD)" rather
// than a resolved value, because Bicep can't string-interpolate a Key-Vault
// -sourced secretRef at template-compile time. Container Apps does NOT
// expand $(VAR) inside another env var's `value` field the way a shell
// would. Treat this as a known gap: either (a) have the app read
// REDIS_PASSWORD and REDIS_HOST as separate env vars and build the URL in
// code (cleanest — a small settings.py change), or (b) set REDIS_URL as
// its own Key Vault secret (redis-url) built at deploy time once the
// redis FQDN is known, same pattern as database-url in
// deploy-ai-sathi.ps1. The .ps1 script does NOT have this problem since it
// resolves the FQDN and interpolates the real password in plain PowerShell
// before setting the env var. Fix this before relying on the Bicep path in
// production — flagged here rather than silently shipped as if it worked.

resource gateway 'Microsoft.App/containerApps@2023-11-02-preview' = {
  name: 'ai-sathi-gateway'
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
      secrets: sharedSecrets
    }
    template: {
      containers: [
        {
          name: 'gateway'
          image: gatewayImage
          resources: {
            cpu: json('0.5')
            memory: '1.0Gi'
          }
          env: sharedEnv
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
      }
    }
  }
  dependsOn: [
    kvRoleAssignment
    acrRoleAssignment
  ]
}

resource worker 'Microsoft.App/containerApps@2023-11-02-preview' = {
  name: 'ai-sathi-worker'
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
      registries: [
        {
          server: acrLoginServer
          identity: identity.id
        }
      ]
      secrets: sharedSecrets
    }
    template: {
      containers: [
        {
          name: 'worker'
          image: workerImage
          resources: {
            cpu: json('0.5')
            memory: '1.0Gi'
          }
          env: sharedEnv
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 2
      }
    }
  }
  dependsOn: [
    kvRoleAssignment
    acrRoleAssignment
  ]
}

output gatewayFqdn string = gateway.properties.configuration.ingress.fqdn
output minioFqdn string = minioFqdn
output identityId string = identity.id
