'''
Created on Jul 20, 2015

@author: stefan
'''


# General settings
SENSOR_UPDATE_INT = 1.0  # temperature readings are updated every x seconds
PCT_UPDATE_INT = 1.0    # process control thread update interval in seconds
                        # use smaller values in SIMULATION mode to increase
                        # simulation speed
WQ_UPDATE_INT = 1.0     # work queue update interval in seconds
THREAD_SLEEP_INT = 0.1  # time in seconds a thread is max allowed to sleep
TEMP_HYST = 0.2         # The range Temp +/- TEMP_HYST is valid

# Richards IP: 192.168.178.57
# Richards LAN IP: 192.168.178.55
# Stefans  IP: 192.168.178.80
IP_ADDRESS = '0.0.0.0'

# Blubber settings
BLUBBER_INT = 300       # interval in seconds
BLUBBER_DURA = 30       # duration in seconds

# Logger settings
LOG_INT = 5.0          # log every x seconds

# Socket message settings
SM_INT = 2.0            # send status every x seconds

# Simulation settings
SIMULATION = False
AMBIENT_TEMP = 10.0     # minimum temperature when no heating is applied
COOLING_FACTOR = 0.001  # cooling in degrees =
                        # (curr temp - AMBIENT_TEMP) / COOLING_FACTOR
HEATING_FACTOR = 0.08    # Normal heating is 1 K per second
RANDOM_FACTOR = 0.01    # Random Faktor. 1 cause a randomness of +/- 0.5 K

# Debug Settings
FLASK_DEBUG = False     # Start flask in debug mode
