#! /usr/bin/python3
#once agent start, call api to register this host, do not directly manipulate database
import etcd
import yaml
import sys
import platform
from e3net.e3common.E3LOG import get_e3loger

e3log=get_e3loger('e3hostagent')
config_filepath='/etc/e3net/e3host.yaml'
etcd_client=None
def _load_config_profile(path):
    with open(path,'r') as stream:
        try:
            return yaml.load(stream)
        except:
            e3log.error('can not parse config file:%s'%(path))
            return None
def init_etcd_session(config):
    global etcd_client
    if 'etcd-ip' not in config:
        e3log.error('no etcd-ip in config file')
        return False
    etcd_ip=config['etcd-ip']
    etcd_port=2739
    if 'etcd-port' in config:
        etcd_port=config['etcd-port']
    try:
        etcd_client=etcd.Client(host=etcd_ip,port=etcd_port)
        return True
    except:
        return False
def etcd_get_hosts():
    lst=list()
    try:
        rc=etcd_client.read('/host')
        if rc.dir is not True:
            return lst 
    pass

def etcd_register_host(config):
    try:
        host=etcd_client.read('/host/%s'%(config['uuid']))
        #already existing,do not touch it
        if host.dir == True:
            return True
    except:
        pass

    try:
        etcd_client.write('/host/%s/hostname'%(config['uuid']),config['hostname'])
        etcd_client.write('/host/%s/my-ip'%(config['uuid']),config['my-ip'])
        etcd_client.write('/host/%s/mems'%(config['uuid']),config['mems'])
        for cpu in config['cpus']:
            etcd_client.write('/host/%s/cpus/%d/used'%(config['uuid'],cpu),0)
        return True
    except:
        return False


if __name__=='__main__':
    #imagine we already know the uuid of the host
    host_uuid='17ae3081-7353-41aa-aab8-7cd03797c2f9'
    config=_load_config_profile(config_filepath)
    config['uuid']=host_uuid
    config['hostname']=platform.node()
    print(config)
    print(init_etcd_session(config))
    print(etcd_register_host(config))
    pass
