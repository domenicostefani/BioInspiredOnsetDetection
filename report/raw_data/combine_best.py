import glob
import numpy as np

method = {
    "hfc":0,
    "energy":1,
    "complex":2,
    "phase":3,
    "specdiff":4,
    "kl":5,
    "mkl":6,
    "specflux":7,
    "mkl(noaw)":8
}

def sorting(val1,val2):
    _method1 = val1.split("-")[1]
    _method2 = val2.split("-")[1]
    if method[_method1] < method[_method2] :
        res = -1
    elif method[_method1] > method[_method2]:
        res = 1
    else:
        _bufsize1 = int(val1.split("-")[2].split("r")[0])
        _bufsize2 = int(val2.split("-")[2].split("r")[0])

        if _bufsize1 < _bufsize2 :
            res = -1
        elif _bufsize1 > _bufsize2:
            res = 1
        else:
            res = 0
            print("WARNING: two seemingly equal files, this shouldn't happen")
            print(val1)
            print(val2)
    return res

filelist = glob.glob("best*.txt")

from functools import cmp_to_key

filelist = sorted(filelist, key=cmp_to_key(sorting))
resstring = ""
for filename in filelist:
    with open(filename,"r") as file:
        partial = str(file.readline()+"\n")
        if "(noaw)" in filename:
            partial = partial.replace("mkl","mkl(noaw)")
            
        resstring += partial
        
print(resstring)

print("Writing")
with open("combined.txt","w") as f:
    f.write(resstring)


