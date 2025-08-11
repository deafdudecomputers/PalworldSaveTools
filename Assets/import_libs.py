import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT']='1'
import sys,argparse,code,collections,copy,ctypes,datetime,functools,gc,importlib.metadata,json,shutil,glob
import logging,multiprocessing,platform,pprint,re,subprocess,tarfile,threading,pickle,zipfile,customtkinter,string,palworld_coord
import time,traceback,uuid,io,pathlib,tkinter as tk,tkinter.font,csv,urllib.request,tempfile,random,pandas as pd
import matplotlib.pyplot as plt,matplotlib.patches as patches,matplotlib.font_manager as font_manager,matplotlib.patheffects as path_effects
from multiprocessing import shared_memory
from tkinter import ttk, filedialog, messagebox, PhotoImage, simpledialog
from PIL import Image,ImageDraw,ImageOps,ImageFont,ImageTk
sys.path.insert(0,os.path.abspath(os.path.join(os.path.dirname(__file__),"palworld_save_tools","commands")))
from palworld_save_tools.archive import *
from palworld_save_tools.palsav import *
from palworld_save_tools.paltypes import *
import palworld_save_tools.rawdata.group as palworld_save_group
from palobject import *
from palworld_save_tools.gvas import *
from palworld_save_tools.rawdata import *
from palworld_save_tools.json_tools import *
from generate_map import *
from pal_names import *
from pal_passives import *
from palworld_coord import sav_to_map
from common import ICON_PATH
from collections import defaultdict
import pygame