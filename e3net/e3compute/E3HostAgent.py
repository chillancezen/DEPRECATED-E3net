#! /usr/bin/python3
#once agent start, call api to register this host, do not directly manipulate database
import os
import etcd
import yaml
import sys
import platform
import wget
from e3net.e3common.E3config import *
from e3net.e3common.E3LOG import get_e3loger
from e3net.e3storage.ZFSWrapper import *

e3log=get_e3loger('e3hostagent')
config_filepath='/etc/e3net/e3host.yaml'
etcd_client=None

#make sure image directory exist
make_sure_dir_exist(image_host_dir)


def _etc_set_key(key,value):
    try:
        etcd_client.write(key,value)
        return True
    except:
        return False

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
        for host in rc.children:
            if host.dir is not True:
                continue
            if host.key[5] != '/':
                continue
            lst.append(host.key[6:])
    except:
        pass
    return lst

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
        etcd_client.write('/host/%s/disks'%(config['uuid']),zfs_free_size())
        return True
    except:
        return False
    
def etcd_unregister_host(host):
    try:
        etcd_client.delete('/host/%s'%(host),recursive=True)
        return True
    except:
        return False

def pull_image(image_name,host,port=5070,force_pull=False):
    url='http://%s:%d/%s'%(host,port,image_name)
    local_file='%s/%s'%(image_host_dir,image_name)
    def _null_bar_callback(current, total, width=80):
        return None
    if force_pull:
        try:
            os.remove(local_file)
        except:
            pass
    try:
        if os.path.isfile(local_file):
            return True
        wget.download(url=url,out=local_file,bar=_null_bar_callback)
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
    print(etcd_get_hosts())
    print(etcd_unregister_host(host_uuid+''))
    print(pull_image('mycentos7.image','127.0.0.1',force_pull=True))
    pass
