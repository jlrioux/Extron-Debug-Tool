import paramiko
import datetime
import os,time
from threading import Thread

import tkinter as tk
import tkcalendar
from tktimepicker import SpinTimePickerOld,constants
from tkinter import filedialog
from ttkwidgets import CheckboxTreeview as CbTree

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from variables import variablesclass



class DateTimePickerWindowClass():
    def __init__(self,vars:'variablesclass',dttype:str):
        self.type = dttype
        self.vars = vars
        self.__dttypes = {'start':'Start Date and Time Selection','end':'End Date and Time Selection'}
        self.dt_window = tk.Tk()


        self.dt_window.title(self.__dttypes[self.type])
        self.dt_window.geometry('450x300')

        self.frame = tk.Frame(self.dt_window,pady=0,padx=0)
        self.frame.grid(column=0,row=0,sticky='nsew')

        self.calendar_frame = tk.Frame(self.frame)
        self.calendar_frame.grid(column=0,row=0,pady=5,padx=0,sticky='nsew')
        self.day_picker = tkcalendar.Calendar(self.calendar_frame,selectmode='day')
        self.day_picker.pack(pady=10,padx=10)


        self.time_picker = SpinTimePickerOld(self.frame)
        self.time_picker.addAll(constants.HOURS12)
        self.time_picker.grid(column=0,row=1,pady=10,padx=10,sticky='nsew')

        self.btn_submit = tk.Button(self.frame,text='Submit',command=self.btn_submit_pressed())
        self.btn_submit.grid(column=0,row=2,pady=10,padx=10,sticky='nsew')


    def btn_submit_pressed(self):
        def f():
            self.vars.ui_view2.update_date(self.type,self.day_picker.get_date())
            self.vars.ui_view2.update_time(self.type,self.time_picker.time())
            print('type:{} time:{}'.format(self.type,self.time_picker.time()))
            self.dt_window.destroy()
        return f


def process_entries(self,entry_list:list[str]):
    index = 0
    for data in entry_list:
        data = data.replace('\\\\r','\\r')
        data = data.replace('\\\\n','\\n')
        data = data.replace('\\\\x','\\x')
        data = data.replace('Timestamp,Device Name,MessageType,Data','')
        ddata = {}
        if '\n' in data:
            data = data.replace('\n','')
        ddata['value'] = data
        parts = data.split(',')
        if parts[0] == 'Timestamp':
            continue
        ddata['time'] = parts[0]
        ddata['name'] = parts[1]
        ddata['v1'] = parts[2]
        ddata['v2'] = parts[3]
        ddata['v3'] = ','.join(parts[4:])
        entry_list[index] = ddata
        self.update_log(ddata)
        index += 1
    self.notify_batch_complete()
