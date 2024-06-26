"""A Python Pulumi program"""

import pulumi
import pulumi_command as command

from pulumi import Output, ResourceOptions
from pulumi_command.remote import Command, ConnectionArgs

def install_vault():
    ssh_keys_stack_ref = pulumi.StackReference("malefitz/ssh-keys/infra")
    ssh_keys: Output = ssh_keys_stack_ref.get_output("ssh-keys")

    deployment_private_key = ssh_keys["deployment"]["private_key_openssh"]

    connection: ConnectionArgs = command.remote.ConnectionArgs(
        host="192.168.0.3",
        private_key=deployment_private_key,
        user="root",
    )

    exports: dict = { }

    exports["install_gpg"] = command.remote.Command("install_gpg",
            connection = connection,
            create     = "/usr/bin/apt install -y gpg",
            delete     = "/usr/bin/apt remove -y gpg",
        )

    exports["apt_configuration_file"] = command.remote.Command("apt_configuration_file",
            connection = connection,
            create     = "echo \"deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main\" > /etc/apt/sources.list.d/hashicorp.list",
            delete     = "rm /etc/apt/sources.list.d/hashicorp.list",
            opts       = ResourceOptions(depends_on=[exports["install_gpg"]])
        )
        
    exports["install_vault_gpg_key"] = command.remote.Command("install_vault_gpg_key",
            connection = connection,
            create     = "/usr/bin/wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg",
            delete     = "rm /usr/share/keyrings/hashicorp-archive-keyring.gpg",
            opts       = ResourceOptions(depends_on=[exports["install_gpg"]]),
        )
    
    exports["install_vault"] = command.remote.Command("install_vault",
            connection = connection,
            create     = "/usr/bin/apt update > /dev/null 2>&1 && apt install -y vault",
            delete     = "/usr/bin/apt remove -y vault",
            opts       = ResourceOptions(depends_on=[exports["install_vault_gpg_key"]]),
        )    

    return exports


# main
exports = install_vault()
pulumi.export('install-vault', exports)