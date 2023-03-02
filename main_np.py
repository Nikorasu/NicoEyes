from machine import ADC, Pin, SPI, freq, Timer
from framebuf import FrameBuffer, GS8, RGB565
from ssd1351 import Display, color565
from ulab import numpy as np

Temperature_Sensor = ADC(4)

def check_temp(timer):
    temp = Temperature_Sensor.read_u16() * (3.3 / 65535)
    temp = 27 - (temp - 0.706)/0.001721
    print(f"Temperature: {temp:.1f}°C")

TempMonitor = Timer(mode=Timer.PERIODIC, period=3000, callback=check_temp)

def thumb2dir(thumbstick):
    x, y = thumbstick[0].read_u16(), thumbstick[1].read_u16()
    return (0,0) if abs(x-32768) < 1000 and abs(y-32768) < 1000 else ((x-32768)/32768,(y-32768)/32768)

class Eye:
    def __init__(self, display=None):
        self.display = display
        with open('uppersmall.raw', 'rb') as upper, open('lowersmall.raw', 'rb') as lower:
            self.upper = np.frombuffer(upper.read(4096), dtype=np.uint8)
            self.lower = np.frombuffer(lower.read(4096), dtype=np.uint8)
        self.buffer = bytearray(32768)
        self.fb = FrameBuffer(self.buffer, 128, 128, RGB565)
        self.curlids = np.zeros(16384, dtype=np.uint8)
        self.lidsfb = FrameBuffer(self.curlids, 128, 128, GS8)
        self.blinking = False
        self.blinklvl = 0x50
    
    def update(self, look=(0,0)):
        if self.blinking and self.blinklvl < 0xEE: self.blinklvl += 0x30
        elif self.blinking and self.blinklvl >= 0xEE: self.blinking = False
        elif not self.blinking and self.blinklvl > 0x50: self.blinklvl -= 0x40
        
        upperlvl = self. blinklvl + look[1] * 0x20
        lowerlvl = self. blinklvl - look[1] * 0x20
        
        smlids = np.where(self.upper >= upperlvl, 0xFF, 0x00)
        smlids = np.where(self.lower >= lowerlvl, smlids, 0x00)
        self.curlids = self.curlids.reshape((128,128))
        smlids = smlids.reshape((64,64))
        self.curlids[0:128:2,0:128:2] = smlids
        self.curlids[1:128:2,0:128:2] = smlids
        self.curlids[0:128:2,1:128:2] = smlids
        self.curlids[1:128:2,1:128:2] = smlids
        self.curlids = self.curlids.reshape((16384,))
        
        self.fb.fill(0xfade) # 0xdefa = 0xfade or 64222 # RGB888 = dedfd6
        self.fb.ellipse(63+int(look[0]*24),64+int(look[1]*24),42,42,0x003,True) # 0x0300 (swap low and high, so 0x003)
        self.fb.ellipse(63+int(look[0]*28),64+int(look[1]*28),16,16,0,True) # alternatively try sqeezing the pupil horizontally for a cat eye effect
        
        self.fb.blit(self.lidsfb,0,0,0xFF,GS8)
        self.display.block(0,0,127,127,self.buffer)  #self.size[0]-1,self.size[1]-1

def main():
    freq(250_000_000) # overclocks pico to 250 MHz
    
    spi = SPI(0, baudrate=14500000, sck=Pin(18), mosi=Pin(19))
    display = Display(spi, dc=Pin(16), cs=Pin(17), rst=Pin(20))

    thumbstick = (ADC(28), ADC(27), Pin(26,Pin.IN,Pin.PULL_UP))
    eye = Eye(display)
    
    try:
        while True:
            if thumbstick[2].value() == 0: eye.blinking = True
            eye.update(thumb2dir(thumbstick))

    finally:
        freq(125_000_000) # reset back to 125 MHz
        display.cleanup()
        TempMonitor.deinit()

if __name__ == '__main__':
    main() # by Nik
