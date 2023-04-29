#!/bin/sh
#ansible-galaxy collection install community.libvirt
ssh-keygen -f /home/nuclearcat/.ssh/known_hosts -R 192.168.122.250
ansible-playbook playbook.yaml -i inventory/hosts


