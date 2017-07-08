#! /usr/bin/python3

import subprocess

zfs_script='/usr/bin/zfs-lxc-tool'

def zfs_free_size():
    try:
        size=subprocess.check_output([zfs_script,'free_size'])
        return float(size)
    except:
        return 0

def zfs_list_fs():
    try:
        lst_str=subprocess.check_output([zfs_script,'list_fs'])
        lst_str=lst_str.decode('utf-8')
        if lst_str == '':
            return list()
        lst=lst_str.split("#")
        return lst
    except:
        return list()
def zfs_create_fs(fsname,size):
    try:
        subprocess.check_output([zfs_script,'create_fs',fsname,str(size)])
        return True
    except:
        return False

def zfs_exist_fs(fsname):
    try:
        subprocess.check_output([zfs_script,'exist_fs',fsname])
        return True
    except:
        return False
def zfs_delete_fs(fsname):
    try:
        subprocess.check_output([zfs_script,'delete_fs',fsname])
        return True
    except:
        return False
#print(zfs_delete_fs('missant1'))
#print(zfs_exist_fs('missant1'))
#print(zfs_create_fs('missant1',1.4))
#print(zfs_create_fs('missant2',3))
#print(zfs_free_size())
#print(zfs_list_fs())
