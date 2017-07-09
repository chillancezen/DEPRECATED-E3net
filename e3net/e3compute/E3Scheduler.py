#! /usr/bin/python3
import json
from e3net.e3common.E3MQ import E3MQClient
from e3net.e3common.E3LOG import get_e3loger
from e3net.e3compute.E3Container import get_e3container_by_id ,set_e3container_status
from e3net.e3compute.DBCompute import init_e3compute_database
from e3net.e3compute.E3COMPUTEHost import get_e3image_by_id
from e3net.e3compute.E3COMPUTEHost import get_e3flavor_by_id
e3log=get_e3loger('e3scheduler')
cheduler=E3MQClient(queue_name='e3-scheduler-mq',
                        user='e3net',
                        passwd='e3credentials')



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
    pass


def start_container(msg):
    pass
def stop_container(msg):
    pass

dist_table={
'boot':boot_container,
'start':start_container,
'stop':stop_container
}

def e3scheduler_fun(ch,method,properties,body):
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

if __name__=='__main__':
    init_e3compute_database('mysql+pymysql://e3net:e3credientials@localhost/E3compute')
    cheduler.start_dequeue(e3scheduler_fun)
