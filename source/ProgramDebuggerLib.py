

from tkinter import *
from Timer import Timer
from Wait import Wait
import json
import re
from EthernetClientInterface import EthernetClientInterface
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from variables import variablesclass

VERSION='1.8.0.5'

class ProcessorCommunicationClass():
    def __init__(self,vars:'variablesclass'):
        self.vars = vars
        #self.t_keep_client_connected = Timer(10,self.fn_keep_client_connected())
        #self.t_keep_client_connected.Stop()
        self.__devices_clientbuffer = ''

        self.__connect_to_system = False
        self.__system_is_connected = False
        self.__connection_manager = Timer(5,self.__f_connection_manager())
        self.__connection_manager.Restart()
        self.__delim = '~END~\x0a'
        self.__rxmatchpattern = '~(RegisterDevices|UpdateDeviceComs|UpdateDevices|Option)~:\d*:?(.*)~END~'

    def open_connect_window(self):
        window2 = Tk()
        window2.title(' Connect To System ')
        window2.geometry('250x75')

        lbl_instructions = Label(window2,text = ' Enter the IP address of the Extron Controller:  ')
        lbl_instructions.grid(column=0,row=0)

        def clear_tb_ip():
            self.vars.ui_view1.ip_address = tb_ip.get(1.0,'end')
            self.vars.ui_view1.ip_address = self.vars.ui_view1.ip_address.strip()
            window2.destroy()
            self.system_connection_start()
        def clear_tb_enter(event):
            clear_tb_ip()
        tb_ip = Text(window2,height=1,width=20)
        tb_ip.grid(column=0,row=2)
        tb_ip.bind('<Return>',clear_tb_enter)
        tb_ip.insert(END,self.vars.ui_view1.ip_address)
        tb_ip.update()
        btn_submit = Button(window2,text='Submit',width=10,height=1,command=clear_tb_ip)
        btn_submit.grid(column=0,row=4)
        #apply focus
        window2.wm_deiconify

    def system_connection_start(self):
        if self.vars.ui_view1.devices_client:
            self.system_connection_stop()
        if not self.vars.ui_view1.devices_client:
            self.vars.ui_view1.SetConnectStatus('Connecting...')
            self.vars.ui_view1.devices_client = EthernetClientInterface(self.vars.ui_view1.ip_address,1988)
            self.SetClient()
        self.__connect_to_system = True
    def system_connection_stop(self):
        self.__connect_to_system = False
        if self.vars.ui_view1.devices_client:
            if 'Connected' in self.vars.ui_view1.system_connected_status:
                self.vars.ui_view1.devices_client.Disconnect()
            self.vars.ui_view1.devices_client = None
            self.vars.ui_view1.system_connected_status = ''

    def fn_keep_client_connected(self):
        def t(timer,count):
            if not self.__system_is_connected and self.vars.ui_view1.devices_client:
                self.vars.ui_view1.SetConnectStatus('Connecting...')
                self.vars.ui_view1.system_connected_status = self.vars.ui_view1.devices_client.Connect()
                if not self.__system_is_connected:
                    self.vars.ui_view1.SetConnectStatus('Timeout')
                elif self.vars.ui_view1.system_connected_status != 'Connected':
                    self.vars.ui_view1.SetConnectStatus('Timeout')
                    self.t_keep_client_connected.Stop()
            elif self.__system_is_connected and self.vars.ui_view1.devices_client:
                self.t_keep_client_connected.Stop()
        return t

    def __f_connection_manager(self):
        def t(timer,count):
            if not self.vars.ui_view1.devices_client:
                return
            if self.__connect_to_system and not self.__system_is_connected:
                self.vars.ui_view1.devices_client.Connect()
            elif self.__system_is_connected and not self.__connect_to_system:
                self.vars.ui_view1.devices_client.Disconnect()
        return t

    def __removesuffix(self,data:'str',end:'str'):
        try:
            return data[data.index(end)+len(end):]
        except:
            return data
    def __HandleRecieveFromClient(self,client,data:'bytes'):
        self.__devices_clientbuffer += data.decode()
        while self.__delim in self.__devices_clientbuffer:
            delim_pos = self.__devices_clientbuffer.index(self.__delim)
            temp_buf = self.__devices_clientbuffer[:delim_pos+len(self.__delim)]
            self.__devices_clientbuffer = self.__removesuffix(self.__devices_clientbuffer,self.__delim)
            matches = re.findall(self.__rxmatchpattern,temp_buf)
            for match in matches:
                match_type = match[0]
                if 'RegisterDevices' == match_type:
                    json_data = match[1]
                    try:
                        device_info = json.loads(json_data)
                    except Exception as e:
                        print('error decoding register devices json from system, error:' + str(e) + '\nRepeat register for device:{}'.format(json_data))
                        device_info = {}
                        self.__devices_clientbuffer = ''
                        self.SendToSystem('~RegisterNext~:{}'.format(json.dumps(list(self.vars.ui_view1.device_info.keys()))))
                        return
                    if 'num_devices' in device_info:
                        print('Current Device {} of {}'.format(len(self.vars.ui_view1.device_info)+1,device_info['num_devices']-1))
                        del device_info['num_devices']
                    try:
                        print('Register device complete:{}'.format(list(device_info.values())[0]['name']))
                    except Exception as e:
                        print('error reading data in device object:' + str(e) + '\nRepeat register for device:{}'.format(json_data))
                        device_info = {}
                        self.__devices_clientbuffer = ''
                        self.SendToSystem('~RegisterNext~:{}'.format(json.dumps(list(self.vars.ui_view1.device_info.keys()))))
                        return
                    self.vars.ui_view1.SetDeviceInfo(device_info)
                    self.vars.ui_view1.SetDeviceList()
                    self.SendToSystem('~RegisterNext~:{}'.format(json.dumps(list(self.vars.ui_view1.device_info.keys()))))
                if 'UpdateDeviceComs' == match_type:
                    json_data = match[1]
                    update = None
                    try:
                        update = json.loads(json_data)
                    except Exception as e:
                        print('error decoding update devices json from system, error:' + str(e))
                    if update:
                        for key in update:
                            self.vars.ui_view1.UpdateDeviceLog(key,update[key])
                if 'UpdateDevices' == match_type:
                    json_data = match[1]

                    update = None
                    try:
                        update = json.loads(json_data)
                    except Exception as e:
                        print('error decoding update devices json from system, error:' + str(e))
                        continue
                    if update:
                        for key in update:
                            if key in self.vars.ui_view1.device_info:
                                Command = self.vars.ui_view1.device_info[key]['status'][update[key]['command']]
                                Qualifier = update[key]['qualifier']
                                Value = update[key]['value']
                                Status = Command['Status']
                                if Qualifier:
                                    for Parameter in Command['Parameters']:
                                        try:
                                            Status = Status[Qualifier[Parameter]]
                                        except KeyError:
                                            if Parameter in Qualifier:
                                                Status[Qualifier[Parameter]] = {}
                                                Status = Status[Qualifier[Parameter]]
                                            else:
                                                return
                                update_is_online = False
                                if update[key]['command'] in ['ConnectionStatus','OnlineStatus']:
                                    update_is_online = True
                                try:
                                    if Status['Live'] != str(Value):
                                        Status['Live'] = str(Value)
                                        self.vars.ui_view1.UpdateDeviceInfo(key,update_is_online)
                                except:
                                    Status['Live'] = str(Value)
                                    self.vars.ui_view1.UpdateDeviceInfo(key,update_is_online)
                if 'Option' in match_type:
                    json_data = match[1]

                    update = None
                    try:
                        update = json.loads(json_data)
                    except Exception as e:
                        print('error decoding update devices json from system, error:' + str(e))
                        continue
                    if update:
                        for key in update.keys():
                            if key in self.vars.ui_view1.device_info:
                                for option in update[key].keys():
                                    if option in self.vars.ui_view1.device_info[key]['options']:
                                        val = update[key][option]
                                        self.vars.ui_view1.UpdateDeviceOption(key,option,val)


    def __HandleConnected(self,client,state:'str'):
        self.__system_is_connected = True
        self.vars.ui_view1.system_connected_status = state
        self.vars.ui_view1.ResetDeviceInfoAndLogs()
        self.vars.ui_view1.SetConnectStatus(state)
        self.SendToSystem('p9oai23jr09p8fmvw98foweivmawthapw4t-{}'.format(VERSION))
        self.vars.ui_view1.devices_client.StartKeepAlive(5,'ping(){}'.format(self.__delim))
    def __HandleDisconnected(self,client,state:'str'):
        self.__system_is_connected = False
        self.vars.ui_view1.system_connected_status = state
        self.vars.ui_view1.SetConnectStatus(state)

    def EndConnections(self):
        self.system_connection_stop()

    def SetClient(self):
        self.vars.ui_view1.devices_client.Connected = self.__HandleConnected
        self.vars.ui_view1.devices_client.Disconnected = self.__HandleDisconnected
        self.vars.ui_view1.devices_client.ReceiveData = self.__HandleRecieveFromClient

    def SendToSystem(self,cmd:'str'):
        if self.vars.ui_view1.devices_client:
            if len(cmd):
                self.vars.ui_view1.devices_client.Send('{}{}'.format(cmd,self.__delim))