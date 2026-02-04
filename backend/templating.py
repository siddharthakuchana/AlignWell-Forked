import os
from fastapi.templating import Jinja2Templates

#path set up of main file and html files folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
#templates setup using Jinja2Templates
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "..", "frontend", "html files"))
