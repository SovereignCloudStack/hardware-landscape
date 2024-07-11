#!/usr/bin/env python3

import os
import subprocess
import sys
import re
import textwrap

basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
subject = "/C=DE/ST=Berlin/L=Berlin/O=OSBA e.V./OU=Fake CA"
password = "dummypassword"
server_cnf = "/tmp/landscape_server_cert.cnf"

os.chdir(basedir)


def create_cert(target_path, key):
    domain = None
    with open("environments/kolla/configuration.yml") as f:
        for line in f:
            if key in line:
                domain = line.split()[1]
                break

    if not domain:
        sys.exit(f"Domain not found for key {key}")

    print(f"CREATE SERVER CERT: {key} -> {domain}")
    try:
        subprocess.run(["openssl", "genpkey", "-algorithm", "RSA", "-out", f"secrets/{key}.key", "-pkeyopt",
                        "rsa_keygen_bits:4096"], check=True)
        subprocess.run(["openssl", "req", "-new", "-key", f"secrets/{key}.key", "-out", f"secrets/{key}.csr", "-subj",
                        f"{subject}/CN={domain}"], check=True)
        subprocess.run([
            "openssl", "x509", "-req", "-in", f"secrets/{key}.csr", "-CA", "secrets/ca.crt", "-CAkey", "secrets/ca.key",
            "-CAcreateserial",
            "-out", f"secrets/{key}.crt", "-days", "730", "-sha256", "-extfile", "secrets/server_cert.cnf",
            "-extensions", "v3_req",
            "-passin", f"pass:{password}"
        ], check=True)

        with open(target_path, 'w') as f_out:
            with open(f"secrets/{key}.key") as f_key:
                f_out.write(f_key.read())
            with open(f"secrets/{key}.crt") as f_crt:
                f_out.write(f_crt.read())

        subprocess.run(["openssl", "x509", "-in", target_path, "-text", "-noout"], check=True)
        subprocess.run(["make", "ansible_vault_edit", f"FILE={target_path}"], check=True)
        subprocess.run(["git", "add", target_path], check=True)
    except subprocess.CalledProcessError as e:
        sys.exit(e)

def create_ca():
    print("CREATE CA CERT")
    try:
        subprocess.run([
            "openssl", "genpkey", "-algorithm", "RSA", "-out", "secrets/ca.key", "-aes256",
            "-pass", f"pass:{password}", "-pkeyopt", "rsa_keygen_bits:4096"
        ], check=True)

        subprocess.run([
            "openssl", "req", "-x509", "-new", "-key", "secrets/ca.key", "-sha256", "-days", "3650",
            "-out", "secrets/ca.crt", "-passin", f"pass:{password}", "-subj", subject
        ], check=True)

        with open(server_cnf, 'w') as f:
            f.write(textwrap.dedent("""
                [ v3_req ]
                basicConstraints = CA:FALSE
                keyUsage = nonRepudiation, digitalSignature, keyEncipherment
                extendedKeyUsage = serverAuth
                subjectAltName = @alt_names

                [ alt_names ]
                DNS.1 = your_common_name
                """)
            )

        with open("inventory/group_vars/generic/99_ca.yml", 'w') as f:
            f.write(tef"""
manager_environment_extra:
  REQUESTS_CA_BUNDLE: /etc/ssl/certs/ca-certificates.crt
kolla_copy_ca_into_containers: "yes"
openstack_cacert: /etc/ssl/certs/ca-certificates.crt
certificates_ca:
  - name: custom.crt
    certificate: |
""")
            with open("secrets/ca.crt") as f_crt:
                for line in f_crt:
                    f.write(f"       {line}")

        subprocess.run(["make", "ansible_vault_edit", "FILE=inventory/group_vars/generic/99_ca.yml"], check=True)
        subprocess.run(["git", "add", "inventory/group_vars/generic/99_ca.yml"], check=True)
    except subprocess.CalledProcessError as e:
        sys.exit(e)


create_ca()
create_cert("environments/kolla/certificates/haproxy.pem", "kolla_external_fqdn")
create_cert("environments/kolla/certificates/haproxy-internal.pem", "kolla_internal_fqdn")
print("SUCCESS")
