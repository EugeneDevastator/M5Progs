from m5stack import *
from m5ui import *
from uiflow import *
import i2c_bus

setScreenColor(0x111111)
class BMP180:
    
    BMP180_ADDR = 0x77
    BMP180_REG_CONTROL = 0xF4
    BMP180_REG_RESULT = 0xF6
    BMP180_COMMAND_TEMPERATURE = 0x2E
    BMP180_COMMAND_PRESSURE0 = 0x34
    BMP180_COMMAND_PRESSURE1 = 0x74
    BMP180_COMMAND_PRESSURE2 = 0xB4
    BMP180_COMMAND_PRESSURE3 = 0xF4
    
    def __init__(self, i2c):
        self.i2c = i2c
        self.AC1 = self.AC2 = self.AC3 = self.VB1 = self.VB2 = self.MB = self.MC = self.MD = 0
        self.AC4 = self.AC5 = self.AC6 = 0
        self.c5 = self.c6 = self.mc = self.md = self.x0 = self.x1 = self.x2 = 0.0
        self.y0 = self.y1 = self.y2 = self.p0 = self.p1 = self.p2 = 0.0
        self._error = ''
    
    def readInt(self, addr):
        return self.i2c.read_mem_data(addr, 1, i2c_bus.INT16BE)[0]
    
    def readBytes(self, addr, count):
        return self.i2c.read_mem_data(addr, count, i2c_bus.UINT8BE)
    
    def readUInt(self, addr):
        return self.i2c.read_mem_data(addr, 1, i2c_bus.UINT16BE)[0]
    
    def writeBytes(self, values):
        try:
            address = values[0]
            for value in values[1:]:
                self.i2c.write_mem_data(address, value, i2c_bus.UINT8BE)
                address += 1  # Increment the address for the next write
            self._error = 0
            return 1
        except Exception as e:
            self._error = str(e)
            return 0

    def startTemperature(self):
        data = [self.BMP180_REG_CONTROL, self.BMP180_COMMAND_TEMPERATURE]
        result = self.writeBytes(data)
        if result:  # good write?
            return 5  # return the delay in ms to wait before retrieving data
        else:
            return 0 
    def getTemperature(self):
        try:
            # Read 2 bytes from the BMP180_REG_RESULT register
            data = self.i2c.read_mem_data(self.BMP180_REG_RESULT, 2, i2c_bus.UINT16BE)
            
            if data:  # good read, calculate temperature
                tu = data[0]
                
                # Calculate temperature using calibration parameters
                a = self.c5 * (tu - self.c6)
                T = a + (self.mc / (a + self.md))
                
                return 1, T  # Return 1 for success and the calculated temperature
            else:
                return 0, None  # Return 0 for failure and None for temperature
        except Exception as e:
            self._error = str(e)
            return 0, None  # Return 0 for failure and None for temperature
            
    def startPressure(self, oversampling):
        try:
            data = [self.BMP180_REG_CONTROL]
            
            # Determine the command and delay based on the oversampling value
            if oversampling == 0:
                data.append(self.BMP180_COMMAND_PRESSURE0)
                delay = 5
            elif oversampling == 1:
                data.append(self.BMP180_COMMAND_PRESSURE1)
                delay = 8
            elif oversampling == 2:
                data.append(self.BMP180_COMMAND_PRESSURE2)
                delay = 14
            elif oversampling == 3:
                data.append(self.BMP180_COMMAND_PRESSURE3)
                delay = 26
            else:
                data.append(self.BMP180_COMMAND_PRESSURE0)
                delay = 5
            
            result = self.writeBytes(data)
            
            if result:  # good write?
                return delay  # return the delay in ms to wait before retrieving data
            else:
                return 0  # or return 0 if there was a problem communicating with the BMP
        except Exception as e:
            self._error = str(e)
            return 0  # Return 0 for failure
       
    def getPressure(self, T):
      try:
          # Read 3 bytes from the BMP180_REG_RESULT register
          data = self.i2c.read_mem_data(self.BMP180_REG_RESULT, 3, i2c_bus.UINT8BE)
          
          if data:  # good read, calculate pressure
              pu = (data[0] * 256.0) + data[1] + (data[2] / 256.0)
              
              # Calculate pressure using calibration parameters and previously calculated temperature
              s = T - 25.0
              x = (self.x2 * pow(s, 2)) + (self.x1 * s) + self.x0
              y = (self.y2 * pow(s, 2)) + (self.y1 * s) + self.y0
              z = (pu - x) / y
              P = (self.p2 * pow(z, 2)) + (self.p1 * z) + self.p0
              
              return 1, P  # Return 1 for success and the calculated pressure
          else:
              return 0, None  # Return 0 for failure and None for pressure
      except Exception as e:
          self._error = str(e)
          return 0, None  # Return 0 for failure and None for pressure

    def init(self):
       self.AC1 = self.readInt(0xAA)
       self.AC2 = self.readInt(0xAC)
       self.AC3 = self.readInt(0xAE)
       self.AC4 = self.readUInt(0xB0)
       self.AC5 = self.readUInt(0xB2)
       self.AC6 = self.readUInt(0xB4)
       self.VB1 = self.readInt(0xB6)
       self.VB2 = self.readInt(0xB8)
       self.MB = self.readInt(0xBA)
       self.MC = self.readInt(0xBC)
       self.MD = self.readInt(0xBE)
       
       self.c3 = 160.0 * pow(2, -15) * self.AC3
       self.c4 = pow(10, -3) * pow(2, -15) * self.AC4
       self.b1 = pow(160, 2) * pow(2, -30) * self.VB1
       self.c5 = (pow(2, -15) / 160) * self.AC5
       self.c6 = self.AC6
       self.mc = (pow(2, 11) / pow(160, 2)) * self.MC
       self.md = self.MD / 160.0
       self.x0 = self.AC1
       self.x1 = 160.0 * pow(2, -13) * self.AC2
       self.x2 = pow(160, 2) * pow(2, -25) * self.VB2
       self.y0 = self.c4 * pow(2, 15)
       self.y1 = self.c4 * self.c3
       self.y2 = self.c4 * self.b1
       self.p0 = (3791.0 - 8.0) / 1600.0
       self.p1 = 1.0 - 7357.0 * pow(2, -20)
       self.p2 = 3038.0 * 100.0 * pow(2, -36)
       return 1 if all([self.AC1, self.AC2, self.AC3, self.AC4, self.AC5, self.AC6, self.VB1, self.VB2, self.MB, self.MC, self.MD]) else 0

