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
