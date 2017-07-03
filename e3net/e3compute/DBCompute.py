#! /usr/bin/python

from sqlalchemy import *
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import uuid

E3COMPUTEDBBase=declarative_base()
E3COMPUTEDBSession=sessionmaker(autocommit=True)
E3COMPUTEDBEngine=None

def create_e3compute_database_entries(engine=None):
	if engine == None:
		engine = E3COMPUTEDBEngine
	E3COMPUTEDBBase.metadata.create_all(engine)

def bind_e3compute_session_with_engine(engine=None):
	if engine == None:
		engine=E3COMPUTEDBEngine
	E3COMPUTEDBSession.configure(bind=engine)
def init_e3compute_database(conn,echo=False):
	global E3COMPUTEDBEngine
	E3COMPUTEDBEngine=create_engine(conn,echo=echo)
	bind_e3compute_session_with_engine(E3COMPUTEDBEngine)
