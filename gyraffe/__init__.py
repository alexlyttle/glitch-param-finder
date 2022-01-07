from ast import literal_eval
from .gyraffe import *

with open('version.txt') as file:
    __version__ = literal_eval(file.readline())
