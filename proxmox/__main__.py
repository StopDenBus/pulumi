"""A Python Pulumi program"""

import pulumi
import pulumi_proxmoxve as proxmox
import pulumi_random as random

from pulumi_proxmoxve import Provider
from pulumi_proxmoxve.ct import Container
from pulumi import Output, Config, ResourceOptions
from pulumi_tls import PrivateKey

def random_password(use_case: str) -> random.RandomPassword:
    password: random.RandomPassword = random.RandomPassword(use_case,
            length=16,
            special=True                             
        )
    return password

def create_container():
    containers: dict = get_pve_config("containers")
    exports: dict = { "containers": {} }
    provider_data: dict = get_pve_config(data_section="provider")
    pve_provider: Provider = get_pve_provider(provider_data)
    container: dict
    container: str
    for container in containers:
        
        root_password: random.RandomPassword = random_password(f"root_{container}")

        ssh_keys_stack_ref = pulumi.StackReference("malefitz/ssh-keys/infra")
        ssh_keys: Output = ssh_keys_stack_ref.get_output("ssh-keys")

        deployment_public_key = ssh_keys["deployment"]["public_key_openssh"]

        public_keys: list = [
            "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIE+m0RtKRNVwkLu+EP8i6yd2ID2qAi2oO2CokOggyYJJ michael@janicelnx",
            deployment_public_key,
        ]

        ct: Container = proxmox.ct.Container(container,
                node_name=containers[container]["node_name"],
                operating_system=proxmox.ct.ContainerOperatingSystemArgs(
                    template_file_id=containers[container]["template"]["id"],
                    type=containers[container]["template"]["type"],
                ),
                disk=proxmox.ct.ContainerDiskArgs(
                    datastore_id=containers[container]["disk"]["datastore"],
                    size=containers[container]["disk"]["size"],
                ),
                initialization=proxmox.ct.ContainerInitializationArgs(
                    dns=proxmox.ct.ContainerInitializationDnsArgs(
                        domain="gusek.info",
                        servers=["192.168.0.10"],
                    ),
                    hostname=container.replace("_", "-"),
                    ip_configs=[proxmox.ct.ContainerInitializationIpConfigArgs(
                        ipv4=proxmox.ct.ContainerInitializationIpConfigIpv4Args(
                            address=containers[container]["network"]["cidr"],
                            gateway=containers[container]["network"]["gateway"],
                        ),
                    )],
                    user_account=proxmox.ct.ContainerInitializationUserAccountArgs(
                        keys=public_keys,
                        password=root_password.result.apply(lambda result: result)
                    ),
                ),
                network_interfaces=[proxmox.ct.ContainerNetworkInterfaceArgs(
                    name=containers[container]["network"]["interface"],
                )],
                description=containers[container]["description"],
                cpu=proxmox.ct.ContainerCpuArgs(
                    cores=containers[container]["cpu"]["cores"],
                ),
                memory=proxmox.ct.ContainerMemoryArgs(
                    dedicated=containers[container]["memory"]["ram"],
                    swap=containers[container]["memory"]["swap"],
                ),
                console=proxmox.ct.ContainerConsoleArgs(
                    enabled=True,
                    tty_count=2,
                    type="tty",
                ),
                features=proxmox.ct.ContainerFeaturesArgs(nesting=True),
                unprivileged = True,
                opts=ResourceOptions(provider=pve_provider)
            )

        exports["containers"][container] = ct        

    return exports

def get_pve_config(data_section: str) -> Config:
    config: Config = pulumi.Config("data")
    data: dict = config.require_object("proxmox")
    return data.get(data_section)

def get_pve_provider(data: map) -> Provider:

    provider: Provider = proxmox.Provider('proxmoxve', 
        endpoint=data.get("endpoint"),
        api_token=data.get("token"),
    )

    return provider

# main
exports = create_container()
pulumi.export('proxmox', exports)

