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
        

class DeviceIDMock:
    def __init__(self):
        self.DeviceID = ""
        # Temperature;Humidity;Humidity Status;Barometer;Forecast
        self.nValue = 0
        self.sValue = "11.22;59.33;0;1024.01;0"
        self.SignalLevel = 100
        self.BatteryLevel = 255

    def Create(self):
        pass

    def Update(self, nValue, sValue, BatteryLevel=None, SignalLevel=None):
        self.nValue = nValue
        self.sValue = sValue
        if BatteryLevel is not None:
            self.BatteryLevel = BatteryLevel
        if SignalLevel is not None:
            self.SignalLevel = SignalLevel


class TestTempHumBaroProxy(unittest.TestCase):
    def testCreation(self):
        dev = DeviceIDMock()
        proxy = Proxy.get(dev)
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
        self.assertEqual(proxy.batt, 255)

    def testSetTemp(self):
        dev = DeviceIDMock()
        proxy = Proxy.get(dev)
        self.assertEqual(dev.sValue, "11.22;59.33;0;1024.01;0")
        proxy.setTemperature(22.11)
        proxy.update()
        self.assertEqual(dev.sValue, "22.11;59.33;0;1024.01;0")

    def testSetHum(self):
        dev = DeviceIDMock()
        proxy = Proxy.get(dev)
        self.assertEqual(dev.sValue, "11.22;59.33;0;1024.01;0")
        proxy.setHumidity(63.26)
        proxy.update()
        self.assertEqual(dev.sValue, "11.22;63.26;0;1024.01;0")

    def testSetBaro(self):
        dev = DeviceIDMock()
        proxy = Proxy.get(dev)
        self.assertEqual(dev.sValue, "11.22;59.33;0;1024.01;0")
        proxy.setPressure(995.24)
        proxy.update()
        self.assertEqual(dev.sValue, "11.22;59.33;0;995.24;0")
        
    def testLinkQuality(self):
        dev = DeviceIDMock();
        proxy = Proxy.get(dev)
        topic = 'AqaraHub/00158D000272C69E/linkquality'
        data = b'18'
        t = Proxy.Topic('AqaraHub', topic)
        proxy.processData(t, data)
        self.assertEqual(dev.SignalLevel, 18)
        self.assertEqual(proxy.batt, 255)

    def testTemperature(self):
        dev = DeviceIDMock();
        proxy = Proxy.get(dev)
        topic = 'AqaraHub/00158D000272C69E/1/in/Temperature Measurement/Report Attributes/MeasuredValue'
        data = b'{"type":"int16","value":2128}'
        t = Proxy.Topic('AqaraHub', topic)
        proxy.processData(t, data)
        self.assertEqual(dev.sValue, "21.28;59.33;0;1024.01;0")
        self.assertEqual(proxy.batt, 255)

    def testHumidity(self):
        dev = DeviceIDMock();
        proxy = Proxy.get(dev)
        topic = 'AqaraHub/00158D000272C69E/1/in/Relative Humidity Measurement/Report Attributes/MeasuredValue'
        data = b'{"type":"uint16","value":3947}'
        t = Proxy.Topic('AqaraHub', topic)
        proxy.processData(t, data)
        self.assertEqual(dev.sValue, "11.22;39.47;0;1024.01;0")
        self.assertEqual(proxy.batt, 255)

    def testPressure(self):
        dev = DeviceIDMock();
        proxy = Proxy.get(dev)
        topic = 'AqaraHub/00158D000272C69E/1/in/Pressure Measurement/Report Attributes/ScaledValue'
        data = b'{"type":"int16","value":9973}'
        t = Proxy.Topic('AqaraHub', topic)
        proxy.processData(t, data)
        self.assertEqual(dev.sValue, "11.22;59.33;0;997.30;0")
        self.assertEqual(proxy.batt, 255)
        
    def testXiaomiBlock(self):
        dev = DeviceIDMock();
        proxy = Proxy.get(dev)
        topic = 'AqaraHub/00158D000272C69E/1/in/Basic/Report Attributes/0xFF01'
        data = b'{"type":"xiaomi_ff01","value":{"1":{"type":"uint16","value":3005},"10":{"type":"uint16","value":0},"100":{"type":"int16","value":2206},"101":{"type":"uint16","value":5527},"102":{"type":"int32","value":102982},"4":{"type":"uint16","value":17320},"5":{"type":"uint16","value":6},"6":{"type":"uint40","value":1}}}'
        t = Proxy.Topic('AqaraHub', topic)
        proxy.processData(t, data)
        self.assertEqual(dev.sValue, "22.06;55.27;0;1029.82;0")
        self.assertEqual(dev.BatteryLevel, 80)
        

if __name__ == '__main__':
    unittest.main()
