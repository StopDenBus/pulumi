"""A Python Pulumi program"""

import pulumi
import pulumi_tls as tls

def generate_keys():
    config = pulumi.Config("data")
    data = config.require_object("ssh-keys")
    use_cases: dict = data.get("use_cases")
    exports: dict = { }

    for use_case in use_cases:
        exports[use_case] = tls.PrivateKey(use_case,
            algorithm=use_cases[use_case]['algorithm'],
            ecdsa_curve=use_cases[use_case]['ecdsa_curve'] if 'ecdsa_curve' in use_cases[use_case] else None,
            rsa_bits=use_cases[use_case]['rsa_bits'] if 'rsa_bits' in use_cases[use_case] else None,
        )

    return exports
    

exports = generate_keys()
pulumi.export('ssh-keys', exports)
