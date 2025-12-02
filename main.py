from skyfield.api import load, wgs84, utc
from datetime import datetime, timedelta

LAT = 8.5241
LONG = 76.9366
ELE = 16

ground_station = wgs84.latlon(LAT, LONG, elevation_m=ELE)

print(f"Ground station: {ground_station}")
print(f"Latitude: {ground_station.latitude}, Longitude: {ground_station.longitude}, Elevation: {ground_station.elevation} meters")

ts= load.timescale()

stations_url = "https://celestrak.org/NORAD/elements/gp.php?GROUP=stations&FORMAT=tle"
satellite= load.tle_file(stations_url)
print(f"Loaded {len(satellite)} satellites")


iss = None
for sat in satellite:
    if 'ISS' in sat.name and 'ZARYA' in sat.name:
        iss = sat
        break 

if iss is None:
    print("Could not find ISS")
    exit()


now = ts.now()
current_time = datetime.now(utc)
print("=" * 60)
print("ISS POSITION RIGHT NOW")
print("=" * 60)
print(f"Current time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")

difference  = iss- ground_station
topocentric = difference.at(now)


alt,az,distance = topocentric.altaz()

print(f"Altitude: {alt.degrees:.2f}° above horizon")
print(f"Azimuth: {az.degrees:.2f}° (compass direction)")
print(f"Distance: {distance.km:.0f} km away")
print()

if alt.degrees > 0:
    print("ISS is visible from the ground station")
    if alt.degrees > 10:
        print("Good visibility")
else:
    print("ISS is not visible from the ground station") 
print()

start_time = ts.now()
end_time = ts.from_datetime(current_time + timedelta(hours=12))

# Variables to track the pass
in_pass = False
pass_start = None
max_altitude = 0
max_altitude_time = None

# Check every minute
time_step = 1  # minutes
current_check = datetime.now(utc)

for i in range(12 * 60):  # 12 hours * 60 minutes
    # Create time object for this check
    t = ts.from_datetime(current_check)
    
    # Calculate position
    difference = iss - ground_station
    topocentric = difference.at(t)
    alt, az, distance = topocentric.altaz()
    
    # Check if satellite is above horizon
    if alt.degrees > 0:
        if not in_pass:
            # Pass just started!
            in_pass = True
            pass_start = current_check
            max_altitude = alt.degrees
            max_altitude_time = current_check
        else:
            # Track maximum altitude during this pass
            if alt.degrees > max_altitude:
                max_altitude = alt.degrees
                max_altitude_time = current_check
    else:
        if in_pass:
            # Pass just ended!
            pass_end = current_check
            duration = (pass_end - pass_start).seconds / 60
            
            # Print the pass details
            print(f"PASS FOUND!")
            print(f"  Start:  {pass_start.strftime('%H:%M:%S')}")
            print(f"  Peak:   {max_altitude_time.strftime('%H:%M:%S')} - {max_altitude:.1f}° altitude")
            print(f"  End:    {pass_end.strftime('%H:%M:%S')}")
            print(f"  Duration: {duration:.1f} minutes")
            
            if max_altitude > 10:
                print(f"  Quality: ✓ GOOD (above 10° elevation)")
            else:
                print(f"  Quality: ✗ LOW (below 10° elevation)")
            print()
            
            # We found a pass, so we can stop searching
            break
            
        in_pass = False
    
    # Move to next minute
    current_check += timedelta(minutes=time_step)