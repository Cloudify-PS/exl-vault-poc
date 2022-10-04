# exl-vault-poc

To create an exemplary blueprint, please upload one from blueprints.zip file.  

## Blueprint packages
Package is used to install a target deployment (wrapped deployment) with one secret (blueprints package) or with list of secrets ( blueprint_multiple_secrets ) from Vault.
It consists of 3 phases:

 - _schedule the removal of secrets_ - just to be sure the newly created secrets will be removed even when the installation is unsuccessful
 - _obtain and save secrets_ - reads required secrets from the Vault and saves them temporarily in local Cloudify secrets
 - _execute install/uninstall workflow on deployment_ - during execution the secrets are available. Once the execution finishes, the secrets are safely removed.

Requirements of the blueprint:

 - local secrets:
   - _vault_token_ - token to read from Vault
   - _vault_url_ - full URL and port of Vault (for example: "http://10.10.10.10:8200")
 - Blueprint inputs:
   - _main_file_name_ - name of main blueprint in package (wrapped deployment)
   - _blueprint_archive_ - url to package (wrapped)
   - _secret_key_ - name of Vault secret to populate (only for blueprints)
   - _secret_keys_ - list of Vault secrets (only for blueprint_multiple_secrets)

An example of how to use the packages:

### Uploading:
```
curl -X PUT \
    --header "Tenant: default_tenant" \
    --header "Content-Type: application/json" \
    -u admin:admin \
    "http://localhost/api/v3.1/blueprints/main_blueprint?application_file_name=blueprint.yaml&visibility=tenant&blueprint_archive_url=https://url/to/archive/master.zip&labels=customer=EXL1"
```

### Create deployment blueprint
```
curl -X PUT \
    --header "Tenant: default_tenant" \
    --header "Content-Type: application/json" \
    -u admin:admin \
    -d '{"blueprint_id": "main_blueprint", "inputs": {"main_file_name": "blueprint_child.yaml", "blueprint_archive": "https://url/to_child/archive/master.zip", "secret_key": "vaultkey1" }, "visibility": "tenant", "site_name": "LONDON", "labels": [{"customer": "EXL1"}]}' \
    "http://localhost/api/v3.1/deployments/my_deployment1?_include=id"
```

### Create deployment  blueprint_multiple_secrets
```
curl -X PUT \
    --header "Tenant: default_tenant" \
    --header "Content-Type: application/json" \
    -u admin:admin \
    -d '{"blueprint_id": "main_blueprint", "inputs": {"main_file_name": "blueprint_child.yaml", "blueprint_archive": "https://url/to_child/archive/master.zip", "secret_keys": ["vaultkey1", "vaultkey2"] }, "visibility": "tenant", "site_name": "LONDON", "labels": [{"customer": "EXL1"}]}' \
    "http://localhost/api/v3.1/deployments/my_deployment1?_include=id"
```
### Temporary API token and Vault Policies
The packages contains properties part for nodes cloudify.nodes.vault.Bunch_secrets/cloudify.nodes.vault.Secret which has information about client_config and resources.

```
    properties:
      client_config: *vault_config
      use_external_resource: True
      resource_config: {get_input: secret_keys}
```
use_external_resource provides information if secrets are already existed (if False, plugin will create the secret) and about resource_config which is cloudify.types.vault.Secret object.
```
  cloudify.types.vault.Secret:
    properties:
      secret_key:
        description: Secret Key [Path]
        type: string
        default: ''
      secret_value:
        description: Secret Value
        default: {}
      create_secret:
        description: >
          A condition whether to store the secret value in Cloudify
          Manager secrets.
        type: boolean
        default: false
      secret_name:
        description: >
          Name of the secret created in Cloudify secrets. Used when
          create_secret flag is enabled.
        type: string
        default: ''
      mount_point:
        description: >
          A mount_point parameter that can be used to address the KvV1
          secret engine under a custom mount path. The full path of the
          secret inside Vault.
        type: string
        default: 'secret'
```

Object client_config provides information about Vault server and is specified in dsl_definitions of plugin.

