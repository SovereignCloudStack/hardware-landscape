#!/bin/bash

# This is a hacky solution to add  or remove custom certificates


basedir="$(readlink -f $(dirname $0)/../)"
subject="/C=DE/ST=Berlin/L=Berlin/O=OSBA e.V./OU=Fake CA"
password="dummypassword"

echo cd $basedir
cd $basedir  || exit 1

modify_yaml(){
   local include_file="$1"
   local file="$2"

   target_file_new="$(mktemp /tmp/new-file-XXXXX)"
   sed -i '/# BEGIN: TLS/,/# END: TLS/d' $file
   (
      cat "$file"
      echo "# BEGIN: TLS"
      cat "$include_file"
      echo "# END: TLS"
   ) >> $target_file_new
   mv $target_file_new $file
   chmod 660 $file
   git diff $file|cat
}

create_cert(){
   local target_path="${1?}"
   local key="${2?}"
   local domain="$(awk -v "type=^${key}" '$0 ~ type{print $2}' environments/kolla/configuration.yml)"
   echo -e "CREATE SERVER CERT: $key -> $domain"
   set -xe
   openssl genpkey -algorithm RSA -out secrets/${key}.key -pkeyopt rsa_keygen_bits:4096
   openssl req -new -key secrets/${key}.key -out secrets/${key}.csr \
      -subj "${subject}/CN=${domain}"
   sed "~s,your_common_name,$domain," ${server_cnf} > ${server_cnf}.new

   openssl x509 -req -in secrets/${key}.csr -CA secrets/ca.crt -CAkey secrets/ca.key -CAcreateserial \
      -out secrets/${key}.crt -days 732 -sha256 \
      -extfile ${server_cnf}.new -extensions v3_req -passin pass:${password}
   cat secrets/${key}.key secrets/${key}.crt > $target_path
   openssl x509 -in $target_path -text -noout|head -20
   make ansible_vault_edit FILE=$target_path
   chmod 660 $target_path
   git add $target_path
   set +xe
}

mk_server_cnf() {
   server_cnf="$(mktemp /tmp/server_cert-XXXXX.cnf)"
   cat > $server_cnf << 'EOF'
[ v3_req ]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[ alt_names ]
DNS.1 = your_common_name
EOF
   #sed "~s,your_common_name,$domain," ${server_cnf} > ${server_cnf}.new
}

if [ "$1" = "add" ];then
   #create_ca
   mk_server_cnf
   chmod 770 environments/kolla/certificates/
   create_cert environments/kolla/certificates/haproxy.pem kolla_external_fqdn
   create_cert environments/kolla/certificates/haproxy-internal.pem kolla_internal_fqdn
   echo "SUCCESS"
elif [ "$1" = "remove" ];then
   set -ex
   sed -i '/# BEGIN: TLS/,/# END: TLS/d' \
      environments/configuration.yml \
      environments/manager/configuration.yml \
      environments/kolla/configuration.yml
   for filename in environments/kolla/certificates/haproxy.pem \
      environments/kolla/certificates/haproxy-internal.pem \
      environments/kolla/certificates/ca.crt
   do
      if [ -f "$filename" ];then
         git rm -f "$filename"
      fi
   done
   echo "SUCCESS"
else
   echo "$0 add|remove"
fi
