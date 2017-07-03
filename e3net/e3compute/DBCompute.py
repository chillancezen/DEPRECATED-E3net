#! /usr/bin/python

from sqlalchemy import *
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import uuid

E3DBBase=declarative_base()
E3DBSession=sessionmaker(autocommit=True)
E3DBEngine=None


