from jsonrpc2_zeromq import RPCServer
import lxc
import concurrent.futures

import time
def _start_container(container):
	try:
		c=lxc.Container(container)
		if c.start():
			return c.wait('RUNNING')
		else:
			return False
	except:
		return False
def _start_container_monitor(handler):
	try:
		rc=handler.result(timeout=5)
		#do notificatoin
		print('start container:',rc)
	except:
		#error handling
		pass

def _stop_container(container):
	try:
		c=lxc.Container(container)
		if c.stop():
			return c.wait('STOPPED')
		else:
			return False
	except:
		return False
def _stop_container_monitor(handler):
	try:
		rc=handler.result(timeout=5)
		print('stop container:',rc)
	except:
		pass

class E3Msg_dispatcher(RPCServer):
	#/*background task monitoring*/
	executors=concurrent.futures.ThreadPoolExecutor(max_workers=10)
	monitors=concurrent.futures.ThreadPoolExecutor(max_workers=10)
	
	def handle_get_containers_method(self):
		return lxc.list_containers()
	def handle_is_container_running_method(self,container):
		try:
			c=lxc.Container(container)
			return c.running
		except:
			return False
	def handle_start_container_method(self,container):
		try:
			handler=self.executors.submit(_start_container,container)
			self.monitors.submit(_start_container_monitor,handler)
			return True
		except:
			return False
	def handle_stop_container_method(self,container):
		try:
			handler=self.executors.submit(_stop_container,container)
			self.monitors.submit(_stop_container_monitor,handler)
			return True
		except:
			pass

s=E3Msg_dispatcher('tcp://127.0.0.1:507')
s.run()
