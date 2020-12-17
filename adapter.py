# Python Plugin AqaraHub MQTT
#
# Author: michlv
#
"""
Proxy objects for dealing with MQTT and Domoticz Device objects.
"""
import json
import threading

def onData(devices, createDevice, rootTopicStr, topicStr, dataStr):
    topic = Topic(rootTopicStr, topicStr)
    deviceID = topic.getDeviceID()

    devProxy = _getDeviceProxy(devices, deviceID)
    if devProxy:
        devProxy.processData(topic, dataStr)
    else:
        _registerDevice(devices, createDevice, deviceID, topic, dataStr)

        
def _getDeviceProxy(devices, deviceID):
    for Unit in devices:
        if devices[Unit].DeviceID == deviceID:
            dev = devices[Unit]
            for i in ProxyObjects:
                a = i.getAdapter(devices, dev)
                if a:
                    return a
    return None


def _registerDevice(devices, createDevice, deviceID, topic, data):
    for i in ProxyObjects:
        i.registerDevice(devices, createDevice, deviceID, topic, data)


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


def _getNextUnitId(devices):
    umax = 0
    for i in devices:
        umax = max(umax, devices[i].Unit)
    return umax+1
    
def _createDeviceByName(devices, createDevice, deviceID, typeName):
    umax = _getNextUnitId(devices)
    createDevice(Name=deviceID, Unit=umax, TypeName=typeName, DeviceID=deviceID, Used=1).Create()

def _createDeviceByType(devices, createDevice, deviceID, type, subtype, switchtype):
    umax = _getNextUnitId(devices)
    createDevice(Name=deviceID, Unit=umax, Type=type, Subtype=subtype, Switchtype=switchtype, DeviceID=deviceID, Used=1).Create()

def _getSensorModel(topic, data):
    t = topic.getInTopic()
    if t == 'Basic/Report Attributes/ModelIdentifier':
        jdata = json.loads(data)
        return jdata['value']
    return None


class XiaomiSensorWithBatteryAndLinkquality:
    def __init__(self, devices, deviceObj):
        self.devices = devices
        self.deviceObj = deviceObj
        #SignalLevel 0-100
        #BatteryLevel 0-255
        self.batt = self.deviceObj.BatteryLevel
        self.signal = self.deviceObj.SignalLevel

    def processData(self, topic, data):
        inTopic = topic.getInTopic()
        if topic.getTopic() == 'linkquality':
            self.signal = int(int(data)/10)
            self.update()
        elif inTopic in self.DataTopic:
            jdata = json.loads(data)
            c = self.DataTopic[inTopic]
            self.processValue(c, jdata['value'])
            self.update()
        elif inTopic == 'Basic/Report Attributes/0xFF01':
            jdata = json.loads(data)
            for i in jdata['value']:
                u = False
                if i in self.XiaomiFields:
                    c = self.XiaomiFields[i]
                    vraw = jdata['value'][i]['value']
                    self.processValue(c, vraw)
                    u = True
                if u:
                    self.update()

    def processValue(self, c, vraw):
        vtype = c[0]
        if vtype == "bool":
            v = vraw
        elif vtype == "map8":
            v = vraw[0]
        else:
            v = float(vraw) * vtype
        c[1](self, v)

    def setXiaomiBattery(self, value):
        self.batt = int((value - 2.765)*100)

    # Overwite below definitions in derived object
    def update(self):
        pass

    DataTopic = {
        #"Temperature Measurement/Report Attributes/MeasuredValue": [0.01, setTemperature],
    }
    
    XiaomiFields = {
        #"1": [0.001, XiaomiSensorWithBatteryAndLinkquality.setXiaomiBattery],
    }


class TempHumBaro(XiaomiSensorWithBatteryAndLinkquality):
    def __init__(self, devices, deviceObj):
        super().__init__(devices, deviceObj)
        #sValue
        (self.temp, self.hum, self.hum_stat, self.baro, self.forecast) = self.deviceObj.sValue.split(';')
        # Temperature;Humidity;Humidity Status;Barometer;Forecast
        self.temp = float(self.temp)
        self.hum = float(self.hum)
        self.hum_stat = 0
        self.baro = float(self.baro)
        self.forecast = 0

    TypeName = "Temp+Hum+Baro"
    Type = 84
    
    @staticmethod
    def registerDevice(devices, createDevice, deviceID, topic, data):
        m = _getSensorModel(topic, data)
        if m == "lumi.weather":
            _createDeviceByName(devices, createDevice, deviceID, TempHumBaro.TypeName)

    @staticmethod
    def getAdapter(devices, deviceObj):
        if deviceObj.Type == TempHumBaro.Type:
            return TempHumBaro(devices, deviceObj)

    def setTemperature(self, value):
        self.temp = value
        
    def setHumidity(self, value):
        self.hum = value
        
    def setPressure(self, value):
        self.baro = value

    def update(self):
        sValue = ';'.join((format(self.temp, '.2f'), format(self.hum, '.2f'), str(self.hum_stat), format(self.baro, '.2f'), str(self.forecast)))
        self.deviceObj.Update(0, sValue, BatteryLevel=self.batt, SignalLevel=self.signal)
    
    DataTopic = {
        "Temperature Measurement/Report Attributes/MeasuredValue": [0.01, setTemperature],
        "Relative Humidity Measurement/Report Attributes/MeasuredValue": [0.01, setHumidity],
        "Pressure Measurement/Report Attributes/ScaledValue": [0.1, setPressure]
    }
    
    XiaomiFields = {
        "1": [0.001, XiaomiSensorWithBatteryAndLinkquality.setXiaomiBattery],
        "100": [0.01, setTemperature],
        "101": [0.01, setHumidity],
        "102": [0.01, setPressure]
    }


