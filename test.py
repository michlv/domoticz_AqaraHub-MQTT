#!/usr/bin/env python3

import unittest
import adapter

class TestTopic(unittest.TestCase):

    def testRoot(self):
        t = adapter.Topic("AqaraHub1", "AqaraHub2/XXYYCC/linkquality")
        self.assertEqual(t.getExpectedRootTopic(), "AqaraHub1")
        self.assertEqual(t.getRootTopic(), "AqaraHub2")
        self.assertFalse(t.checkRootTopic())

    def testTopic(self):
        t = adapter.Topic("AqaraHub", "AqaraHub/XXYYCC/linkquality")
        self.assertEqual(t.getExpectedRootTopic(), "AqaraHub")
        self.assertEqual(t.getRootTopic(), "AqaraHub")
        self.assertTrue(t.checkRootTopic())
        self.assertEqual(t.getDeviceID(), "XXYYCC")
        self.assertEqual(t.getTopic(), "linkquality")
        self.assertEqual(t.getInTopic(), None)

    def testIn(self):
        t = adapter.Topic("AqaraHub", "AqaraHub/XXYYCC/1/in/Temperature")
        self.assertEqual(t.getExpectedRootTopic(), "AqaraHub")
        self.assertEqual(t.getRootTopic(), "AqaraHub")
        self.assertTrue(t.checkRootTopic())
        self.assertEqual(t.getDeviceID(), "XXYYCC")
        self.assertEqual(t.getTopic(), "1/in/Temperature")
        self.assertEqual(t.getInTopic(), "Temperature")
        

_devices = {}

class DeviceIDTHBMock:
    def __init__(self, Name=None, Unit=None, TypeName=None, DeviceID=None, Used=None):
        self.Name = Name
        self.Unit = Unit
        self.TypeName = TypeName
        self.Type = 84
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


