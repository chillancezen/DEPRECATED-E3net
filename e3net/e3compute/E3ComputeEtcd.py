#! /usr/bin/python3

import etcd
from e3net.e3storage.ZFSWrapper import *

etcd_client=None


def etcd_key_to_key(etcd_key):
    return etcd_key.split('/')[-1]

def init_etcd_session(etcd_ip,etcd_port=2379):
    global etcd_client
    try:
        etcd_client=etcd.Client(host=etcd_ip,port=etcd_port)
        return True
    except:
        return False
def _etcd_set_key(key,value):
    try:
        etcd_client.write(key,value)
        return True
    except:
        return False
def _etcd_get_value(key):
    try:
        rc=etcd_client.read(key,recursive=False)
        return rc.value
    except:
        return None
def _etcd_get_children(key):
    try:
        ret=list()
        rc=etcd_client.read(key,recursive=False)
        if rc.dir is True:
            for c in rc.children:
                ret.append(c)
        return ret
    except:
        return list()

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
            etcd_client.write('/host/%s/cpus/%d/container_id'%(config['uuid'],cpu),'')
        etcd_client.write('/host/%s/disks'%(config['uuid']),zfs_free_size())
        return True
    except:
        return False
def etcd_get_free_memory(host_id):
    try:
        mem=int(_etcd_get_value('/host/%s/mems'%(host_id)))
        return mem
    except:
        return 0
def etcd_allocate_memory(host_id,mem_to_alloc):
    mem=int(_etcd_get_value('/host/%s/mems'%(host_id)))
    if mem < mem_to_alloc :
        return False
    free_mem=mem-mem_to_alloc
    if _etcd_set_key('/host/%s/mems'%(host_id),free_mem) is False:
        return False
    return True

def etcd_deallocate_memory(host_id,mem_to_dealloc):
    mem=int(_etcd_get_value('/host/%s/mems'%(host_id)))
    free_mem=mem+int(mem_to_dealloc)
    if _etcd_set_key('/host/%s/mems'%(host_id),free_mem) is False:
        return False
    return True

def etcd_get_free_disk(host_id):
    current=_etcd_get_value('/host/%s/disks'%(host_id))
    try:
        return float(current)
    except:
        return 0
def etcd_update_disk(host_id):
    size=float(zfs_free_size())
    if _etcd_set_key('/host/%s/disks'%(host_id),str(size)) is False:
        return False
    return True
def etcd_assign_container_cpu(host_id,container_id,cpu):
    current=_etcd_get_value('/host/%s/cpus/%d/container_id'%(host_id,cpu))
    if current is None:#cpu is not available at all
        return False
    #perhaps it's ready assigned before
    if current == container_id:
        return True
    if current != '':
        return False
    if _etcd_set_key('/host/%s/cpus/%d/container_id'%(host_id,cpu),container_id) is False:
        return False
    return True

def etcd_get_free_cpus(host_id):
    ret=list()
    lst=_etcd_get_children('/host/%s/cpus'%(host_id))
    for e in lst:
        current=_etcd_get_value('%s/container_id'%(e.key))
        if current != '':
            continue
        ret.append(int(etcd_key_to_key(e.key)))
    return ret

def etcd_get_cpus_by_container_id(host_id,container_id):
    ret=list()
    lst=_etcd_get_children('/host/%s/cpus'%(host_id))
    for e in lst:
        current=_etcd_get_value('%s/container_id'%(e.key))
        if current != container_id:
            continue
        ret.append(int(etcd_key_to_key(e.key)))
    return ret
def etcd_release_cpu(host_id,cpu):
    current=_etcd_get_value('/host/%s/cpus/%d/container_id'%(host_id,cpu))
    if current is None:
        return False
    if _etcd_set_key('/host/%s/cpus/%d/container_id'%(host_id,cpu),'') is False:
        return False
    return True
def etcd_allocate_cpus_for_container(host_id,container_id,num_of_cpu):
    # count previously allocated cpus for the container as allocated
    lst=etcd_get_cpus_by_container_id(host_id,container_id)
    num_of_cpu = num_of_cpu-len(lst)
    lst=etcd_get_free_cpus(host_id)
    if len(lst) < num_of_cpu:
        return False
    for cpu in lst[0:num_of_cpu]:
        if etcd_assign_container_cpu(host_id,container_id,cpu) is False:
            for cpu_another in lst[0:num_of_cpu]:
                etcd_release_cpu(host_id,cpu_another)
            return False
    return True 
    
def etcd_release_cpus_of_container(host_id,container_id):
    lst=etcd_get_cpus_by_container_id(host_id,container_id)
    for cpu in lst:
        etcd_release_cpu(host_id,cpu)

def etcd_unregister_host(host):
    try:
        etcd_client.delete('/host/%s'%(host),recursive=True)
        return True
    except:
        return False

