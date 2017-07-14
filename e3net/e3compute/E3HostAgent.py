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
from minio import Minio
from minio.error import ResponseError
import hashlib
import tarfile
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
'''
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
'''

def pull_image(image_name,host,port=9000,key='e3net',passwd='e3credentials',force_pull=False):
    '''
    this version use minio as the backed object storage,
    it's still convenient and even greater than what I imagined before
    '''
    bucket_name='images'
    object_name=image_name
    local_file='%s/%s'%(image_host_dir,image_name)

    if force_pull:
        try:
            os.remove(local_file)
        except:
            pass
    try:
        if os.path.isfile(local_file):
            return True
        client=Minio('%s:%d'%(host,port),
                    access_key=key,
                    secret_key=passwd,
                    secure=False)
        client.fget_object(bucket_name,object_name,local_file)
        return True
    except:
        return False

def validate_image(image_name,sha1_sum):
    '''
    use sha1 instead of MD5
    ''' 
    local_file='%s/%s'%(image_host_dir,image_name)
    try:
        sha1=hashlib.sha1()
        with open(local_file,'rb') as f:
            for chunk in iter(lambda:f.read(4096),b''):
                sha1.update(chunk)
        if sha1.hexdigest() != sha1_sum:
            return False
        return True 
    except:
        return False

def extract_image(image_name,path):
    '''
    on the premise that path is already ready
    '''
    local_file='%s/%s'%(image_host_dir,image_name)
    try:
        with tarfile.open(local_file) as tar:
            tar.extractall(path=path)
        return True
    except:
        return False
def extract_image_to_cotainer(image_name,container_id):
    container_dir='%s/%s'%(lxc_runtime_dir,container_id) 
    return extract_image(image_name,container_dir)

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
    print(pull_image('centos7.lxc.vnf.image','127.0.0.1',key='e3net',force_pull=False))
    print(validate_image('centos7.lxc.vnf.image','af18f2920a4e725cabd0e25e9af3c910b209b69f'))
    #print(extract_image('mycentos7.image','/tmp'))
    print(extract_image_to_cotainer('centos7.lxc.vnf.image','41ef25d2-1f38-43e7-a220-4c4b5350d1e0'))