class TestTempHumBaroAdapter(unittest.TestCase):
    def getMock(self):
        global _devices

        _devices = {}
        device = DeviceIDTHBMock()
        a = adapter.TempHumBaro(_devices, device)
        return (_devices, device, a)
    
    def testCreation(self):
        (devices, dev, proxy) = self.getMock()
        self.assertTrue(isinstance(proxy, adapter.TempHumBaro))
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
        t = adapter.Topic('AqaraHub', topic)
        proxy.processData(t, data)
        self.assertEqual(dev.SignalLevel, 1)
        self.assertEqual(dev.BatteryLevel, 255)

    def testTemperature(self):
        (devices, dev, proxy) = self.getMock()
        topic = 'AqaraHub/00158D000272C69E/1/in/Temperature Measurement/Report Attributes/MeasuredValue'
        data = '{"type":"int16","value":2128}'
        t = adapter.Topic('AqaraHub', topic)
        proxy.processData(t, data)
        self.assertEqual(dev.sValue, "21.28;59.33;0;1024.01;0")
        self.assertEqual(dev.SignalLevel, 100)
        self.assertEqual(dev.BatteryLevel, 255)

    def testHumidity(self):
        (devices, dev, proxy) = self.getMock()
        topic = 'AqaraHub/00158D000272C69E/1/in/Relative Humidity Measurement/Report Attributes/MeasuredValue'
        data = '{"type":"uint16","value":3947}'
        t = adapter.Topic('AqaraHub', topic)
        proxy.processData(t, data)
        self.assertEqual(dev.sValue, "11.22;39.47;0;1024.01;0")
        self.assertEqual(dev.SignalLevel, 100)
        self.assertEqual(dev.BatteryLevel, 255)

    def testPressure(self):
        (devices, dev, proxy) = self.getMock()
        topic = 'AqaraHub/00158D000272C69E/1/in/Pressure Measurement/Report Attributes/ScaledValue'
        data = '{"type":"int16","value":9973}'
        t = adapter.Topic('AqaraHub', topic)
        proxy.processData(t, data)
        self.assertEqual(dev.sValue, "11.22;59.33;0;997.30;0")
        self.assertEqual(dev.SignalLevel, 100)
        self.assertEqual(dev.BatteryLevel, 255)
        
    def testXiaomiBlock(self):
        (devices, dev, proxy) = self.getMock()
        topic = 'AqaraHub/00158D000272C69E/1/in/Basic/Report Attributes/0xFF01'
        data = '{"type":"xiaomi_ff01","value":{"1":{"type":"uint16","value":3005},"10":{"type":"uint16","value":0},"100":{"type":"int16","value":2206},"101":{"type":"uint16","value":5527},"102":{"type":"int32","value":102982},"4":{"type":"uint16","value":17320},"5":{"type":"uint16","value":6},"6":{"type":"uint40","value":1}}}'
        t = adapter.Topic('AqaraHub', topic)
        proxy.processData(t, data)
        self.assertEqual(dev.sValue, "22.06;55.27;0;1029.82;0")
        self.assertEqual(dev.BatteryLevel, 80)
        self.assertEqual(dev.SignalLevel, 100)

    def testCreateAndUpdate(self):
        (devices, dev, proxy) = self.getMock()
        topic = 'AqaraHub/00158D0002786756/1/in/Basic/Report Attributes/ModelIdentifier'
        data = '{"type":"string","value":"lumi.weather"}'
        adapter.onData(devices, DeviceIDTHBMock, 'AqaraHub', topic, data)
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
        adapter.onData(devices, DeviceIDTHBMock, 'AqaraHub', topic, data)
        dev = devices[1]
        self.assertEqual(dev.sValue, "11.22;59.33;0;1024.01;0")
        self.assertEqual(dev.BatteryLevel, 255)
        self.assertEqual(dev.SignalLevel, 100)

        # Update
        topic = 'AqaraHub/00158D0002786756/1/in/Basic/Report Attributes/0xFF01'
        adapter.onData(devices, DeviceIDTHBMock, 'AqaraHub', topic, data)
        dev = devices[1]
        self.assertEqual(dev.sValue, "22.06;55.27;0;1029.82;0")
        self.assertEqual(dev.BatteryLevel, 80)
        self.assertEqual(dev.SignalLevel, 100)
    
    def testTypeNameNoMatch1(self):
        (devices, dev, proxy) = self.getMock()
        topic = 'AqaraHub/00158D0002786756/1/in/Basic/Report Attributes/ModelIdentifier'
        data = '{"type":"string","value":"lumi.XXXXX"}'
        adapter.onData(devices, DeviceIDTHBMock, 'AqaraHub', topic, data)
        self.assertEqual(len(devices), 0)

    def testTypeNameNoMatch2(self):
        (devices, dev, proxy) = self.getMock()
        topic = 'AqaraHub/00158D0002786756/1/in/XX/YY'
        data = '10'
        adapter.onData(devices, DeviceIDTHBMock, 'AqaraHub', topic, data)
        self.assertEqual(len(devices), 0)


class DeviceIDMSMock:
    def __init__(self, Name=None, Unit=None, Type=None, Subtype=None, Switchtype=None, DeviceID=None, Used=None):
        self.Name = Name
        self.Unit = Unit
        self.Type = Type
        self.SubType = Subtype
        self.SwitchType = Switchtype
        self.DeviceID = DeviceID
        self.Used = Used
        self.nValue = 0
        self.sValue = ""
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


