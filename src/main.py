import math
import datetime
import copy

import os
if not os.path.exists('access_output'):
   os.makedirs('access_output')

from astropy import units as u
from astropy.coordinates import GCRS, EarthLocation, AltAz
from astropy.time import Time
time = Time('2012-7-12 23:00:00')

from hapsira.bodies import Earth
from hapsira.twobody import Orbit

# Main orbit params
a = (500+6378.14) * u.km
inc = 45 * u.deg
# Walker params
sats = 10
planes = 10
### Hardcoded f=0
# Image params
max_resolution = 50 #m from requirement
pixel_pitch_micron = 0.0055 #mm
focal_length = 31.69 # cm
# Targets
lats = [38.65, 45.28, 43.93, 45.60, 33.87]
lons = [-117.5, -114.2, -110.24, -112.79, -111.28]
# Sim params
duration = 7*u.day
sim_step = 1*u.min

# Assume all circular, regular orbits
ecc = 0 * u.one
argp = 0 * u.deg

# Calculate look angle
ifov = (pixel_pitch_micron/1e3)/(focal_length/1e2) #rad
max_distance = max_resolution/math.tan(ifov)
p1 = (6378.14**2 + max_distance/1000**2 - (6378.14+500)**2)
graze = math.acos(p1/(2*6378.14*max_distance/1000))-math.pi/2
print('Graze Limit: {} deg.'.format(graze*180/math.pi))

if sats < 0:
    raise NotImplementedError('Not enough satellites.')
else:
    raan = 0 * u.deg
    nu = 0 * u.deg
    print("Sat 1: 0,0")
    orb = [copy.deepcopy(Orbit.from_classical(Earth, a, ecc, inc, raan, argp, nu))]
    if sats > 1:
        plane = 1
        stp = 1
        plane_draan = 360/planes #36 deg/plane in raan
        sats_per_plane = sats/planes
        plane_dnu = 360/sats_per_plane #360 deg/sat in nu (only 1 sat)
        for sat in range(2,sats+1):
            if stp + 1 > sats_per_plane:
                plane = plane + 1
                raan += plane_draan*u.deg
                nu = 0 * u.deg
            else:
                nu += plane_dnu * u.deg
            print("Sat {}: {},{}".format(sat,raan.value,nu.value))
            orb.append(copy.deepcopy(Orbit.from_classical(Earth, a, ecc, inc, raan, argp, nu)))

if len(lats) != len(lons):
    raise NotImplementedError('Error with targets.')

for o in orb:
    print(o.raan.value)

# Make Earth Locations
els = []
a_f = []
for k,v in enumerate(lats):
    lat = v
    lon = lons[k]
    els.append(EarthLocation(lat=lat*u.deg, lon=lon*u.deg, height=0*u.m))
    a_f.append(open("access_output/access_{}_{}_{}.csv".format(k,int(lat*100),int(lon*100)),'w'))
    a_f[-1].write('sat,access_start,access_end')

j = 1
cnt_accesses = [0,0,0,0,0]
for sat in orb:
    print('Checking this satellite: {} -- {},{}'.format(j, sat.raan, sat.nu))
    sat_now = sat
    i = 0
    accesses = [0,0,0,0,0]
    a_tf = [-1, -1, -1, -1, -1]
    while i < (duration/sim_step).to(u.one).value:
        #print('Sim Step: {}'.format(i))
        sat_now = sat_now.propagate(sim_step)
        #t_now = Time((time.to_datetime()+datetime.timedelta(sim_step.to(u.s).value)).isoformat())
        sat_eci = GCRS(sat_now.r[0].to(u.m), sat_now.r[1].to(u.m), sat_now.r[2].to(u.m), obstime=sat_now.epoch, representation_type='cartesian')
        for k,el in enumerate(els):
            sat_altaz = sat_eci.transform_to(AltAz(obstime=sat_now.epoch, location=el))
            if sat_altaz.alt > graze*u.rad and accesses[k]==0:
                #print('Access start at {} on target {}.'.format(sat_now.epoch.to_datetime(),k))
                accesses[k]=1
                a_tf[k]=i
                #print(sat_altaz.distance.to(u.km))
            elif sat_altaz.alt < graze*u.rad and accesses[k]==1:
                #print('Access end at {} on target {}.'.format(sat_now.epoch.to_datetime(),k))
                cnt_accesses[k] += 1
                accesses[k]=0
                a_f[k].write('\n{},{},{}'.format(j,(a_tf[k]*sim_step).to(u.min).value,(i*sim_step).to(u.min).value))
                a_tf[k]=-1
        i += 1

    # Check if any had open accesses at sim end
    for k,v in enumerate(a_tf):
        if v != -1:
            a_f[k].write('\n{},{},{}'.format(j,(a_tf[k]*sim_step).to(u.min).value,(i*sim_step).to(u.min).value))

    j += 1

# Close all files
for k,v in enumerate(a_f):
    v.close()
