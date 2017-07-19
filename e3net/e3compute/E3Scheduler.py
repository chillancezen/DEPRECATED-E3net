#! /usr/bin/python3
import json
import concurrent.futures
from e3net.e3common.E3MQ import E3MQClient
from e3net.e3common.E3LOG import get_e3loger
from e3net.e3compute.E3Container import get_e3container_by_id ,set_e3container_status
from e3net.e3compute.E3Container import set_e3container_extra, set_e3container_host
from e3net.e3compute.DBCompute import init_e3compute_database
from e3net.e3compute.E3COMPUTEHost import get_e3image_by_id
from e3net.e3compute.E3COMPUTEHost import get_e3flavor_by_id
from e3net.e3compute.E3COMPUTEHost import get_e3host_by_name
from e3net.e3compute.E3ComputeEtcd import *

e3log=get_e3loger('e3scheduler')
scheduler=E3MQClient(queue_name='e3-scheduler-mq',
                        user='e3net',
                        passwd='e3credentials')
scheduler_anothrt=E3MQClient(queue_name='e3-scheduler-another-mq',
                        user='e3net',
                        passwd='e3credentials')

hostmq=E3MQClient(queue_name=None,user='e3net',passwd='e3credentials')

sequential_executor=concurrent.futures.ThreadPoolExecutor(max_workers=1)
concurrent_executor=concurrent.futures.ThreadPoolExecutor(max_workers=5)

#hostagent message queue format:host-<uuid>


def _validate_image_and_flavor(data):
    image=data['image']
    flavor=data['flavor']
    flavor_size=flavor.disk*1024*1024*1024
    image_size=image.size
    if image_size > flavor_size:
        return False
    return True

def boot_container_bottom_half(data):
    
    container=data['container']
    image=data['image']
    flavor=data['flavor']

    if _validate_image_and_flavor(data) is False:
        error_msg='image(name:%s)\'s size is larger than flavor(name:%s)\'s size'%(image.name,flavor.name)
        e3log.error(error_msg)
        set_e3container_extra(container.id,error_msg)
        set_e3container_status(container.id,'failed')
        return
 
    #to-do:select an host according to the flavor(compute)&network requirment 
    #and run the container on the target host
    #here we still randomly choose one host
    #allocate the network resource
    #allocate the compute resource
    
    #for debug purpose ,here we manually select one host
    host=get_e3host_by_name('nfv-volume')

    set_e3container_host(container.id,host.name)
    #1 allocate memory/cpu/disk from host
    error_flag=False
    if etcd_allocate_memory(host.id,flavor.mem) is True:
        if etcd_get_free_disk(host.id) < flavor.disk:
            error_flag=True
            etcd_deallocate_memory(host.id,flavor.mem)
        elif etcd_allocate_cpus_for_container(host.id,container.id,flavor.cpus) is False:
            error_flag=True
            etcd_deallocate_memory(host.id,flavor.mem)
    else:
        error_flag=True

    if error_flag is True:
        error_msg='can not satisify the allocation requirement(cpu:%s(free:%s) memory:%sMB(free:%sMB) disk:%sGB(free:%sGB)) of container(id:%s)'%(
                flavor.cpus,
                len(etcd_get_free_cpus(host.id)),
                flavor.mem,
                etcd_get_free_memory(host.id),
                flavor.disk,
                etcd_get_free_disk(host.id),
                container.id)
        e3log.error(error_msg)
        set_e3container_extra(container.id,error_msg)
        set_e3container_status(container.id,'failed')
        return
    #2 send task to agent to boot the container 
    mq_id='host-%s'%(host.id)
    msg=dict()
    msg['action']='boot'
    msg['body']=str(data)
    rc=hostmq.enqueue_message(msg=str(msg),queue_another=mq_id)
    if rc:
        e3log.info('distributing container(id:%s) booting message to host(name:%s) succeeds'%(container.id,host.name))
    else:
        set_e3container_status(container.id,'failed')
        set_e3container_extra(container.id,'distributing container booting message to host(name:%s) fails'%(containerhost.name)) 
        e3log.error('distributing container(id:%s) booting message to host(name:%s) fails'%(container.id,host.name))

def boot_container(msg):
    if 'container_id' not in msg:
        return 
    container_id=msg['container_id']
    container=get_e3container_by_id(container_id)
    if not container:
        e3log.error('can not find container by id:%s'%(container_id))
        return
    image=get_e3image_by_id(container.image_id)
    flavor=get_e3flavor_by_id(container.flavor_id)
    if not image or not flavor :
        error_msg='can not find image or flavor associated with container(id:%s)'%(container_id)
        e3log.error('can not find image or flavor associated with container(id:%s)'%(container_id))
        return
    #1. check the task status of the target container
    if container.task_status != 'created':
        e3log.error('can not boot container(id:%s) since its task status is:%s'%(container_id,container.task_status))
        return
    rc=set_e3container_status(container.id,'spawning')
    if rc:
        e3log.info('container(id:%s) is spawning'%(container_id))
    else:
        e3log.error('can not set container(id:%s) to status:spawning,task terminated'%(container_id)) 
        return
    try:
        sequential_executor.submit(boot_container_bottom_half,{'container':container,'image':image,'flavor':flavor})
    except:
        e3log.error('errors occur when submitting bottom half task of booting container(id:%s)'%(container_id))
    
def start_container(msg):
    pass
def stop_container(msg):
    pass
def notify_controller(msg):
    pass

dist_table={
'boot':boot_container,
'start':start_container,
'stop':stop_container
}

another_dist_table={
'notify':notify_controller
}
def e3scheduler_func(ch,method,properties,body):
    try:
        msg=json.loads(body.decode("utf-8"))
    except:
        return
    if 'action' not in msg:
        return 
    action=msg['action']
    if action not in dist_table:
        return 
    dist_table[action](msg)
    #if distributed routine does not race with other action, submit to consurrent worker
def e3_scheduler_another_func(ch,method,properties,body):
    try:
        msg=json.loads(body.decode("utf-8"))
    except:
        return
    if 'action' not in msg:
        return
    action=msg['action']
    if action not in another_dist_table:
        return
    another_dist_table[action](msg)

if __name__=='__main__':
    print('init etcd:',init_etcd_session(etcd_ip='10.0.2.15',etcd_port=2379))
    init_e3compute_database('mysql+pymysql://e3net:e3credientials@localhost/E3compute')
    scheduler.start_dequeue(e3scheduler_func)