```
dsl_definitions:

  client_config: &client_config
    client_config:
      type: cloudify.types.vault.ClientConfig
      description: Your Vault client configuration.
      required: false
    use_api_client_token:
      type: boolean
      description: >
        Auto-generate and use a new API Client token with adequate
        policies for managing Vault resources. If set to false, plugin
        will use the Master Token for all operations.
      required: false
      default: false
    client_token_policies:
      type: list
      description: >
        Valid only when `use_api_client_token` is enabled. A list of
        policies to be granted for new API Client token.
      required: false
      default: [secret]
    
```
If plugin should use local API token (https://www.vaultproject.io/api-docs/auth/token) for secrets reading, the value of use_api_client_token must be True (by default is False). When use_api_client_token is True, master token specified in cloudify.types.vault.ClientConfig is used for generate local API token with ttl equal to 90s. You can also specify the vault API token policies under client_token_policies which is a list object.
By default, plugin use _secret_ policy to create API token and the policy must contains correct priviliges regarding to used path
Example:
```
path "secret*" {
  capabilities = [ "create", "read", "update", "delete", "list", "sudo" ]
}

path "secret/data/foo" {
  capabilities = ["read"]
}
```
(more information about policy here: https://www.vaultproject.io/docs/concepts/policies)

## Custom workflows
The examples of running workflows using Cloudify Manager's API calls are implemented in the Postman Collection: https://www.getpostman.com/collections/e76f72a2a89d598509ac

### execute_with_secrets

Workflow is used to execute any other workflows on a target deployment (wrapped deployment).  
It consists of 3 phases:
 - _schedule the removal of secrets_ - just to be sure the newly created secrets will be removed even when the installation is unsuccessful
 - _obtain and save secrets_ - reads required secrets from the Vault and saves them temporarily in local Cloudify secrets
 - _execute target workflow on deployment_ - during the target workflow execution the secrets are available. Once the execution finishes, the secrets are safely removed.

Requirements of the workflow:
 - local secrets:
    - _vault_token_ - token to read from Vault
    - _vault_url_ - full URL and port of Vault (for example: "http://10.10.10.10:8200")
 - workflow inputs:
    - deployment_id
    - workflow_id
    - target workflow_id
    - target_deployment_id
    - secret_list
    - any other inputs required for the target workflow to operate

An example of how to use the workflow:
```
curl -L -X POST 'http://localhost/api/v3.1/executions?_include=id' \
-H 'Tenant: default_tenant' \
-H 'Content-Type: application/json' \
-u admin:admin \
--data-raw '{
    "deployment_id": "de6ded0b-546f-4584-9ae4-bd081cd17073",
    "workflow_id": "execute_with_secrets",
    "allow_custom_parameters": true,
    "parameters": {
        "workflow_id": "restart",
        "target_deployment_id": "hello_de6ded0b-546f-4584-9ae4-bd081cd17073",
        "secret_list": [
            {
                "secret_key": "hello"
            },
            {
                "secret_key": "hello2"
            }
        ],
        "run_by_dependency_order": false,
        "node_ids": ["MyResource"]
    }
}'
```

### remove_local_secrets

Leveraged also in _execute_with_secrets_, _remove_local_secrets_ workflow takes a list of secret names and removes them from the local Cloudify Manager's secret store.  
Requirements of the workflow:
 - local secrets:
    - _vault_token_ - token to read from Vault
    - _vault_url_ - full URL and port of Vault (for example: "http://10.10.10.10:8200")
 - workflow inputs:
    - secret_list - a list of secret names to be removed from local Secret Store

An example of how to use the workflow:
```
curl -L -X POST 'http://localhost/api/v3.1/executions?_include=id' \
-H 'Tenant: default_tenant' \
-H 'Content-Type: application/json' \
-u admin:admin \
--data-raw '{
    "deployment_id": "d7f16305-05b3-4976-aa59-b3195abcbc3e",
    "workflow_id": "remove_local_secrets",
    "parameters": {
        "secret_list": [
            "hello-2d7741b2-4789-487e-bd06-74464f85bfa0",
            "hello2-2d7741b2-4789-487e-bd06-74464f85bfa0"
        ]
    }
}'
```
