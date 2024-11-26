from secrets import WIFI_PASSWORD, WIFI_SSID, COUNTRY
import network
import rp2
import socket
from interstate75 import Interstate75, DISPLAY_INTERSTATE75_128X128
from time import sleep, ticks_us

# connect to wifi
rp2.country(COUNTRY)

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(WIFI_SSID, WIFI_PASSWORD)
while wlan.isconnected() is False:
    print('Waiting for connection...')
    sleep(1)
    
# Setup for the display
i75 = Interstate75(
    display=DISPLAY_INTERSTATE75_128X128, stb_invert=False, panel_type=Interstate75.PANEL_GENERIC)
display = i75.display
WIDTH, HEIGHT = display.get_bounds()

#WIDTH, HEIGHT = 86, 64

video = socket.socket()

# Change your IP and socket as appropriate
video.connect(("192.168.0.209", 4002))

y = 0
x = 0
tick_increment = 1000000 // 30

# This Micropython Viper function is compiled to native code
# for maximum execution speed.
@micropython.viper
def render(data:ptr8, x:int, y:int, next_tick:int):
    for i in range(0, 1024, 2):
        # The encoded video data is an array of span lengths and
        # greyscale colour values
        span_len = int(data[i])
        colour = int(data[i+1])
        
        # Expand the grey colour to each colour channel
        colour = (colour << 19) | (colour << 11) | (colour << 3)
        
        display.set_pen(colour)
        #display.pixel_span(x+21, y+64, span_len)
        display.pixel_span(x, y, span_len)

        x += span_len
        if x >= int(WIDTH):
            y += 1
            x = 0
            if y >= int(HEIGHT):
                i75.update()
                
                # Wait until the next frame at 15FPS
                next_tick += 1000000 // 30
                while int(ticks_us()) < next_tick:
                    pass
                y = 0
                
    return x, y, next_tick

sleep(3)
next_tick = ticks_us()

# Read out the file and render
while True:
    data = video.read(1024)
    if len(data) < 1024: break
    x, y, next_tick = render(data, x, y, next_tick)

