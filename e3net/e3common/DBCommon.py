#! /usr/bin/python

from sqlalchemy import *
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import uuid

E3DBBase=declarative_base()
E3DBSession=sessionmaker(autocommit=True)
E3DBEngine=None

def create_e3common_database_entries(engine=None):
	if engine == None:
		engine = E3DBEngine
	E3DBBase.metadata.create_all(engine)

def bind_e3common_session_with_engine(engine=None):
	if engine == None:
		engine=E3DBEngine
	E3DBSession.configure(bind=engine)
def init_e3common_database(conn,echo=False):
	global E3DBEngine
	E3DBEngine=create_engine(conn,echo=echo)
	bind_e3common_session_with_engine(E3DBEngine)
