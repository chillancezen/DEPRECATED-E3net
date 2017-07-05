from e3net.e3compute.DBCompute import *
from uuid import uuid4
import json
from datetime import datetime

class Host(E3COMPUTEDBBase):
	__tablename__='host'
	
	id=Column(String(64),primary_key=True)
	name=Column(String(64),nullable=False,index=True,unique=True)
	description=Column(Text,nullable=True)
	host_ip=Column(String(32),nullable=False)	
	
	def __repr__(self):
		obj=dict()
		obj['id']=self.id
		obj['name']=self.name
		obj['description']=self.description
		obj['host_ip']=self.host_ip
		return str(obj)

class Image(E3COMPUTEDBBase):
	__tablename__='image'
	
	id=Column(String(64),primary_key=True)
	name=Column(String(64),nullable=False,index=True,unique=True)
	size=Column(Integer(),nullable=False)
	description=Column(Text,nullable=True)
	created_at=Column(DateTime(),nullable=False,default=datetime.now)
	
	def __repr__(self):
		obj=dict()
		obj['id']=self.id
		obj['name']=self.name
		obj['size']=self.size
		obj['description']=self.description
		obj['created_at']=self.created_at.ctime()
		return str(obj)
'''
class Interface(E3COMPUTEDBBase):
	__tablename__='interface'
	
	id=Column(String(64),primary_key=True)
	pci=Column(String(32),nullable=False)
	mac=Column(String(32),nullable=False)
	host_id=Column(String(64),ForeignKey('host.id'))

	def __repr__(self):
		obj=dict()
		obj['id']=self.id
		obj['pci']=self.pci
		obj['mac']=self.mac
		obj['host_id']=self.host_id
		return str(obj)
'''
def register_e3host(hostname,host_ip,desc=''):
	session=E3COMPUTEDBSession()
	try:
		session.begin()
		host=session.query(Host).filter(Host.name==hostname).first()
		if host:
			host.description=desc
			host.host_ip=host_ip
		else:
			host=Host()
			host.id=str(uuid4())
			host.name=hostname
			host.host_ip=host_ip
			host.description=desc
			session.add(host)
		session.commit()
		return True
	except:
		session.rollback()
		return False
	finally:
		session.close()
def get_e3hosts():
	session=E3COMPUTEDBSession()
	lst=list()
	try:
		session.begin()
		lst=session.query(Host).all()
	except:
		lst=list()
		session.rollback()
	finally:
		session.close()

	return lst
def get_e3host_by_id(id):
	session=E3COMPUTEDBSession()
	host=None
	try:
		session.begin()
		host=session.query(Host).filter(Host.id==id).first()
	except:
		host=None
		session.rollback()
	finally:
		session.close()
	return host
def get_e3host_by_name(hostname):
	session=E3COMPUTEDBSession()
	host=None
	try:
		session.begin()
		host=session.query(Host).filter(Host.name==hostname).first()
	except:
		host=None
		session.rollback()
	finally:
		session.close()
	return host
def unregister_host(id):
	session=E3COMPUTEDBSession()
	host=None
	try:
		session.begin()
		host=session.query(Host).filter(Host.id==id).first()
		if host:
			session.delete(host)
			session.commit()
			return True
		return False
	except:
		session.rollback()
		return False
	finally:
		session.close()
if __name__=='__main__':
	init_e3compute_database('mysql+pymysql://e3net:e3credientials@localhost/E3compute',True)
	create_e3compute_database_entries()
	#print(register_e3host('server-67','130.140.150.65',desc='controoler'))
	#print(get_e3hosts())
	print(get_e3host_by_id('523a178d-aa63-40d4-99c6-0a167e11c41c'))
	print(get_e3host_by_name('server-66'))
