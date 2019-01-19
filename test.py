#!/usr/bin/env python3

import unittest
import Proxy

class TestTopic(unittest.TestCase):

    def testRoot(self):
        t = Proxy.Topic("AqaraHub1", "AqaraHub2/XXYYCC/linkquality")
        self.assertEqual(t.getExpectedRootTopic(), "AqaraHub1")
        self.assertEqual(t.getRootTopic(), "AqaraHub2")
        self.assertFalse(t.checkRootTopic())

    def testTopic(self):
        t = Proxy.Topic("AqaraHub", "AqaraHub/XXYYCC/linkquality")
        self.assertEqual(t.getExpectedRootTopic(), "AqaraHub")
        self.assertEqual(t.getRootTopic(), "AqaraHub")
        self.assertTrue(t.checkRootTopic())
        self.assertEqual(t.getDeviceID(), "XXYYCC")
        self.assertEqual(t.getTopic(), "linkquality")
        self.assertEqual(t.getInTopic(), None)

    def testIn(self):
        t = Proxy.Topic("AqaraHub", "AqaraHub/XXYYCC/1/in/Temperature")
        self.assertEqual(t.getExpectedRootTopic(), "AqaraHub")
        self.assertEqual(t.getRootTopic(), "AqaraHub")
        self.assertTrue(t.checkRootTopic())
        self.assertEqual(t.getDeviceID(), "XXYYCC")
        self.assertEqual(t.getTopic(), "1/in/Temperature")
        self.assertEqual(t.getInTopic(), "Temperature")
        

_devices = {}

class DeviceIDMock:
    def __init__(self, Name=None, Unit=None, TypeName=None, DeviceID=None, Used=None):
        self.Name = Name
        self.Unit = Unit
        self.TypeName = TypeName
        self.DeviceID = DeviceID
        self.Used = Used
        # Temperature;Humidity;Humidity Status;Barometer;Forecast
        self.nValue = 0
        self.sValue = "11.22;59.33;0;1024.01;0"
        self.SignalLevel = 100
        self.BatteryLevel = 255

    def Create(self):
        global _devices
    
        _devices[self.Unit] = self

    def Update(self, nValue, sValue, BatteryLevel=None, SignalLevel=None):
        self.nValue = nValue
        self.sValue = sValue
        if BatteryLevel is not None:
            self.BatteryLevel = BatteryLevel
        if SignalLevel is not None:
            self.SignalLevel = SignalLevel


