from os import listdir
import pandas as pd
import numpy as np

from astropy import units as u
duration = 7*u.day

def find_csv_filenames( path_to_dir, suffix=".csv" ):
    filenames = listdir(path_to_dir)
    return [ filename for filename in filenames if filename.endswith( suffix ) ]

o = []
filenames = find_csv_filenames(".")
for name in filenames:
  df = pd.read_csv(name)
  #print(type(df['access_start'][0]))
  v = []
  for i in range(0,int(duration.to(u.day).value)):
      min_m = np.float64(i*1440)
      max_m = np.float64((i+1)*1440-1)

      v.append(len(df[df['access_start'].between(min_m, max_m)]))

  o.append(np.average(v))

with open("accesses_per_day_targets_output.csv", 'w') as f:
    for k,v in enumerate(o):
        if k==0:
            f.write(str(v))
        else:
            f.write(','+str(v))
