#! /usr/bin/python3
# this is a simple HTTP server, later will be re-designed
import os
from e3net.e3common.E3config import * 
make_sure_dir_exist(image_server_dir)

'''
def start_image_service(host='0.0.0.0',port=5070):
    try:
        os.chdir(image_server_dir)
        os.system('/usr/bin/python3 -m http.server --bind %s %d'%(host,port))
    except:
        return False
'''
def start_image_service():
    try:
        os.system('/usr/bin/minio server %s'%(image_server_dir))
    except:
        return False

if __name__=='__main__':
    start_image_service()
