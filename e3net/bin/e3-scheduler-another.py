#! /usr/bin/python3 
import sys
from e3net.e3common.E3CFG import get_e3config
from e3net.e3compute.E3ComputeEtcd import init_etcd_session
from e3net.e3compute.DBCompute import init_e3compute_database
from e3net.e3common.E3MQ import E3MQClient
from e3net.e3compute.E3Scheduler import e3_scheduler_another_func

if __name__=='__main__':
    e3cfg=get_e3config('e3scheduler')
    if 'etcd' not in e3cfg or\
        'rabbitmq' not in e3cfg or \
        'db_compute_connection' not in e3cfg:
        print('incomplete options in config file')
        sys.exit(1)
    if init_etcd_session(e3cfg['etcd']['etcd_host'],e3cfg['etcd']['etcd_port']) is False:
        print('can not init etcd session,please check config file for its options')
        sys.exit(1)
    init_e3compute_database(conn=e3cfg['db_compute_connection'])
    scheduler=E3MQClient(queue_name='e3-scheduler-another-mq',
                            user=e3cfg['rabbitmq']['rabbitmq_user'],
                            passwd=e3cfg['rabbitmq']['rabbitmq_passwd'],
                            host=e3cfg['rabbitmq']['rabbitmq_server_host'],
                            port=e3cfg['rabbitmq']['rabbitmq_server_port'])
    scheduler.start_dequeue(e3_scheduler_another_func)
