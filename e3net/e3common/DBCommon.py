#! /usr/bin/python

from sqlalchemy import *
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import uuid

E3COMMONDBBase=declarative_base()
E3COMMONDBSession=sessionmaker(autocommit=True)
E3COMMONDBEngine=None

def create_e3common_database_entries(engine=None):
	if engine == None:
		engine = E3COMMONDBEngine
	E3COMMONDBBase.metadata.create_all(engine)

def bind_e3common_session_with_engine(engine=None):
	if engine == None:
		engine=E3COMMONDBEngine
	E3COMMONDBSession.configure(bind=engine)
def init_e3common_database(conn,echo=False):
	global E3COMMONDBEngine
	E3COMMONDBEngine=create_engine(conn,echo=echo)
	bind_e3common_session_with_engine(E3COMMONDBEngine)
