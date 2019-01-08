# Python Plugin AqaraHub MQTT
#
# Author: michlv
#
"""
Proxy objects for dealing with MQTT and Domoticz Device objects.
"""
import json

def get(deviceObj):
    return TempHumBaro(deviceObj)

def getTypeName(topic, data):
    for i in ProxyObjects:
        typeName = i.getTypeName(topic, data)
        if typeName:
            return typeName
    return None


class Topic:
    def __init__(self, rootTopic, topic):
        self.rootTopic = rootTopic
        self.topic = topic.split('/')
        
    def checkRootTopic(self):
        return len(self.topic) > 0 and self.topic[0] == self.rootTopic

    def getExpectedRootTopic(self):
        return self.rootTopic

    def getRootTopic(self):
        if len(self.topic) > 0:
            return self.topic[0]
        return ""
    
    def getDeviceID(self):
        if len(self.topic) >= 2:
            return self.topic[1]
        return None
    
    def getTopic(self):
        if len(self.topic) >= 3:
            return self.asString(self.topic[2:])
        return None

    def getInTopic(self):
        if len(self.topic) >= 5 and self.topic[3] == 'in':
            return self.asString(self.topic[4:])
        return None

    def asString(self, topic):
        if topic is None:
            return None
        return '/'.join(topic)


class TempHumBaro:
    def __init__(self, deviceObj):
        self.deviceObj = deviceObj
        #SignalLevel 0-100
        #BatteryLevel 0-255
        #sValue
        (self.temp, self.hum, self.hum_stat, self.baro, self.forecast) = self.deviceObj.sValue.split(';')
        # Temperature;Humidity;Humidity Status;Barometer;Forecast
        self.temp = float(self.temp)
        self.hum = float(self.hum)
        self.hum_stat = 0
        self.baro = float(self.baro)
        self.forecast = 0
        self.batt = self.deviceObj.BatteryLevel
        self.signal = self.deviceObj.SignalLevel
            
    @staticmethod
    def getTypeName(topic, data):
        t = topic.getInTopic()
        if t == 'Basic/Report Attributes/ModelIdentifier':
            jdata = json.loads(data)
            if jdata['value'] == "lumi.weather":
                return "Temp+Hum+Baro"
        return None
        
    def processData(self, topic, data):
        inTopic = topic.getInTopic()
        if topic.getTopic() == 'linkquality':
            self.signal = int(int(data)/10)
            self.update()
        elif inTopic in self.DataTopic:
            jdata = json.loads(data)
            c = self.DataTopic[inTopic]
            v = float(jdata['value']) * c[0]
            c[1](self, v)
            self.update()
        elif inTopic == 'Basic/Report Attributes/0xFF01':
            jdata = json.loads(data)
            for i in jdata['value']:
                u = False
                if i in self.XiaomiFields:
                    c = self.XiaomiFields[i]
                    v = float(jdata['value'][i]['value']) * c[0]
                    c[1](self, v)
                    u = True
                if u:
                    self.update()
                
    def setTemperature(self, value):
        self.temp = value
        
    def setHumidity(self, value):
        self.hum = value
        
    def setPressure(self, value):
        self.baro = value

    def setXiaomiBattery(self, value):
        self.batt = int((value - 2.2)*100)        
    
    def update(self):
        sValue = ';'.join((format(self.temp, '.2f'), format(self.hum, '.2f'), str(self.hum_stat), format(self.baro, '.2f'), str(self.forecast)))
        self.deviceObj.Update(0, sValue, BatteryLevel=self.batt, SignalLevel=self.signal)
    
    DataTopic = {
        "Temperature Measurement/Report Attributes/MeasuredValue": [0.01, setTemperature],
        "Relative Humidity Measurement/Report Attributes/MeasuredValue": [0.01, setHumidity],
        "Pressure Measurement/Report Attributes/ScaledValue": [0.1, setPressure]
    }
    
    XiaomiFields = {
        "1": [0.001, setXiaomiBattery],
        "100": [0.01, setTemperature],
        "101": [0.01, setHumidity],
        "102": [0.01, setPressure]
    }
                

ProxyObjects = [TempHumBaro]
