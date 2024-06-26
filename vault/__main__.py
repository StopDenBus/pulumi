"""A Python Pulumi program"""

import json
import pulumi
import pulumi_random as random
import pulumi_vault as vault

def random_password(use_case: str) -> random.RandomPassword:
    password: random.RandomPassword = random.RandomPassword(use_case,
            length=16,
            special=True                             
        )
    return password

config = pulumi.Config("data")
data = config.require_object("vault")
mounts: dict = data.get("mounts")
secrets: dict = data.get("secrets")
exports: dict = { "mounts": {}, "secrets": {} }

for mount in mounts:
    exports["mounts"][mount] = vault.Mount(mount,
            path        = mount,
            type        = mounts[mount]["type"],
            description = mounts[mount]["description"]
        )

for secret in secrets:
    password = random_password(secret)

    exports["secrets"][secret] = vault.kv.SecretV2(secret,
            mount     = exports["mounts"][secrets[secret]["mount"]].path,
            name      = secrets[secret]["name"],
            data_json = pulumi.Output.json_dumps(
                {
                    "key": password.result,
                }
            )
        )
    
pulumi.export('vault', exports)
