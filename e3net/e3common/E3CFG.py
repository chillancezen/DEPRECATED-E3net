#! /usr/bin/python3 
import yaml
import os
import sys
from e3net.e3common.E3config import *

def get_e3config(conf):
    config_file='%s/%s.yaml'%(e3net_config_dir,conf)
    if not os.path.isfile(config_file):
       return dict()
    try:
        with open(config_file,'r') as stream:
            config=yaml.load(stream)
        return config
    except:
        return dict()

if __name__=='__main__':
    e3config=get_e3config('e3host')
    print(e3config)
