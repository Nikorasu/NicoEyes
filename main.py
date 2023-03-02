from framebuf import FrameBuffer, GS8, RGB565
from machine import ADC, Pin, SPI
from ssd1351 import Display, color565

def thumb2dir(thumbstick):
    x, y = thumbstick[0].read_u16(), thumbstick[1].read_u16()
    return (0,0) if abs(x-32768) < 1000 and abs(y-32768) < 1000 else ((x-32768)/32768,(y-32768)/32768)

class Eye:
    def __init__(self, display=None):  #, size=(128,128)
        self.display = display
        with open("blink.raw", "rb") as f:
            self.lids = bytearray(f.read(16384))
        self.blinklvl = 0x60
        self.blinking = False
        self.buffer = bytearray(32768)
        self.fb = FrameBuffer(self.buffer, 128, 128, RGB565)
        self.curlids = bytearray(16384)
        self.lidsfb = FrameBuffer(self.curlids, 128, 128, GS8)
        self.prvblnklvl = 0
    
    def update(self, look=(0,0)):
        if self.blinking and self.blinklvl < 0xEE: self.blinklvl += 0x50
        elif self.blinking and self.blinklvl >= 0xEE: self.blinking = False
        elif not self.blinking and self.blinklvl > 0x60: self.blinklvl -= 0xa0
        
        if self.blinklvl != self.prvblnklvl:
            self.lidsfb.fill(0)
            up0cnt, dwn0cnt = 0, 0
            for i in range(11420): # (from center to top -> 11712) reduce to widest open eye position
                if up0cnt <= 128:
                    self.curlids[11711-i] = 0xFF if self.lids[11711-i] >= self.blinklvl else 0x00
                    up0cnt = up0cnt + 1 if self.curlids[11711-i] == 0 else 0
                if dwn0cnt <= 128 and i+11712 < 16384:
                    self.curlids[11712+i] = 0xFF if self.lids[11712+i] >= self.blinklvl else 0x00
                    dwn0cnt = dwn0cnt + 1 if self.curlids[11712+i] == 0 else 0
                if up0cnt >= 128 and dwn0cnt >= 128: break
            self.prvblnklvl = self.blinklvl
        
        self.fb.fill(0xfade) # 0xdefa = 0xfade or 64222 # RGB888 = dedfd6
        self.fb.ellipse(63+int(look[0]*24),64+int(look[1]*24),42,42,0x003,True) # 0x0300 (swap low and high, so 0x003)
        self.fb.ellipse(63+int(look[0]*28),64+int(look[1]*28),16,16,0,True) # alternatively try sqeezing the pupil horizontally for a cat eye effect
        
        self.fb.blit(self.lidsfb,0,0,0xFF,GS8)
        self.display.block(0,0,127,127,self.buffer)  #self.size[0]-1,self.size[1]-1

def main():
    spi = SPI(0, baudrate=14500000, sck=Pin(18), mosi=Pin(19))
    display = Display(spi, dc=Pin(16), cs=Pin(17), rst=Pin(20))

    thumbstick = (ADC(28), ADC(27), Pin(26,Pin.IN,Pin.PULL_UP))
    eye = Eye(display)
    
    try:
        while True:
            if thumbstick[2].value() == 0: eye.blinking = True
            eye.update(thumb2dir(thumbstick))

    finally:
        display.cleanup()

if __name__ == '__main__':
    main() # by Nik
