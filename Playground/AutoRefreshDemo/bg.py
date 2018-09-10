import os
import time
import random
from shutil import copyfile


files = os.listdir('imgs')
while True:
    index = random.randint(0, 3)
    file_name = files[index]
    copyfile(os.path.join('imgs', file_name), 'img.png')
    time.sleep(0.04)
