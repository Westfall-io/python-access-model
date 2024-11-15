from os import listdir, path
import pandas as pd
import numpy as np

from astropy import units as u

def find_csv_filenames( path_to_dir, suffix=".csv" ):
    filenames = listdir(path_to_dir)
    return [ filename for filename in filenames if filename.endswith( suffix ) ]

def postprocess_apd(config, debug):
    pd.options.mode.chained_assignment = None
    print('Running apd')
    duration = config.scenario.duration * u.day
    o = []
    filenames = find_csv_filenames("access_output")
    for name in filenames:
      df = pd.read_csv(path.join('access_output',name))
      v = []
      for i in range(0,int(duration.to(u.day).value)):
          current_day = i * u.day

          # Start of this day in minutes
          min_m = np.float64(current_day.to(u.min).value)
          # End of this day in minutes
          max_m = np.float64(
              ((current_day+1*u.day).to(u.min)-1*u.min).value
          )

          v.append(len(df[df['access_start'].between(min_m, max_m)]))

      o.append(np.average(v))

    with open("accesses_per_day_targets_output.csv", 'w') as f:
        for k,v in enumerate(o):
            if k==0:
                f.write(str(v))
            else:
                f.write(','+str(v))

def postprocess_maxgap(config, debug):
    print('Running max gap')
    duration = config.scenario.duration * u.day
    o = []
    filenames = find_csv_filenames("access_output")
    for name in filenames:
        df = pd.read_csv(path.join('access_output',name))
        try:
            df = df.sort_values("access_start")
            if len(df.index) == 1:
                continue

            i = 1
            # Remove encapsulated accesses
            last_end = -1
            drops = []
            for i in range(1,len(df.index)-1):
                # For each access
                ast = df['access_start'].iloc[[i]].tolist()[0]
                af = df['access_end'].iloc[[i]].tolist()[0]
                if ast <= last_end:
                    # Starts before the end of the last access
                    if af <= last_end:
                        # Ends before the end, this is encapsulated and can be deleted
                        print('Dropping - Start {} End {} -- End {}'.format(ast,af,last_end ))
                        drops.append(i)
                    else:
                        # This overlaps but only at the beginning and extends it
                        last_end = af
                        i += 1
                else:
                    # This doesn't overlap at all
                    last_end = af
                    i += 1

            for i in drops:
                df = df.drop(i)

            #print(df)
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
