#! /usr/bin/python3 

'''
this file act as rte_config.h in DPDK:
as the basic configuration file
'''
import os
image_host_dir='/var/lib/lxcimage/client'

image_server_dir='/var/lib/lxcimage/server'

lxc_runtime_dir='/var/lib/lxc'

#e3net configuration directory 
e3net_config_dir='/etc/e3net'






def make_sure_dir_exist(dirs):
    try:
        if not os.path.exists(dirs):
            os.makedirs(dirs)
    except:
        pass


 
