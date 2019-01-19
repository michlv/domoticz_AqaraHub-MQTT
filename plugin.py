# Python Plugin AqaraHub MQTT
#
# Author: michlv
#
"""
<plugin key="AqaraHub-MQTT" name="AqaraHub (MQTT)" author="michlv" version="0.0.1" externallink="https://github.com/Frans-Willem/AqaraHub">
    <params>
        <param field="Address" label="IP Address" width="200px" required="true" default="nasvmln"/>
        <param field="Port" label="Connection" required="true" width="200px">
            <options>
                <option label="Unencrypted" value="1883" default="true" />
                <option label="Encrypted" value="8883" />
                <option label="Encrypted (Client Certificate)" value="8884" />
            </options>
        </param>
        <param field="Username" label="Username" width="200px"/>
        <param field="Password" label="Password" width="200px"/>
        <param field="Mode1" label="Topic" width="200px" required="true" default="AqaraHub"/>
        <param field="Mode6" label="Debug" width="75px">
            <options>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal"  default="true" />
            </options>
        </param>
    </params>
</plugin>
"""
import Domoticz
import random
import time
import Proxy

PluginName = "AqaraHub-MQTT"

class BasePlugin:
    enabled = False
    mqttConn = None
    counter = 0
    
    def __init__(self):
        return

    def onStart(self):
        if Parameters["Mode6"] == "Debug":
            Domoticz.Debugging(1)
        DumpConfigToLog()
        self.doConnect()

    def onConnect(self, Connection, Status, Description):
        if (Status == 0):
            Domoticz.Debug("MQTT connected successfully.")
            id = "Domoticz_{0}_{1}_{2}".format(PluginName, int(time.time()), random.randint(1000, 9999))
            sendData = { 'Verb' : 'CONNECT',
                         'ID' : id }
            Connection.Send(sendData)
        else:
            Domoticz.Log("Failed to connect ("+str(Status)+") to: "+Parameters["Address"]+":"+Parameters["Port"]+" with error: "+Description)

    def onMessage(self, Connection, Data):
        verb=Data["Verb"]
        Domoticz.Log("onMessage called with: "+verb)
        DumpDictionaryToLog(Data)
        if (verb == "CONNACK" and Data['Status'] == 0):
            self.doSubscribe(Connection)
        elif (verb == 'PUBLISH'):
            t = Proxy.Topic(Parameters["Mode1"], Data['Topic'])
            if t.checkRootTopic() == False:
                Domoticz.Error("Unexpected root topic element {1} ({0})".format(t.getExpectedRootTopic(), t.getRootTopic()))
            else:
                self.processData(t.getDeviceID(), t, Data['Payload'].decode())
            
    def onDisconnect(self, Connection):
        Domoticz.Log("onDisconnect called")

    def onHeartbeat(self):
        Domoticz.Log("onHeartbeat called: "+str(self.counter))
        if (self.mqttConn.Connected()):
            if ((self.counter % 6) == 0):
                self.mqttConn.Send({ 'Verb' : 'PING' })
            #elif (self.counter % 45 == 0):
            #    self.mqttConn.Send({'Verb' : 'UNSUBSCRIBE', 'Topics': [Parameters["Mode1"]]})
            #elif (self.counter % 50 == 0):
            #    self.mqttConn.Send({ 'Verb' : 'DISCONNECT' })
            self.counter = self.counter + 1
        else:
            self.doConnect()

    def doSubscribe(self, Connection):
        Connection.Send({'Verb' : 'SUBSCRIBE', 'PacketIdentifier': 1001, 'Topics': [{'Topic':Parameters["Mode1"]+"/#", 'QoS': 0}]})

    def doConnect(self):
        Protocol = "MQTT"
        if (Parameters["Port"] == "8883"):
            Protocol = "MQTTS"
        self.mqttConn = Domoticz.Connection(Name=PluginName, Transport="TCP/IP", Protocol=Protocol, Address=Parameters["Address"], Port=Parameters["Port"])
        self.mqttConn.Connect()

    def processData(self, deviceID, topic, data):
        devProxy = self.getDeviceProxy(deviceID)
        if devProxy:
            devProxy.processData(topic, data)
        else:
            self.registerDevice(deviceID, topic, data)

    def getDeviceProxy(self, deviceID):
        for Unit in Devices:
            if Devices[Unit].DeviceID == deviceID:
                dev = Devices[Unit]
                Domoticz.Log("Found device unit: {0}".format(dev.Unit))
                return Proxy.get(dev)
        return None
    
    def registerDevice(self, deviceID, topic, data):
        umax = 0
        for i in Devices:
            umax = max(umax, Devices[i].Unit)
        type = Proxy.getTypeName(topic, data)
        if type:
            Domoticz.Log("Found proxy of type {0}, registering new device {1}.".format(type, deviceID))
            Domoticz.Device(Name=deviceID, Unit=umax+1, TypeName=type, DeviceID=deviceID, Used=1).Create()
        else:
            Domoticz.Debug("Unknown device device {0}".format(deviceID))

    
global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

    # Generic helper functions
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return

def DumpDictionaryToLog(theDict, Depth=""):
    if isinstance(theDict, dict):
        for x in theDict:
            if isinstance(theDict[x], dict):
                Domoticz.Log(Depth+"> Dict '"+x+"' ("+str(len(theDict[x]))+"):")
                DumpDictionaryToLog(theDict[x], Depth+"---")
            elif isinstance(theDict[x], list):
                Domoticz.Log(Depth+"> List '"+x+"' ("+str(len(theDict[x]))+"):")
                DumpListToLog(theDict[x], Depth+"---")
            elif isinstance(theDict[x], str):
                Domoticz.Log(Depth+">'" + x + "':'" + str(theDict[x]) + "'")
            else:
                Domoticz.Log(Depth+">'" + x + "': " + str(theDict[x]))

def DumpListToLog(theList, Depth):
    if isinstance(theList, list):
        for x in theList:
            if isinstance(x, dict):
                Domoticz.Log(Depth+"> Dict ("+str(len(x))+"):")
                DumpDictionaryToLog(x, Depth+"---")
            elif isinstance(x, list):
                Domoticz.Log(Depth+"> List ("+str(len(theList))+"):")
                DumpListToLog(x, Depth+"---")
            elif isinstance(x, str):
                Domoticz.Log(Depth+">'" + x + "':'" + str(theList[x]) + "'")
            else:
                Domoticz.Log(Depth+">'" + x + "': " + str(theList[x]))

                
