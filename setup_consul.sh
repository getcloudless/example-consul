#!/bin/bash

{% if cloudless_test_framework_ssh_key %}
adduser "{{ cloudless_test_framework_ssh_username }}" --disabled-password --gecos "Cloudless Test User"
echo "{{ cloudless_test_framework_ssh_username }} ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
mkdir /home/{{ cloudless_test_framework_ssh_username }}/.ssh/
echo "{{ cloudless_test_framework_ssh_key }}" >> /home/{{ cloudless_test_framework_ssh_username }}/.ssh/authorized_keys
{% endif %}

# https://urbanautomaton.com/blog/2014/09/09/redirecting-bash-script-output-to-syslog/
exec 1> >(logger -s -t "$(basename "$0")") 2>&1

# Version of Consul to install
CONSUL_VERSION="1.5.3"

# Get Hashicorp's GPG Key
gpg --keyserver keys.gnupg.net --recv-key 0x51852D87348FFC4C

# Bail out if we can't verify Hashicorp's Key with the fingerprint we know about
if gpg --fingerprint 0x51852D87348FFC4C | grep "91A6 E7F8 5D05 C656 30BE  F189 5185 2D87 348F FC4C"; then
    echo "Could not verify fingerprint..."
    gpg --fingerprint 0x51852D87348FFC4C
fi

# Download the binary and signature files.
curl -Os https://releases.hashicorp.com/consul/${CONSUL_VERSION}/consul_${CONSUL_VERSION}_linux_amd64.zip
curl -Os https://releases.hashicorp.com/consul/${CONSUL_VERSION}/consul_${CONSUL_VERSION}_SHA256SUMS
curl -Os https://releases.hashicorp.com/consul/${CONSUL_VERSION}/consul_${CONSUL_VERSION}_SHA256SUMS.sig

# Verify the signature file is untampered.
gpg --verify consul_${CONSUL_VERSION}_SHA256SUMS.sig consul_${CONSUL_VERSION}_SHA256SUMS

# Verify the SHASUM matches the binary.
shasum -a 256 -c consul_${CONSUL_VERSION}_SHA256SUMS

# Unzip and install the binary
sudo apt-get -y install unzip
unzip consul_${CONSUL_VERSION}_linux_amd64.zip
mkdir -p /opt/consul/
mv consul /opt/consul/consul

# Create Data Directory
mkdir -p /var/consul/data/

# Start consul
#
# Ideally this should be installed on the box as a real daemon, but this is an
# example of how to do everything in a startup script.
/opt/consul/consul agent -server -bootstrap-expect=1 -data-dir=/var/consul/data/ -client "0.0.0.0" &> /var/log/consul.log &
