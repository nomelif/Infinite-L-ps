from ev3dev.ev3 import *
import time
import os # For the sake of ssh:ing into the other EV3 brick
import curses # For the sake of remoting the robot somewhat humanely

# Hardware init

m1 = LargeMotor('outA')
m2 = LargeMotor('outB')
m3 = LargeMotor('outC')
m4 = LargeMotor('outD')
cl1 = ColorSensor(address='in1')
cl1.mode = 'RGB-RAW'
us = UltrasonicSensor(address='in2')
us.mode='US-DIST-CM'
us2 = UltrasonicSensor(address='in3')
us2.mode='US-DIST-CM'

# Setup curses

stdscr = curses.initscr()
curses.cbreak()
stdscr.keypad(1)
stdscr.addstr(0, 10, "Cast thine curses at me or strike 'q' to slaughter me???")
stdscr.refresh()


# Helper for getting somewhat accurate measurements from the color sensor in measure mode
# Bodgy sliding window. We used it to figure out the colors of things during development

RGB_buffer = [[0] * 3] * 3
last_RGB = [0] * 3
def get_RGB():
    global RGB_buffer
    global last_RGB
    RGB_buffer.pop(0)
    measure = [cl1.value(0), cl1.value(1), cl1.value(2)]
    RGB_buffer.append(measure)
    now_RGB = [sum(map(lambda x: x[0], RGB_buffer)) / len(RGB_buffer), sum(map(lambda x: x[1], RGB_buffer)) / len(RGB_buffer), sum(map(lambda x: x[2], RGB_buffer)) / len(RGB_buffer)]
    for loc, val in enumerate(now_RGB):
        if abs((val / (measure[loc] + 1)) - 1) < 0.1:
            last_RGB[loc] = val
    return last_RGB


# Follows the line inside the labyrinth

def follow_line():
    try: # The try block lets us interrupt the macro nicely with a keyboard interrupt
        while us.value() < 500: # We are in the mase iff there is a roof above us
          if cl1.value(2) > 70: # If the color sensor sees the line, it turns one way and advances
            set_motors(-300, -300, 100, 100)
          else: # Else it turns the other way and advances
            set_motors(100, 100, -300, -300)
    except KeyboardInterrupt:
      stop_motors()
    stop_motors()


# Macro to set the states of the motors

def set_motors(A, B, C, D):
    m1.run_forever(speed_sp=A)
    m2.run_forever(speed_sp=B)
    m3.run_forever(speed_sp=C)
    m4.run_forever(speed_sp=D)

# Macro to stop the motors

def stop_motors():
    m1.stop(stop_action="hold")
    m2.stop(stop_action="hold")
    m3.stop(stop_action="hold")
    m4.stop(stop_action="hold")


# Automation for the monolith

def monolith():

    # We go forwards until we get near the back wall

    set_motors(-300, -300, -300, -300)
    while us2.value() > 150:
        pass

    # We turn roughly 90 deg to the right

    set_motors(-300, -300, 300, 300)
    time.sleep(2)

    # We run forwards until we are basically on the edge of the button pit

    set_motors(-300, -300, -300, -300)
    while us2.value() > 170:
        pass
    stop_motors()

    # We ssh into the other EV3 we are running, triggering a small script that drops a projectile
    # This projectile should hopefully drop onto the switch, thus bypassig the whole monolith itself
    # drop.py is included in this repo aswell

    os.system("sshpass -p 'maker' ssh robot@172.20.10.9 'python3 drop.py'")

    # Drive onto the orange pad

    set_motors(-300, -300, 300, 300)
    time.sleep(1)
    set_motors(-300, -300, -300, -300)
    time.sleep(4)
    stop_motors()

    # From now on it's manual control


# Test whether we are on an orange pad

def orang(t=30):
    r1, g1, b1 = cl1.value(0), cl1.value(1), cl1.value(2)
    return abs(r1 - 116) < t and abs(g1 - 107) < t and abs(b1- 187) < t


# Here is the main loop. We are using curses to capture keyboard input over ssh

key = ''
while key != ord('q'): # We wait for a q to quit
    try: # If a keyboard interrupt bubbles up this high, we silently swallow it

      key = stdscr.getch() # Actual keyboard input

      # Basic remote control with arrow keys

      if key == curses.KEY_LEFT:
        set_motors(200, 200, -200, -200)
      elif key == curses.KEY_RIGHT:
        set_motors(-200, -200, 200, 200)
      elif key == curses.KEY_UP:
        set_motors(-900, -900, -900, -900)
      elif key == curses.KEY_DOWN:
        set_motors(900, 900, 900, 900)

      # x to stop

      elif key == ord('x'):
        stop_motors()

      # u to active the monolith macro

      elif key == ord('u'):
        monolith()

      # 1 to activate the line follower

      elif key == ord('l'):
          follow_line()

      # m to enter measure mode

      elif key == ord('m'):
          curses.endwin()
          r1, g1, b1 = cl1.value(0), cl1.value(1), cl1.value(2)
          for i in range(3):
            vals = get_RGB()
          time.sleep(1.5)
          curses.initscr()
          stdscr.addstr(0, 0, str(vals[0]) + ", " + str(vals[1]) + ", " + str(vals[2]) + " " + str(orang()) + "\n\r")


    except KeyboardInterrupt:
      stop_motors()



# Clear curses to return back to a normal CLI

curses.endwin()

# Make sure that the motors are stopped

stop_motors()
