import bpy

from . import frame_functions
from . import color_functions

def register():
    color_functions.register()
    frame_functions.register()

def unregister():
    frame_functions.unregister()
    color_functions.unregister()
    