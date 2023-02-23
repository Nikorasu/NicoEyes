#from gc import collect
from framebuf import FrameBuffer, GS8, RGB565
from machine import ADC, Pin, SPI
from ssd1351 import Display, color565
#from time import sleep_us, ticks_us, ticks_diff

def thumb2dir(thumbstick):
    x, y = thumbstick[0].read_u16(), thumbstick[1].read_u16()
    #x2 = (x-32768)/32768 if abs(x-32768) > 1000 else 0 # 1000 is deadzone
    #y2 = (y-32768)/32768 if abs(y-32768) > 1000 else 0 # following is improved:
    #y2 = 0 if abs(x-32768) < 1000 and abs(y-32768) < 1000 else (y-32768)/32768
    dir = (0,0) if abs(x-32768) < 1000 and abs(y-32768) < 1000 else ((x-32768)/32768,(y-32768)/32768)
    return dir

class Eye:
    def __init__(self, display=None, size=(128,128)):
        self.display = display
        self.size = size
        with open("blink.raw", "rb") as f:
            self.lids = bytearray(f.read(size[0] * size[1]))
        self.blinklvl = 0x40
        self.blinking = False
        self.buffer = bytearray(size[0] * size[1] * 2)
        self.fb = FrameBuffer(self.buffer, self.size[0], self.size[1], RGB565)
    
    def update(self, look=(0,0)):
        if self.blinking and self.blinklvl < 0xCC:
            self.blinklvl += 0x40
        elif self.blinking and self.blinklvl >= 0xCC:
            self.blinking = False
        elif not self.blinking and self.blinklvl > 0x40:
            self.blinklvl -= 0x40
        
        curlids = bytearray(self.size[0] * self.size[1])
        for i in range(len(self.lids)):
            curlids[i] = 0xFF if self.lids[i] > self.blinklvl else 0x00
        
        lidsfb = FrameBuffer(curlids, self.size[0], self.size[1], GS8)
        
        self.fb.fill(65503)
        
        self.fb.ellipse(64+int(look[0]*24),64+int(look[1]*24),39,39,16706,True)
        self.fb.ellipse(64+int(look[0]*24),64+int(look[1]*24),15,15,0,True)
        
        self.fb.blit(lidsfb,0,0,0xFF,GS8)
        self.display.block(0,0,self.size[0]-1,self.size[1]-1,self.buffer)
        
        #del fb, curlids, lidsfb
        #collect()

def main():
    screensize = (128,128) # currently only supports 128x128
    
    spi = SPI(0, baudrate=14500000, sck=Pin(18), mosi=Pin(19))
    display = Display(spi, dc=Pin(16), cs=Pin(17), rst=Pin(20))

    thumbstick = (ADC(28), ADC(27), Pin(26,Pin.IN,Pin.PULL_UP))
    # thumbstick[2].value() == 0 if button is pressed
    
    eye1 = Eye(display, screensize)
    
    try:
        while True:
            #timer = ticks_us()
            
            if thumbstick[2].value() == 0: eye1.blinking = True

            eye1.update(thumb2dir(thumbstick))
            
            # Attempt to set framerate to 30 FPS
            #timer_dif = 33333 - ticks_diff(ticks_us(), timer)
            #if timer_dif > 0:
            #    sleep_us(timer_dif)

    finally:
        display.cleanup()

if __name__ == '__main__':
    main() # by Nik
