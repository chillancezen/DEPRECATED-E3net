#! /usr/bin/python3

import logging
import os

logers=dict()
def _make_sure_file_exist(filepath):
    if not os.path.exists(os.path.dirname(filepath)):
        try:
            os.makedirs(os.path.dirname(filepath))
            with open(filepath,'w') as f:
                f.write('log file:%s created\n'%(filepath))
        except:
            return False
    return True

def _get_e3loger(filename):
    logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
    rootLogger = logging.getLogger(filename)
    rootLogger.setLevel(logging.DEBUG)
    filepath="{0}/{1}.log".format('/var/log/e3net', filename)
    if _make_sure_file_exist(filepath) is False:
        return None
    fileHandler = logging.FileHandler(filepath)
    fileHandler.setFormatter(logFormatter)
    rootLogger.addHandler(fileHandler)
    return rootLogger

def get_e3loger(filename):
    if filename in logers:
        return logers[filename]
    logger=_get_e3loger(filename)
    if logger is None:
        return None
    logers[filename]=logger
    return logger 

if __name__ == '__main__':
    pass