def describe_pressure(pressure):
    if pressure < 950:
        return "Very Low"
    elif 950 <= pressure < 990:
        return "Low"
    elif 990 <= pressure < 1031:
        return "Normal"
    elif 1031 <= pressure < 1051:
        return "High"
    else:
        return "Very High"

lbTemp = M5TextBox(10, 182, "Text", lcd.FONT_DejaVu24, 0xFFFFFF, rotate=0)
label1 = M5TextBox(10, 54, "Pressure:", lcd.FONT_Default, 0xdedddd, rotate=0)
lbPres = M5TextBox(10, 79, "Text", lcd.FONT_DejaVu18, 0xFFFFFF, rotate=0)
lbTempTitle = M5TextBox(10, 149, "Temperature:", lcd.FONT_Default, 0xd9d7d7, rotate=0)
lbPresText = M5TextBox(10, 112, "Text", lcd.FONT_Default, 0xFFFFFF, rotate=0)
lbStatus = M5TextBox(59, 214, "status", lcd.FONT_Default, 0xbfc3cf, rotate=0)
header = M5Title(title="+3v3; sda 26; scl 0", x=0, fgcolor=0x000000, bgcolor=0xfff200)
label0 = M5TextBox(3, 26, "BMP180", lcd.FONT_UNICODE, 0x00c7ff, rotate=0)

i2c0 = i2c_bus.easyI2C((26, 0), 0x00, freq=400000)
i2c0.addr=(0x77)
lbStatus.setText(str(i2c0.scan()))
bmp180 = BMP180(i2c0)
init_result = bmp180.init()
tempinit = bmp180.startTemperature()

if(tempinit>0):
    wait_ms(tempinit)
Tinit = bmp180.getTemperature()[1]
lbStatus.setText(str(init_result)+" "+str(Tinit))
lbTemp.setText("{:.2f}".format(Tinit)+" C˚")

presDelay = bmp180.startPressure(1)
if(presDelay>0):
  lbStatus.setText("pressure..")
  wait_ms(presDelay)
pres = bmp180.getPressure(Tinit)[1]
lbPres.setText("{:.2f}".format(pres) + " mb")
lbPresText.setText(describe_pressure(pres))