class DebugLogDataManager():
    def __init__(self):
        self.__folder_path = None
        self.__ip_address = None
        self.__start_date = None
        self.__end_date = None
        self.__all_data = []
        self.__device_data = {}
        self.client_connected = False
        self.client_status = 'Disconnected'
        self.__status_callback = None
        self.status_callback = None
        self.__log_callback = None
        self.__threads = [] #type:list[Thread]

        self.__num_batches = 1000
        self.__current_batch = 0


    def __update_status(self,text):
        self.client_status = text
        if self.__status_callback:
            self.__status_callback(self.client_status)
    def __update_log(self,data):
        if self.__log_callback:
            self.__log_callback(data)
    def update_log(self,data):
        self.__update_log(data)
    def __clear_all_data(self):
        self.__all_data = []
    def set_update_status_callback(self,func):
        self.__status_callback = func
        self.status_callback = func
    def set_update_log_callback(self,func):
        self.__log_callback = func
    def pull_data_from_ip(self,ip,password='extron',start_date=None,end_date=None):
        self.__ip_address = ip
        if not start_date:
            self.__start_date = datetime.datetime.strptime('1/1/00 12:00 AM','%m/%d/%y %I:%M %p')
        else:
            self.__start_date = datetime.datetime.strptime(start_date,'%m/%d/%y %I:%M %p')
        if not end_date:
            self.__end_date = datetime.datetime.now()
        else:
            self.__end_date = datetime.datetime.strptime(end_date,'%m/%d/%y %I:%M %p')

        self.__clear_all_data()
        port = 22022
        username = "admin"
        try:
            transport = paramiko.Transport((self.__ip_address,port))
            transport.connect(None,username,password)
        except Exception as e:
            self.__update_status('Err: Connection to host {}: {}'.format(self.__ip_address,e))
            return
        self.client_connected = True
        sftp_client = paramiko.SFTPClient.from_transport(transport)

        self.__update_status('Pulling DebugLog file list')
        try:
            files = sftp_client.listdir('/DebugLogs/')
        except Exception as e:
            self.__update_status('Unable to pull DebugLog file list:{}'.format(e))
            sftp_client.close()
            transport.close()
            return
        files.sort()
        files_to_fetch = []
        for file in files:
            filepath = '/DebugLogs/{}'.format(file)
            #check datetime of file is within start and end datetimes
            filedatetime = datetime.datetime.strptime(file,'DebugLog-%Y-%m-%d-%H.csv')
            if filedatetime >= self.__start_date and filedatetime <= self.__end_date:
                files_to_fetch.append(filepath)
        file_count = 1
        for file in files_to_fetch:
            self.__update_status('Reading DebugLog file {} of {}: {}'.format(file_count,len(files_to_fetch),file))
            remote_file =  sftp_client.open(file)
            self.__all_data += remote_file.readlines()[1:]
            file_count += 1

        sftp_client.close()
        transport.close()
        self.client_connected = False
        self.__update_status('Pull Complete')
        self.__update_status('Processing...')
        index = 0
        for data in self.__all_data:
            data = data.replace('\\\\r','\\r')
            data = data.replace('\\\\n','\\n')
            data = data.replace('\\\\x','\\x')
            data = data.replace('Timestamp,Device Name,MessageType,Data','')
            ddata = {}
            if '\n' in data:
                data = data.replace('\n','')
            ddata['value'] = data
            parts = data.split(',')
            if parts[0] == 'Timestamp':
                continue
            ddata['time'] = parts[0]
            ddata['name'] = parts[1]
            ddata['v1'] = parts[2]
            ddata['v2'] = parts[3]
            ddata['v3'] = ','.join(parts[4:])
            self.__all_data[index] = ddata
            self.__update_log(ddata)
            index += 1


        self.__update_status('Idle')


    def notify_batch_complete(self):
        self.__current_batch += 1
        self.__update_status('Processing... {} % complete'.format(int(self.__current_batch/self.__num_batches*100)))
    def pull_data_from_folder(self,start_date=None,end_date=None):
        self.__folder_path = filedialog.askdirectory(initialdir=self.__folder_path,title='Select Folder')
        if not start_date:
            self.__start_date = datetime.datetime.strptime('1/1/00 12:00 AM','%m/%d/%y %I:%M %p')
        else:
            self.__start_date = datetime.datetime.strptime(start_date,'%m/%d/%y %I:%M %p')
        if not end_date:
            self.__end_date = datetime.datetime.now()
        else:
            self.__end_date = datetime.datetime.strptime(end_date,'%m/%d/%y %I:%M %p')

        self.__clear_all_data()

        self.__update_status('Pulling DebugLog file list')
        files = []
        try:
            files = os.listdir(self.__folder_path)
        except Exception as e:
            self.__update_status('Unable to pull DebugLog file list:{}'.format(e))
            return

        files.sort()
        files_to_fetch = []
        for file in files:
            filepath = '{}/{}'.format(self.__folder_path,file)
            #check datetime of file is within start and end datetimes
            try:
                filedatetime = datetime.datetime.strptime(file,'DebugLog-%Y-%m-%d-%H.csv')
            except Exception as e:
                print(e)
                continue
            if filedatetime >= self.__start_date and filedatetime <= self.__end_date:
                files_to_fetch.append(filepath)
        file_count = 1
        for file in files_to_fetch:
            self.__update_status('Reading DebugLog file {} of {}: {}'.format(file_count,len(files_to_fetch),file))
            remote_file =  open(file,mode='r')
            self.__all_data += remote_file.readlines()[1:]
            file_count += 1

        self.client_connected = False
        self.__update_status('Pull Complete')
        self.__update_status('Processing...')
        cur_start = 0
        cur_end = 10000
        self.__current_batch = 0
        self.__num_batches = int(len(self.__all_data)/10000)+1
        self.__update_status('Processing... {} batches of 10000 logs with up to 10 worker threads'.format(self.__num_batches))
        time.sleep(2)
        self.__update_status('Processing... 0 % complete')
        if cur_end > len(self.__all_data):
            cur_end = len(self.__all_data)
        while cur_end < len(self.__all_data):
            if len(self.__threads) < 11:
                self.__threads.append(Thread(target=process_entries,args=[self,self.__all_data[cur_start:cur_end]]))
                self.__threads[-1].start()
                cur_start = cur_end
                cur_end = cur_start + 10000
            else:
                for thread in self.__threads:
                    thread.join()
                self.__threads = []
        for thread in self.__threads:
            thread.join()
        self.__threads = []
        time.sleep(1)
        #for thread in self.__threads:
        #    thread.join()

        self.__update_status('Idle')

