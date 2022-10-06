# exl-vault-poc

To create an exemplary blueprint, please upload one from blueprints.zip file.  

## Blueprint packages
Package is used to install a target deployment (wrapped deployment) with one secret (blueprints package) or with list of secrets ( blueprint_multiple_secrets ) from Vault.
It consists of 3 phases:

 - _schedule the removal of secrets_ - just to be sure the newly created secrets will be removed even when the installation is unsuccessful
 - _obtain and save secrets_ - reads required secrets from the Vault and saves them temporarily in local Cloudify secrets
 - _execute install/uninstall workflow on deployment_ - during execution the secrets are available. Once the execution finishes, the secrets are safely removed.

Requirements of the blueprint:

 - local secrets (hidden for current user, created by secrets_user_name):
   - _vault_token_ - token to read from Vault
   - _vault_url_ - full URL and port of Vault (for example: "http://10.10.10.10:8200")
   - _secrets_user_name_ - name of user which is responsible for secret handling
   - _secrets_user_password_ - password of user which is responsible for secret handling
 - blueprint inputs:
   - _main_file_name_ - name of main blueprint in package (wrapped deployment)
   - _blueprint_archive_ - url to package (wrapped)
   - _mount_point_ - Vault path to mounted secrets (path must be enabled), it can be [aws path](https://www.vaultproject.io/docs/secrets/aws), [postgresql path](https://www.vaultproject.io/docs/secrets/databases/postgresql) or [the simplest secrets path](https://www.vaultproject.io/docs/secrets)
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

### Create deployment blueprint_multiple_secrets
```
curl -X PUT \
    --header "Tenant: default_tenant" \
    --header "Content-Type: application/json" \
    -u admin:admin \
    -d '{"blueprint_id": "main_blueprint", "inputs": {"main_file_name": "blueprint_child.yaml", "blueprint_archive": "https://url/to_child/archive/master.zip", "secret_keys": ["vaultkey1", "vaultkey2"] }, "visibility": "tenant", "site_name": "LONDON", "labels": [{"customer": "EXL1"}]}' \
    "http://localhost/api/v3.1/deployments/my_deployment1?_include=id"
```
### Install/uninstall
```
curl -X POST \
    --header "Tenant: default_tenant" \
    --header "Content-Type: application/json" \
    -u admin:admin \
    -d '{"deployment_id":"my_deployment1", "workflow_id":"install"}' \
    "http://localhost/api/v3.1/deployments/my_deployment1?_include=id"
```

### Temporary API token and Vault Policies
The main [cloudify-vault-plugin](https://github.com/ahmadiesa-abu/cloudify-vault-plugin/tree/exl_changes) nodes are:
- cloudify.nodes.vault.Secret
- cloudify.nodes.vault.Bunch_secrets

They are used to create or read a single or multiple Vault secrets at once (accordingly).  
Each node type has information about the resource in its _resource_config_ property of _cloudify.types.vault.Secret_ type.  
For more details please refer to the [plugin.yaml](https://github.com/ahmadiesa-abu/cloudify-vault-plugin/blob/exl_changes/plugin.yaml) file of the plugin.  
_use_external_resource_ property provides information if secrets already exist in the Vault (if `False`, plugin will create the secret).  
Object _client_config_ deliver information about Vault server and its connection. It is specified in _cloudify.types.vault.ClientConfig_ data type.
Object _executor_user_config_ provides information about user which is responsible for secrets management (creation, deleting, etc. - only this user can view the value of secrets). The object is described in _cloudify.types.vault.ExecutorConfig_.

If plugin should use a [local API token](https://www.vaultproject.io/api-docs/auth/token) for secrets reading, the value of _use_api_client_token_ must be `True` (by default it is `False`). When _use_api_client_token_ is `True`, the master token specified in _cloudify.types.vault.ClientConfig_ is used to generate a local API token with ttl equal to 90s.  
You can also specify the vault API token policies under _client_token_policies_ which is a list object.
By default, plugin use _secret_ policy to create API token and the [policy](https://www.vaultproject.io/docs/concepts/policies) must contains correct priviliges regarding to used path.  
Example:
```
path "secret*" {
  capabilities = [ "create", "read", "update", "delete", "list", "sudo" ]
}

path "secret/data/foo" {
  capabilities = ["read"]
}
```

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
   - _secrets_user_name_ - name of user which is responsible for secret handling
   - _secrets_user_password_ - password of user which is responsible for secret handling
 - workflow inputs:
    - deployment_id
    - workflow_id
    - secrets_node_ids
    - secrets_node_instance_ids
    - workflow_node_ids
    - workflow_node_instance_ids
    - workflow_params 

An example of how to use the workflow:
```
curl -L -X POST 'http://localhost/api/v3.1/executions?_include=id' \
-H 'Tenant: default_tenant' \
-H 'Content-Type: application/json' \
-u admin:admin \
--data-raw '{
    "deployment_id": "de6ded0b-546f-4584-9ae4-bd081cd17073",
    "workflow_id": "execute_with_secrets",
    "parameters": {
        "workflow_id": "restart",
        "secrets_node_ids": ["install_vault_secrets"],
        "workflow_node_ids": ["deployment"],
        "workflow_params": {
            "run_by_dependency_order": false
        }
    }
}''
```
