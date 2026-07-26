param name string
param location string
param fileShareName string = 'minio-data'
param fileShareQuotaGb int = 20

resource storage 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: name
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Cool'
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
  }
}

resource fileServices 'Microsoft.Storage/storageAccounts/fileServices@2023-01-01' = {
  parent: storage
  name: 'default'
}

resource share 'Microsoft.Storage/storageAccounts/fileServices/shares@2023-01-01' = {
  parent: fileServices
  name: fileShareName
  properties: {
    shareQuota: fileShareQuotaGb
  }
}

output accountName string = storage.name
output fileShareName string = fileShareName
#disable-next-line outputs-should-not-contain-secrets
output accountKey string = storage.listKeys().keys[0].value
