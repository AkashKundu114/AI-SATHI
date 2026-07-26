param name string
param location string
param adminUser string
@secure()
param adminPassword string
param databaseName string = 'kothkori'

resource server 'Microsoft.DBforPostgreSQL/flexibleServers@2023-06-01-preview' = {
  name: name
  location: location
  sku: {
    name: 'Standard_B1ms'
    tier: 'Burstable'
  }
  properties: {
    version: '16'
    administratorLogin: adminUser
    administratorLoginPassword: adminPassword
    storage: {
      storageSizeGB: 32
    }
    backup: {
      backupRetentionDays: 7
      geoRedundantBackup: 'Disabled'
    }
    highAvailability: {
      mode: 'Disabled'
    }
  }
}

// Allows Azure services (Container Apps) to reach this server. This is the
// standard "0.0.0.0-0.0.0.0" Azure convention -- it does NOT open the
// server to the public internet without a password, but it is not
// private-network-isolated either. Fine for a pilot; add VNet integration +
// a private endpoint before this holds data you can't afford to leak.
resource allowAzureServices 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2023-06-01-preview' = {
  parent: server
  name: 'AllowAllAzureServices'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

resource pgvectorExtension 'Microsoft.DBforPostgreSQL/flexibleServers/configurations@2023-06-01-preview' = {
  parent: server
  name: 'azure.extensions'
  properties: {
    value: 'VECTOR'
    source: 'user-override'
  }
}

resource database 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2023-06-01-preview' = {
  parent: server
  name: databaseName
  dependsOn: [
    pgvectorExtension
  ]
}

output fqdn string = server.properties.fullyQualifiedDomainName
output databaseName string = databaseName
