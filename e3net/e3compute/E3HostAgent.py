#! /usr/bin/python3
#once agent start, call api to register this host, do not directly manipulate database
import os
import yaml
import sys
import platform
import wget
import ast
import lxc
from e3net.e3common.E3config import *
from e3net.e3common.E3LOG import get_e3loger
from e3net.e3common.E3CFG import get_e3config
from e3net.e3storage.ZFSWrapper import *
from e3net.e3common.E3MQ import E3MQClient
from e3net.e3compute.E3ComputeEtcd import *
from minio import Minio
from minio.error import ResponseError
import hashlib
import tarfile
host_uuid=None
e3log=get_e3loger('e3hostagent')
e3cfg=get_e3config('e3host')
config_filepath='/etc/e3net/e3host.yaml'
#etcd_client=None
mq_scheduler_another=E3MQClient(queue_name='e3-scheduler-another-mq',user='e3net',passwd='e3credentials')
#make sure image directory exist
make_sure_dir_exist(image_host_dir)

'''
def _etc_set_key(key,value):
    try:
        etcd_client.write(key,value)
        return True
    except:
        return False

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
            def is_within_directory(directory, target):
                
                abs_directory = os.path.abspath(directory)
                abs_target = os.path.abspath(target)
            
                prefix = os.path.commonprefix([abs_directory, abs_target])
                
                return prefix == abs_directory
            
            def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
            
                for member in tar.getmembers():
                    member_path = os.path.join(path, member.name)
                    if not is_within_directory(path, member_path):
                        raise Exception("Attempted Path Traversal in Tar File")
            
                tar.extractall(path, members, numeric_owner) 
                
            
            safe_extract(tar, path=path)
        return True
    except:
        return False
def extract_image_to_cotainer(image_name,container_id):
    container_dir='%s/%s'%(lxc_runtime_dir,container_id) 
    return extract_image(image_name,container_dir)


def _initialize_container(param):
    def _cpu_list_to_string(lst):
        cpu_str=None
        for cpu in lst:
            if cpu_str==None:
                cpu_str=str(cpu)
            else:
                cpu_str=cpu_str+','+str(cpu)
        return cpu_str
    container=param['container']
    flavor=param['flavor']
    try:
        c=lxc.Container(container['id'])
        c.set_config_item(key='lxc.rootfs',value='%s/%s/rootfs'%(lxc_runtime_dir,container['id']))
        c.set_config_item(key='lxc.utsname',value=container['name'])
        cpu_lst=etcd_get_cpus_by_container_id(host_uuid,container['id'])
        c.set_config_item(key='lxc.cgroup.cpuset.cpus',value=_cpu_list_to_string(cpu_lst)) 
        c.set_config_item(key='lxc.cgroup.memory.limit_in_bytes',value='%sM'%(flavor['mem']))   
        c.save_config()
        return True
    except:
        return False 
    pass


def _exist_container(container_id):
    try:
        c=lxc.Container(container_id)
        return c.defined
    except:
        return False
def _notify_scheduler(body):
    msg=dict()
    msg['action']='notify'
    msg['body']=body
    return mq_scheduler_another.enqueue_message(msg=str(msg))

def notify_scheduler_boot_succeess(container_id):
    body=dict()
    body['prior_action']='boot'
    body['status']='OK'
    body['container_id']=container_id
    return _notify_scheduler(body)

def notify_scheduler_boot_failure(container_id,error_msg):
    body=dict()
    body['prior_action']='boot'
    body['status']='FAIL'
    body['msg']=error_msg
    body['container_id']=container_id
    return _notify_scheduler(body)

def boot_container_instance(data):
    try:
        param=ast.literal_eval(data)
    except:
        return
    if 'container' not in param \
        or 'flavor' not in param  \
        or 'image' not in param :
        e3log.error('incomplete parameters in booting container')
        return 
    container=param['container']
    flavor=param['flavor']
    image=param['image']
    #0 check whether container exists
    if _exist_container(container['id']):
        e3log.warn('container:%s alrady exists'%(container['id']))
        return
    #1 mount zfs for container
    if float(zfs_free_size()) < float(flavor['disk']):
        e3log.error('host has no enough disk space(needed:%s quota:%s) for container(id:%s)'%(flavor['disk'],zfs_free_size(),container['id']))
        notify_scheduler_boot_failure(container['id'],'no enough disk space for continer')
        return
    if not zfs_exist_fs(container['id']):
        if not zfs_create_fs(container['id'],flavor['disk']):
            e3log.error('can not create zfs for container(id:%s)'%(container['id']))
            notify_scheduler_boot_failure(container['id'],'creating zfs backed filesystem for container(id:%s)'%(container['id']))
            return
    etcd_update_disk(host_uuid) 
    e3log.info('zfs backed filesystem is ready for cotainer(id:%s name:%s)'%(container['id'],container['name']))
    #2 pull and validate images and then extract image to mounted fs
    rc=pull_image(image_name=image['name'],
                    host=e3cfg['image-server-ip'],
                    port=e3cfg['image-server-port'],
                    key=e3cfg['minio']['key'],
                    passwd=e3cfg['minio']['secret'],
                    force_pull=False)
    if rc == False:
        e3log.error('can not pull image(id:%s name:%s)'%(image['id'],image['name']))
        zfs_delete_fs(container['id'])
        etcd_update_disk(host_uuid)
        notify_scheduler_boot_failure(container['id'],'pulling image error')
        return
    rc=validate_image(image_name=image['name'],sha1_sum=image['sha1sum'])
    if rc == False:
            e3log.warn('invalid sha1um for image(name:%s),repull image'%(image['name']))
            rc=pull_image(image_name=image['name'],
                            host=e3cfg['image-server-ip'],
                            port=e3cfg['image-server-port'],
                            key=e3cfg['minio']['key'],
                            passwd=e3cfg['minio']['secret'],
                            force_pull=True)
            if rc==False or validate_image(image_name=image['name'],sha1_sum=image['sha1sum']) is False:
                e3log.error('can not prepare image(name:%s) for container(id:%s name:%s)'%(image['name'],container['id'],container['name']))
                zfs_delete_fs(container['id'])
                etcd_update_disk(host_uuid)
                notify_scheduler_boot_failure(container['id'],'pulling image errors')
                return
    e3log.info('image(id:%s name:%s) is ready for container(id:%s name:%s)'%(image['id'],image['name'],container['id'],container['name']))
    
    rc=extract_image_to_cotainer(image['name'],container['id'])
    if rc==False:
        e3log.error('extracting image(name:%s) to conatiner(id:%s)\'s filesystem fails'%(image['name'],container['id']))
        zfs_delete_fs(container['id'])
        etcd_update_disk(host_uuid)
        notify_scheduler_boot_failure(container['id'],'extracting image error')
        return
    e3log.info('image(id:%s name:%s) is extracted to container(id:%s name:%s)\'s filesystem'%(image['id'],image['name'],container['id'],container['name']))
    #3 initialize container options
    rc=_initialize_container(param)
    if rc is False:
        zfs_delete_fs(container['id'])
        etcd_update_disk(host_uuid)
        e3log.error('error occurs during initializing container(id:%s)\' config'%(container['id']))
        notify_scheduler_boot_failure(container['id'],'initailizing container config error')
        return False
    if notify_scheduler_boot_succeess(container['id']) is False:
        e3log.error('can not notify scheduler that container(id:%s) is ready'%(container['id']))
    return True

def _start_container(container_id):
    c=lxc.Container(container_id)
    if c.defined is False:
        return False
    if c.start() is False:
        return False
    if c.wait('RUNNING',timeout=max_seconds_to_wait_lxc_container_state) is False:
        return False
    return True
def _stop_container(container_id):
    c=lxc.Container(container_id)
    if c.defined is False:
        return False
    if c.stop() is False:
        return False
    if c.wait('STOPPED',timeout=max_seconds_to_wait_lxc_container_state) is False:
        return False
    return True
def _destroy_container(container_id):
    c=lxc.Container(container_id)
    if c.defined is False:
        e3log.warn('container(id:%s) to be destroyed does not exist'%(container_id))
        return False
    c.stop()
    c.wait('STOPPED',timeout=max_seconds_to_wait_lxc_container_state)
    #1 delete the fs and then update etcd entry
    if zfs_delete_fs(container_id) is False:
        e3log.warn('container(id:%s) to be destroyed fails to delete its filesystem'%(container_id)) 
    etcd_update_disk(host_uuid)
    return True
     
def start_container_instance(data):
    if 'container_id' not in data:
        return
    container_id=data['container_id']
    start_rc=_start_container(container_id)
    notify_msg=dict()
    notify_msg['prior_action']='start'
    notify_msg['container_id']=container_id
    if start_rc is False:
        notify_msg['status']='FAIL'
        e3log.warn('starting container(%s) fails'%(container_id))
    else:
        notify_msg['status']='OK'
        e3log.info('starting container(%s) succeeds'%(container_id))
    if _notify_scheduler(notify_msg) is False:
        e3log.error('can not send notofication back for starting container(id:%s)'%(container_id))

def stop_container_instance(data):
    if 'container_id' not in data:
        return
    container_id=data['container_id']
    stop_rc=_stop_container(container_id)
    notify_msg=dict()
    notify_msg['prior_action']='stop'
    notify_msg['container_id']=container_id
    if stop_rc is False:
        notify_msg['status']='FAIL'
        e3log.warn('stopping container(%s) fails'%(container_id))
    else :
        notify_msg['status']='OK'
        e3log.info('stopping container(%s) succeeds'%(container_id))
    if _notify_scheduler(notify_msg) is False:
        e3log.error('can not send notofication back for starting container(id:%s)'%(container_id))
def destroy_container_instance(data):
    if 'container_id' not in data:
        return
    container_id=data['container_id']
    rc=_destroy_container(container_id)
    notify_msg=dict()
    notify_msg['prior_action']='destroy'
    notify_msg['container_id']=container_id
    if rc is False:
        notify_msg['status']='FAIL'
        e3log.warn('destroying container(%s) fails'%(container_id))
    else:
        notify_msg['status']='OK'
        e3log.info('destroying container(%s) succeeds'%(container_id))
    if _notify_scheduler(notify_msg) is False:
        e3log.error('can not send notofication back for starting container(id:%s)'%(container_id))
    pass
action_table={
    'boot':boot_container_instance,
    'start':start_container_instance,
    'stop':stop_container_instance,
    'destroy':destroy_container_instance
}

def host_agent_callback_func(ch,method,properties,body):
    try:
        msg=ast.literal_eval(body.decode('utf-8'))
    except:
        return
    if 'action' not in msg or 'body' not in msg:
        return
    action=msg['action']
    body=msg['body']
    if action not in action_table:
        return 
    action_table[action](body)
    
    pass
if __name__=='__main__':
    #imagine we already know the uuid of the host
    host_uuid='f1f39bfd-7be3-49b3-a520-ecb28943a4d5'
    e3cfg['uuid']=host_uuid
    e3cfg['hostname']=platform.node()
    print(init_etcd_session(e3cfg['etcd-ip'],e3cfg['etcd-port']))
    #print(etcd_get_free_disk(host_uuid))
    #print(etcd_allocate_cpus_for_container(host_uuid,'container-id-jsdsjdhs',3))
    #print(etcd_get_cpus_by_container_id(host_uuid,'container-id-jsdsjdhs'))
    #print(etcd_assign_container_cpu(host_uuid,'container-id-jsdsjdhs',2))
    #print(etcd_assign_container_cpu(host_uuid,'container-id-jsdsjdhs',0))
    #print(etcd_get_free_cpus(host_uuid))
    #print(etcd_release_cpus_of_container(host_uuid,'container-id-jsdsjdhs')) 
    #print(etcd_get_cpus_by_container_id(host_uuid,'container-id-jsdsjdhs'))
    #print(etcd_get_free_cpus(host_uuid))
    #print(etcd_assign_container_cpu(host_uuid,'container-id-jsdsjdhs',2))
    #print(etcd_allocate_memory(host_uuid,512))
    #print(etcd_update_disk(host_uuid))
    #print(_etc_get_children('/host/f1f39bfd-7be3-49b3-a520-ecb28943a4d5/cpus'))
    #print(etcd_get_hosts())
    #print(etcd_register_host(e3cfg))
    #print(etcd_get_hosts())
    print(etcd_unregister_host('f1f39bfd-7be3-49b3-a520-ecb28943a4d5'))
    print(etcd_register_host(e3cfg))
   # print(etcd_get_free_disk(host_uuid))
    #print((etcd_allocate_cpus_for_container(host_uuid,'f1f39bfd-7be3-49b3-a520-ecb28943a4d5',2)))
    mq_client=E3MQClient(queue_name='host-%s'%(host_uuid),user='e3net',passwd='e3credentials')
    mq_client.start_dequeue(host_agent_callback_func)
    #config=e3cfg
    #config['uuid']=host_uuid
    #config['hostname']=platform.node()
    #print(e3cfg)
    #print(init_etcd_session(e3cfg))
    #print(etcd_register_host(config))
    #print(etcd_get_hosts())
    #print(etcd_unregister_host(host_uuid+''))
    #print(pull_image('vnf.base.image','127.0.0.1',key='e3net',force_pull=True))
    #print(validate_image('vnf.base.image','0ae2b1a243ff0528626c1ab73ff13f01e66d3c74'))
    #print(ex.tract_image('mycentos7.image','/tmp'))
    #print(extract_image_to_cotainer('centos7.lxc.vnf.image','41ef25d2-1f38-43e7-a220-4c4b5350d1e0'))
    pass
