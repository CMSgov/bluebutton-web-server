from .base import *
from platform import python_version

DEBUG = True

SECRET_KEY = "BBOAUTH2-LOCAL-_ocdlv24!g$4)b&wq9fjn)p!vrs729idssk2qp7iy!u#"

if DEBUG:
    print("==========================================================")
    # APPLICATION_TITLE is set in .base
    print(APPLICATION_TITLE)
    print("running on", python_version())
    print("==========================================================")


    
    
    
