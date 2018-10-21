from ev3dev.ev3 import *
import time

# s is the servo that drops our "projectile" once we reach the monolith
# This just makes it spin for ten seconds

s = MediumMotor()
s.run_forever(speed_sp=1000)
time.sleep(10)
s.run_forever(speed_sp=0)
