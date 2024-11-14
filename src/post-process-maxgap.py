from os import listdir, path
import pandas as pd
import numpy as np

from astropy import units as u
duration = 7*u.day

def find_csv_filenames(path_to_dir, suffix=".csv" ):
    filenames = listdir(path_to_dir)
    return [ filename for filename in filenames if filename.endswith( suffix ) ]

o = []
filenames = find_csv_filenames("access_output")
for name in filenames:
    df = pd.read_csv(path.join('access_output',name))
    try:
        df = df.sort_values("access_start")
        if len(df.index) > 1:
            i = 1
            # Remove encapsulated accesses
            last_end = -1
            for i in range(1,len(df.index)-1):
                ast = df['access_start'].iloc[[i]].tolist()[0]
                af = df['access_end'].iloc[[i]].tolist()[0]
                if ast <= last_end:
                    # Starts before the end of the last access
                    if af <= last_end:
                        # Ends before the end, this is encapsulated and can be deleted
                        print('Dropping - Start {} End {} -- End {}'.format(ast,af,last_end ))
                        df = df.drop(i)
                    else:
                        # This overlaps but only at the beginning and extends it
                        last_end = af
                        i += 1
                else:
                    # This doesn't overlap at all
                    last_end = af
                    i += 1

            print(df)
            # Remove overlaps between accesses
            last_end = -1
            for i in df.index:
                if df['access_start'][i] <= last_end:
                    # Set this start to the end
                    df['access_start'][i] = last_end
                else:
                    last_end = df['access_end'].loc[i]

            # Get all accesses after the first and subtract the previous end
            o.append(max(np.array(df['access_start'].tolist()[1:])-np.array(df['access_end'].tolist()[:-1]))/60)
    except NotImplementedError:
        pass

with open("max_gap_targets_output.csv", 'w') as f:
    for k,v in enumerate(o):
        if k==0:
            f.write(str(v))
        else:
            f.write(','+str(v))