class TestMotionSensorAdapter(unittest.TestCase):
    def getMock(self):
        global _devices

        _devices = {}
        device = DeviceIDMSMock()
        a = adapter.MotionSensor(_devices, device)
        return (_devices, device, a)
    
    def testCreation(self):
        (devices, dev, proxy) = self.getMock()
        self.assertTrue(isinstance(proxy, adapter.MotionSensor))
        self.assertEqual(dev.nValue, 0)
        self.assertEqual(dev.sValue, "")
        self.assertEqual(proxy.value, 0)
        proxy.setOccupancy("true")
        proxy.update()
        self.assertEqual(dev.nValue, 1)
        self.assertEqual(dev.sValue, "")
        self.assertEqual(dev.BatteryLevel, 255)
        self.assertEqual(dev.SignalLevel, 100)

    def testSetOccupancy(self):
        (devices, dev, proxy) = self.getMock()
        self.assertEqual(dev.nValue, 0)
        self.assertEqual(dev.sValue, "")
        proxy.setOccupancy("true")
        proxy.update()
        self.assertEqual(dev.nValue, 1)
        self.assertEqual(dev.sValue, "")

    def testLinkQuality(self):
        (devices, dev, proxy) = self.getMock()
        topic = 'AqaraHub/00158D000272C69E/linkquality'
        data = '18'
        t = adapter.Topic('AqaraHub', topic)
        proxy.processData(t, data)
        self.assertEqual(dev.SignalLevel, 1)
        self.assertEqual(dev.BatteryLevel, 255)

    def testIlluminance(self):
        (devices, dev, proxy) = self.getMock()
        topic = 'AqaraHub/00158D0002E96C81/1/in/Illuminance Measurement/Report Attributes/0x0000'
        data = '{"type":"uint16","value":6}'
        t = adapter.Topic('AqaraHub', topic)
        proxy.processData(t, data)
        self.assertEqual(dev.nValue, 0)
        self.assertEqual(dev.sValue, "")
        self.assertEqual(dev.SignalLevel, 100)
        self.assertEqual(dev.BatteryLevel, 255)

    def testOccupancy(self):
        (devices, dev, proxy) = self.getMock()
        topic = 'AqaraHub/00158D0002E96C81/1/in/Occupancy Sensing/Report Attributes/Occupancy'
        data = '{"type":"map8","value":[true,false,false,false,false,false,false,false]}'
        t = adapter.Topic('AqaraHub', topic)
        proxy.processData(t, data)
        self.assertEqual(dev.nValue, 1)
        self.assertEqual(dev.sValue, "")
        self.assertEqual(dev.SignalLevel, 100)
        self.assertEqual(dev.BatteryLevel, 255)

    def testCreateAndUpdate(self):
        (devices, dev, proxy) = self.getMock()
        topic = 'AqaraHub/00158D0002E96C81/1/in/Basic/Report Attributes/ModelIdentifier'
        data = '{"type":"string","value":"lumi.sensor_motion.aq2"}'
        adapter.onData(devices, DeviceIDMSMock, 'AqaraHub', topic, data)
        self.assertEqual(len(devices), 1)
        self.assertTrue(1 in devices)
        self.assertTrue(devices[1].Name, "00158D0002E96C81")
        self.assertTrue(devices[1].Unit, 1)
        self.assertTrue(devices[1].Type, 244)
        self.assertTrue(devices[1].SubType, 73)
        self.assertTrue(devices[1].SwitchType, 8)
        self.assertTrue(devices[1].DeviceID, "00158D0002E96C81")
        self.assertTrue(devices[1].Used, 1)

        # No Update, different ID
        topic = 'AqaraHub/00158D0002E96C81XX/1/in/Basic/Report Attributes/0xFF01'
        data = '{"type":"xiaomi_ff01","value":{"1":{"type":"uint16","value":3055},"10":{"type":"uint16","value":0},"100":{"type":"bool","value":true},"11":{"type":"uint16","value":10},"3":{"type":"int8","value":30},"4":{"type":"uint16","value":424},"5":{"type":"uint16","value":9},"6":{"type":"uint40","value":0}}}'

        adapter.onData(devices, DeviceIDMSMock, 'AqaraHub', topic, data)
        dev = devices[1]
        self.assertEqual(dev.nValue, 0)
        self.assertEqual(dev.sValue, "")
        self.assertEqual(dev.BatteryLevel, 255)
        self.assertEqual(dev.SignalLevel, 100)

        # Update
        topic = 'AqaraHub/00158D0002E96C81/1/in/Basic/Report Attributes/0xFF01'
        adapter.onData(devices, DeviceIDMSMock, 'AqaraHub', topic, data)
        dev = devices[1]
        self.assertEqual(dev.nValue, 1)
        self.assertEqual(dev.sValue, "")
        self.assertEqual(dev.BatteryLevel, 85)
        self.assertEqual(dev.SignalLevel, 100)


if __name__ == '__main__':
    unittest.main()