_timers = {}
_timersLock = threading.Lock()

_allowTimers = True

class MotionSensor(XiaomiSensorWithBatteryAndLinkquality):
    def __init__(self, devices, deviceObj):
        super().__init__(devices, deviceObj)
        #nValue
        self.value = self.deviceObj.nValue
        self.illuminance = self.deviceObj.sValue
        self.motionTimeout = 2*60
        
    Type = 244
    SubType = 73
    SwitchType = 8
    
    @staticmethod
    def registerDevice(devices, createDevice, deviceID, topic, data):
        m = _getSensorModel(topic, data)
        if m == "lumi.sensor_motion.aq2":
            _createDeviceByType(devices, createDevice, deviceID, MotionSensor.Type, MotionSensor.SubType, MotionSensor.SwitchType)

    @staticmethod
    def getAdapter(devices, deviceObj):
        if deviceObj.Type == MotionSensor.Type and deviceObj.SubType == MotionSensor.SubType and deviceObj.SwitchType == MotionSensor.SwitchType:
            return MotionSensor(devices, deviceObj)

    def update(self):
        global _allowTimers
        global _timersLock

        _timersLock.acquire()
        try:
            obj = self.deviceObj
            if not (self.value == obj.nValue and self.illuminance == obj.sValue and self.batt == obj.BatteryLevel and self.signal == obj.SignalLevel):
                self.deviceObj.Update(self.value, self.illuminance, BatteryLevel=self.batt, SignalLevel=self.signal)
            if self.value == 1 and _allowTimers:
                self.updateTimer()
        finally:
            _timersLock.release()
            
    # Called from CriticalSection
    def updateTimer(self):
        global _timers

        devId = self.deviceObj.DeviceID
        if devId in _timers:
            t = _timers[devId][1].cancel()
        tm = threading.Timer(self.motionTimeout, MotionSensor.timerCallback, [self])
        _timers[devId] = [self, tm]
        tm.start()
    
    def timerCallback(self):
        global _timers
        global _timersLock
        
        _timersLock.acquire()
        try:
            devId = self.deviceObj.DeviceID
            self.deviceObj.Update(0, self.illuminance)
            del _timers[devId]
        finally:
            _timersLock.release()

    def setIlluminance(self, value):
        #self.illuminance = str(value)
        pass

    def setOccupancy(self, value):
        self.value = int(bool(value))
        
    DataTopic = {
        "Illuminance Measurement/Report Attributes/0x0000": [1, setIlluminance],
        "Occupancy Sensing/Report Attributes/Occupancy": ["map8", setOccupancy]
    }


    XiaomiFields = {
        "1": [0.001, XiaomiSensorWithBatteryAndLinkquality.setXiaomiBattery],
        #"100": ["bool", setOccupancy]
    }


class DoorSensor(XiaomiSensorWithBatteryAndLinkquality):
    def __init__(self, devices, deviceObj):
        super().__init__(devices, deviceObj)
        #nValue
        self.value = self.deviceObj.nValue
        
    Type = 244
    SubType = 73
    SwitchType = 11
    
    @staticmethod
    def registerDevice(devices, createDevice, deviceID, topic, data):
        m = _getSensorModel(topic, data)
        if m == "lumi.sensor_magnet.aq2":
            _createDeviceByType(devices, createDevice, deviceID, DoorSensor.Type, DoorSensor.SubType, DoorSensor.SwitchType)

    @staticmethod
    def getAdapter(devices, deviceObj):
        if deviceObj.Type == DoorSensor.Type and deviceObj.SubType == DoorSensor.SubType and deviceObj.SwitchType == DoorSensor.SwitchType:
            return DoorSensor(devices, deviceObj)

    def update(self):
        obj = self.deviceObj
        if not (self.value == obj.nValue and self.batt == obj.BatteryLevel and self.signal == obj.SignalLevel):
            self.deviceObj.Update(self.value, "", BatteryLevel=self.batt, SignalLevel=self.signal)
            
    def setDoorOpen(self, value):
        self.value = int(bool(value))
        
    DataTopic = {
        "OnOff/Report Attributes/OnOff": ["bool", setDoorOpen],
    }

    XiaomiFields = {
        "1": [0.001, XiaomiSensorWithBatteryAndLinkquality.setXiaomiBattery],
        "100": ["bool", setDoorOpen]
    }


ProxyObjects = [TempHumBaro, MotionSensor, DoorSensor]
