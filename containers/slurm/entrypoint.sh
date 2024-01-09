#!/bin/bash

setup_hosts() {
  # add host name
  echo "127.0.0.1	$(hostname)" >> /etc/hosts
}

setup_mysql() {
  # create home directory for mysql user
  usermod -d /var/lib/mysql/ mysql
  # fix permission of mysql folder
  chmod -R 755 /var/run/mysqld
  # start service
  service mysql start 
  # create database and set permissions
  mysql -u root -e " \
    create user 'slurm'@'$(hostname)' identified by 'password'; \
    grant all on slurm_acct_db.* TO 'slurm'@'$(hostname)'; \
    create database slurm_acct_db; \
    flush privileges;"
}

slurm_config() {
  # update configuration files for hostname, cpu and memory information
  sed -i "s/<<HOSTNAME>>/$(hostname)/" /etc/slurm/slurm.conf
  sed -i "s/<<CPU>>/$(nproc)/" /etc/slurm/slurm.conf
  sed -i "s/<<MEMORY>>/$(if [[ "$(slurmd -C)" =~ RealMemory=([0-9]+) ]]; then echo "${BASH_REMATCH[1]}"; else exit 100; fi)/" /etc/slurm/slurm.conf
  sed -i "s/<<HOSTNAME>>/$(hostname)/" /etc/slurm/slurmdbd.conf
  # fix permissions
  chmod 600 /etc/slurm/slurmdbd.conf
  chown slurm:slurm /etc/slurm/slurmdbd.conf
  chmod 640 /etc/slurm/slurm.conf
  chown slurm:slurm /etc/slurm/slurm.conf
  # create directory for slurm controller
  mkdir -p /var/spool/slurmctld
  chown slurm:slurm /var/spool/slurmctld
}

slurm_add_user() {
  sacctmgr -Q -i add cluster mycluster
  sacctmgr -Q -i add account default description "Default account" Organization=Regular
  sacctmgr -Q -i create user name=ufs account=default
}

slurm_all_restart() {
  service munge restart
  service slurmdbd restart
  service slurmd restart
  service slurmctld restart
}

# call functions with sudo rights
setup_hosts
setup_mysql
slurm_config
slurm_all_restart

exec "$@"
