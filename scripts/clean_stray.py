import os
import shutil

base = "/home/ubuntu/.hermes/profiles/vishal/workspace/"
stray = os.path.join(base, "~")
if os.path.isdir(stray):
    for name in os.listdir(stray):
        p = os.path.join(stray, name)
        if os.path.isdir(p):
            shutil.rmtree(p)
        else:
            os.remove(p)
    os.rmdir(stray)
    print("removed stray dir:", stray)
else:
    print("no stray dir at", stray)