class TestTempHumBaroProxy(unittest.TestCase):
    def getMock(self):
        global _devices

        _devices = {}
        device = DeviceIDMock()
        adapter = Proxy.TempHumBaro(_devices, device)
        return (_devices, device, adapter)
    
    def testCreation(self):
        (devices, dev, proxy) = self.getMock()
        self.assertTrue(isinstance(proxy, Proxy.TempHumBaro))
        self.assertEqual(dev.sValue, "11.22;59.33;0;1024.01;0")
        self.assertEqual(proxy.temp, 11.22)
        self.assertEqual(proxy.hum, 59.33)
        self.assertEqual(proxy.baro, 1024.01)
        self.assertEqual(proxy.batt, 255)
        proxy.setTemperature(22.11)
        proxy.setHumidity(63.21)
        proxy.setPressure(995.23)
        proxy.update()
        self.assertEqual(dev.sValue, "22.11;63.21;0;995.23;0")        
        self.assertEqual(dev.BatteryLevel, 255)
        self.assertEqual(dev.SignalLevel, 100)

    def testSetTemp(self):
        (devices, dev, proxy) = self.getMock()
        self.assertEqual(dev.sValue, "11.22;59.33;0;1024.01;0")
        proxy.setTemperature(22.11)
        proxy.update()
        self.assertEqual(dev.sValue, "22.11;59.33;0;1024.01;0")

    def testSetHum(self):
        (devices, dev, proxy) = self.getMock()
        self.assertEqual(dev.sValue, "11.22;59.33;0;1024.01;0")
        proxy.setHumidity(63.26)
        proxy.update()
        self.assertEqual(dev.sValue, "11.22;63.26;0;1024.01;0")

    def testSetBaro(self):
        (devices, dev, proxy) = self.getMock()
        self.assertEqual(dev.sValue, "11.22;59.33;0;1024.01;0")
        proxy.setPressure(995.24)
        proxy.update()
        self.assertEqual(dev.sValue, "11.22;59.33;0;995.24;0")
        
    def testLinkQuality(self):
        (devices, dev, proxy) = self.getMock()
        topic = 'AqaraHub/00158D000272C69E/linkquality'
        data = '18'
        t = Proxy.Topic('AqaraHub', topic)
        proxy.processData(t, data)
        self.assertEqual(dev.SignalLevel, 1)
        self.assertEqual(dev.BatteryLevel, 255)

    def testTemperature(self):
        (devices, dev, proxy) = self.getMock()
        topic = 'AqaraHub/00158D000272C69E/1/in/Temperature Measurement/Report Attributes/MeasuredValue'
        data = '{"type":"int16","value":2128}'
        t = Proxy.Topic('AqaraHub', topic)
        proxy.processData(t, data)
        self.assertEqual(dev.sValue, "21.28;59.33;0;1024.01;0")
        self.assertEqual(dev.SignalLevel, 100)
        self.assertEqual(dev.BatteryLevel, 255)

    def testHumidity(self):
        (devices, dev, proxy) = self.getMock()
        topic = 'AqaraHub/00158D000272C69E/1/in/Relative Humidity Measurement/Report Attributes/MeasuredValue'
        data = '{"type":"uint16","value":3947}'
        t = Proxy.Topic('AqaraHub', topic)
        proxy.processData(t, data)
        self.assertEqual(dev.sValue, "11.22;39.47;0;1024.01;0")
        self.assertEqual(dev.SignalLevel, 100)
        self.assertEqual(dev.BatteryLevel, 255)

    def testPressure(self):
        (devices, dev, proxy) = self.getMock()
        topic = 'AqaraHub/00158D000272C69E/1/in/Pressure Measurement/Report Attributes/ScaledValue'
        data = '{"type":"int16","value":9973}'
        t = Proxy.Topic('AqaraHub', topic)
        proxy.processData(t, data)
        self.assertEqual(dev.sValue, "11.22;59.33;0;997.30;0")
        self.assertEqual(dev.SignalLevel, 100)
        self.assertEqual(dev.BatteryLevel, 255)
        
    def testXiaomiBlock(self):
        (devices, dev, proxy) = self.getMock()
        topic = 'AqaraHub/00158D000272C69E/1/in/Basic/Report Attributes/0xFF01'
        data = '{"type":"xiaomi_ff01","value":{"1":{"type":"uint16","value":3005},"10":{"type":"uint16","value":0},"100":{"type":"int16","value":2206},"101":{"type":"uint16","value":5527},"102":{"type":"int32","value":102982},"4":{"type":"uint16","value":17320},"5":{"type":"uint16","value":6},"6":{"type":"uint40","value":1}}}'
        t = Proxy.Topic('AqaraHub', topic)
        proxy.processData(t, data)
        self.assertEqual(dev.sValue, "22.06;55.27;0;1029.82;0")
        self.assertEqual(dev.BatteryLevel, 80)
        self.assertEqual(dev.SignalLevel, 100)

    def testCreateAndUpdate(self):
        (devices, dev, proxy) = self.getMock()
        topic = 'AqaraHub/00158D0002786756/1/in/Basic/Report Attributes/ModelIdentifier'
        data = '{"type":"string","value":"lumi.weather"}'
        Proxy.onData(devices, DeviceIDMock, 'AqaraHub', topic, data)
        self.assertEqual(len(devices), 1)
        self.assertTrue(1 in devices)
        self.assertTrue(devices[1].Name, "00158D0002786756")
        self.assertTrue(devices[1].Unit, 1)
        self.assertTrue(devices[1].TypeName, "Temp+Hum+Baro")
        self.assertTrue(devices[1].DeviceID, "00158D0002786756")
        self.assertTrue(devices[1].Used, 1)

        # No Update, different ID
        topic = 'AqaraHub/00158D0002786756XX/1/in/Basic/Report Attributes/0xFF01'
        data = '{"type":"xiaomi_ff01","value":{"1":{"type":"uint16","value":3005},"10":{"type":"uint16","value":0},"100":{"type":"int16","value":2206},"101":{"type":"uint16","value":5527},"102":{"type":"int32","value":102982},"4":{"type":"uint16","value":17320},"5":{"type":"uint16","value":6},"6":{"type":"uint40","value":1}}}'
        Proxy.onData(devices, DeviceIDMock, 'AqaraHub', topic, data)
        dev = devices[1]
        self.assertEqual(dev.sValue, "11.22;59.33;0;1024.01;0")
        self.assertEqual(dev.BatteryLevel, 255)
        self.assertEqual(dev.SignalLevel, 100)

        # Update
        topic = 'AqaraHub/00158D0002786756/1/in/Basic/Report Attributes/0xFF01'
        Proxy.onData(devices, DeviceIDMock, 'AqaraHub', topic, data)
        dev = devices[1]
        self.assertEqual(dev.sValue, "22.06;55.27;0;1029.82;0")
        self.assertEqual(dev.BatteryLevel, 80)
        self.assertEqual(dev.SignalLevel, 100)
    
    def testTypeNameNoMatch1(self):
        (devices, dev, proxy) = self.getMock()
        topic = 'AqaraHub/00158D0002786756/1/in/Basic/Report Attributes/ModelIdentifier'
        data = '{"type":"string","value":"lumi.XXXXX"}'
        Proxy.onData(devices, DeviceIDMock, 'AqaraHub', topic, data)
        self.assertEqual(len(devices), 0)

    def testTypeNameNoMatch2(self):
        (devices, dev, proxy) = self.getMock()
        topic = 'AqaraHub/00158D0002786756/1/in/XX/YY'
        data = '10'
        Proxy.onData(devices, DeviceIDMock, 'AqaraHub', topic, data)
        self.assertEqual(len(devices), 0)
        

if __name__ == '__main__':
    unittest.main()
