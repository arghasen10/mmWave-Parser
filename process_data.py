import csv

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

filename = "20220610_213256.csv"

df = pd.read_csv(filename)

timenp = df.Time
print(timenp)
numObjnp = df.numObj
rangeIdxnp = df.rangeIdx
rangenp = df.range
dopplerIdxnp = df.dopplerIdx
dopplernp = df.doppler
peakValnp = df.peakVal
xnp = df.x
ynp = df.y
znp = df.z
rpnp = df.rp
noiserpnp = df.noiserp
zinp = df.zi
rangeDopplernp = df.rangeDoppler

timestamp = []
count = 0
y_corr = []
for e in rangenp:
    if type(e) != float:
        count += 1
        mystr = e.split("[")[1:2][0].split("]")[0:1][0].split(",")
        for ele in mystr:
            timestamp.append(count)
            y_corr.append(float(ele))

plt.scatter(timestamp, y_corr)
plt.xlabel("Time (sec)")
plt.ylabel("Range profiles (m)")

timestamptosec = []
for e in timestamp:
    timestamptosec.append(e / 4)
plt.xticks([0, 300, 600, 900, 1200], [0, 100, 200, 300, 400])
plt.show()


timestamp = []
count = 0
y_corr = []
for e in peakValnp:
    if type(e) != float:
        count += 1
        mystr = e.split("[")[1:2][0].split("]")[0:1][0].split(",")
        for ele in mystr:
            if float(ele) > 500:
                timestamp.append(count)
                y_corr.append(float(ele))

plt.scatter(timestamp, y_corr)
plt.xlabel("Time (sec)")
plt.ylabel("Noise profiles (m)")

timestamptosec = []
for e in timestamp:
    timestamptosec.append(e / 4)
plt.xticks([0, 300, 600, 900, 1200], [0, 100, 200, 300, 400])
plt.show()
