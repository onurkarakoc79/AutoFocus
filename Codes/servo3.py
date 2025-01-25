import pigpio
import time

servo_pin=18

pi=pigpio.pi()
pi.set_mode(servo_pin,pigpio.OUTPUT)

def set_angle(angle):
    pulse_width= int((angle/180)*(2500-500)+500)
    pi.set_servo_pulsewidth(servo_pin,pulse_width)
    time.sleep(1)

angle=0
set_angle(angle)
counter=10
while True:
    if(angle>=135):
        angle=0
    set_angle(angle)
    angle+=counter
pi.stop()
