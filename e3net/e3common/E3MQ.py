#! /usr/bin/python3
import pika
import time
from threading import Lock

class E3MQClient():
    # note that queue_name is None,no queue is declared
    def __init__(self,queue_name,user,passwd,host='127.0.0.1',port=5672):
        self.user=user
        self.passwd=passwd
        self.host=host
        self.port=port
        self.queue_name=queue_name
        self.is_connected=self._connect()
        self.lock=Lock() 
    def _connect(self):
        try: 
            self.conn=pika.BlockingConnection(
                    pika.ConnectionParameters(
                        host=self.host,
                        credentials=pika.PlainCredentials(self.user,self.passwd),
                        port=self.port))
            self.channel=self.conn.channel()
            if self.queue_name is not None:
                self.channel.queue_declare(queue=self.queue_name)
            return True
        except:
            return False

    #if we pass the parameter queue_another, the queue name will be replaced
    def enqueue_message(self,msg,queue_another=None):
        self.lock.acquire()
        queue=self.queue_name
        if queue_another:
            queue=queue_another
        if self.is_connected == False:
            self.is_connected=self._connect()
        if self.is_connected == False:
            self.lock.release()
            return False 
        try:
            self.channel.basic_publish(exchange='',
                    routing_key=queue,
                    body=msg,
                    properties=pika.BasicProperties(
                        delivery_mode=2))
            return True
        except pika.exceptions.ConnectionClosed:
            self.is_connected=False
            return False
        except :
            return False
        finally:
            self.lock.release()

    def start_dequeue(self,callback,interval=1):
        self.callback_fun=callback
        while self.is_connected == False:
            self.is_connected=self._connect()
            if self.is_connected == False:
                time.sleep(interval)
        try:
            self.channel.basic_consume(self.callback_fun,
                        queue=self.queue_name,
                        no_ack=True)
        except:
            return False
       
        try:
            self.channel.start_consuming()
        except pika.exceptions.ConnectionClosed:
            self.is_connected=False
            self.start_dequeue(self.callback_fun,interval)
        except:
            return False
        return True
             
def callback_fun(ch,method,properties,body):
    print('message recv:',body)
import sys
if __name__=='__main__':
    mq=E3MQClient('missant','e3net','e3credentials')
    if len(sys.argv) >1 :
        while True:
            time.sleep(1)
            print(mq.enqueue_message('hello world'))
    else:
        mq.start_dequeue(callback_fun)
 
    pass
