import copy
import tkinter as tk
from tkinter import filedialog
from ttkwidgets import CheckboxTreeview as CbTree
from Wait import Wait
import re
from ProgramLoggerLib import DateTimePickerWindowClass,DebugLogDataManager
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from variables import variablesclass



class ProgramLoggerClass():
    def __init__(self,frame:'tk.Frame',vars:'variablesclass'):
        #class variables
        self.vars = vars
        self.log_data = DebugLogDataManager()
        self.log_data.set_update_status_callback(self.__create_pull_status_update_callback())
        self.log_data.set_update_log_callback(self.UpdateDeviceLog())
        self.pull_log_data_mode = 'IP'
        self.pull_log_folder_path = ''

        self.__frame = frame

        self.__timestamp_newest_first = True
        self.__device_logs = {} #type:dict[list[str]]
        self.__display_names = []
        self.__current_log_list = []
        self.__device_log_busy = False
        self.__tb_pause_flag = False
        self.__tb_hex_flag = False
        self.__tb_search_flag = False
        self.__tb_search_text = ''
        self.__device_list = []
        self.device_info = {}

        self.start_date = ''
        self.start_time = ''
        self.start_datetime = ''
        self.end_date = ''
        self.end_time = ''
        self.end_datetime = ''

        self.ip_address = ''
        self.ip_password = ''

        self.__btn_colors = None

        def focus_next_widget(event):
            event.widget.tk_focusNext().focus()
            return("break")
        def focus_target_widget(target):
            def e(event):
                target.focus()
                return("break")
            return e
        def enter_on_button(func):
            def e(event):
                func()
                return("break")
            return e

        #set up the UI
        self.__frame_header = tk.Frame(self.__frame)
        self.__frame_header.grid(column=0,row=0,sticky='news')

        self.__frame_header_body_nav = tk.Frame(self.__frame_header)
        self.__frame_header_body_nav.grid(column=0,row=0,sticky='news')
        self.__btn_body_view_log_start_label = tk.Label(self.__frame_header_body_nav,text = 'Start Date & Time')
        self.__btn_body_view_log_start_label.grid(column=0,row=0,sticky='nw')
        self.__btn_body_view_log_end_label = tk.Label(self.__frame_header_body_nav,text = 'End Date & Time')
        self.__btn_body_view_log_end_label.grid(column=1,row=0,padx=2,sticky='nw')
        self.__btn_body_view_log_start_date = tk.Button(self.__frame_header_body_nav,text="~Dawn of Time~",command=self.__get_start_datetime)
        self.__btn_body_view_log_start_date.grid(column=0,row=1,padx=2,sticky='nw')
        self.__btn_body_view_log_end_date = tk.Button(self.__frame_header_body_nav,text="~End of Time~",command=self.__get_end_datetime)
        self.__btn_body_view_log_end_date.grid(column=1,row=1,padx=2,sticky='nw')
        self.__btn_pull_logs = tk.Button(self.__frame_header_body_nav,text="Pull Logs IP",command=self.__open_connect_ip_window)
        self.__btn_pull_logs.grid(column=2,row=1,padx=2,sticky='nw')
        self.__btn_pull_logs = tk.Button(self.__frame_header_body_nav,text="Pull Logs Local",command=self.__pull_processor_logs_local)
        self.__btn_pull_logs.grid(column=3,row=1,padx=2,sticky='nw')

        self.__frame_controller_status = tk.Frame(self.__frame_header)
        self.__frame_controller_status.grid(column=0,row=2,sticky='news')
        self.__lbl_controller_status = tk.Label(self.__frame_controller_status,text = '   STATUS : Idle')
        self.__lbl_controller_status.grid(column=0,row=0,sticky='news')

        self.__frame_body_log = tk.PanedWindow(self.__frame,opaqueresize=True)
        self.__frame_body_log.grid(column=0,row=1,sticky='news')
        self.__frame_body_log_left = tk.PanedWindow(self.__frame_body_log)
        self.__frame_body_log_left.grid(column=0,row=0,sticky='news')

        self.__device_tree = CbTree(self.__frame_body_log_left)
        self.__device_tree.grid(column=0,row=0,sticky='news',pady=2)
        self.__device_tree.insert('', 'end', 'System', text='System')
        self.__device_tree.bind('<ButtonRelease>',self.__event_device_tree_release())
        self.__scrollb_device_treey = tk.Scrollbar(self.__frame_body_log_left,command=self.__device_tree.yview)
        self.__scrollb_device_treey.grid(column=1,row=0,sticky='news')
        self.__device_tree.configure(yscrollcommand=self.__scrollb_device_treey.set)

        self.__frame_body_log_right = tk.PanedWindow(self.__frame_body_log)
        self.__frame_body_log_right.grid(column=1,row=0,sticky='news')

        self.__frame_log_top = tk.Frame(self.__frame_body_log_right)
        self.__frame_log_top.grid(column=0,row=0,sticky='nw')
        self.__btn_tb_sort_timestamp = tk.Button(self.__frame_log_top,text="Timestamp:Newest",command=self.__toggle_tb_timestamp)
        self.__btn_tb_sort_timestamp.grid(column=0,row=0,padx=2,sticky='nw')
        self.__btn_tb_hex_format = tk.Button(self.__frame_log_top,text="Display HEX",command=self.__format_device_log)
        self.__btn_tb_hex_format.grid(column=1,row=0,padx=2,sticky='nw')
        self.__search_text_var = tk.StringVar()
        self.__search_text_var.trace_add('write',self.__search_text_changed())
        self.__btn_tb_search_txt = tk.Entry(self.__frame_log_top,text="",textvariable=self.__search_text_var)
        self.__btn_tb_search_txt.grid(column=2,row=0,padx=2,sticky='nw')
        self.__btn_tb_search_toggle = tk.Button(self.__frame_log_top,text="RegEx Search",command=self.__toggle_search_text)
        self.__btn_tb_search_toggle.bind('<Tab>',focus_target_widget(self.__btn_tb_search_txt))
        self.__btn_tb_search_toggle.bind('<Return>',enter_on_button(self.__toggle_search_text))
        self.__btn_tb_search_toggle.grid(column=3,row=0,padx=2,sticky='nw')

        self.__tb_log = tk.Text(self.__frame_body_log_right,wrap='none')
        self.__tb_log.grid(column=0,row=1,sticky='news')
        self.__scrollb_logy = tk.Scrollbar(self.__frame_body_log_right,command=self.__tb_log.yview)
        self.__scrollb_logy.grid(column=1,row=1,sticky='nws')
        self.__tb_log['yscrollcommand'] = self.__scrollb_logy.set
        self.__scrollb_logx = tk.Scrollbar(self.__frame_body_log_right,orient='horizontal',command=self.__tb_log.xview)
        self.__scrollb_logx.grid(column=0,row=2,sticky='new')
        self.__tb_log['xscrollcommand'] = self.__scrollb_logx.set

        self.__frame_body_log.paneconfig(self.__frame_body_log_left,stretch='always')
        self.__frame_body_log.paneconfig(self.__frame_body_log_right,stretch='always')

        self.__initialize_hide()
        self.Hide()

    def __open_connect_ip_window(self):
        window2 = tk.Tk()
        window2.title(' Connect To System ')
        window2.geometry('250x125')


        def clear_tb_ip():
            self.ip_address = tb_ip.get(1.0,'end')
            self.ip_address = self.ip_address.strip()
            self.ip_password = tb_password.get()
            self.ip_password = self.ip_password.strip()
            window2.destroy()
            self.__pull_processor_logs_ip()
        def clear_tb_enter(event):
            clear_tb_ip()

        def focus_next_widget(event):
            event.widget.tk_focusNext().focus()
            return("break")


        lbl_instructions1 = tk.Label(window2,text = ' Enter the IP address of the Extron Controller:  ')
        lbl_instructions1.grid(column=0,row=0)
        tb_ip = tk.Text(window2,height=1,width=20)
        tb_ip.grid(column=0,row=1)
        tb_ip.bind('<Return>',clear_tb_enter)
        tb_ip.bind('<Tab>',focus_next_widget)
        tb_ip.insert(tk.END,self.ip_address)
        tb_ip.update()

        lbl_instructions2 = tk.Label(window2,text = ' Enter the password of the Extron Controller:  ')
        lbl_instructions2.grid(column=0,row=2)
        tb_password = tk.Entry(window2,show="*",width=20)
        tb_password.grid(column=0,row=3)
        tb_password.bind('<Return>',clear_tb_enter)
        tb_password.bind('<Tab>',focus_next_widget)
        tb_password.insert(tk.END,self.ip_password)
        tb_password.update()

        btn_submit = tk.Button(window2,text='Submit',width=10,height=1,command=clear_tb_ip)
        btn_submit.bind('<Return>',clear_tb_enter)
        btn_submit.grid(column=0,row=4)
        #apply focus
        window2.wm_deiconify()
        tb_ip.focus_set()

    #time and date methods
    def update_time(self,dttype,timestr):
        ampm = {'a.m':'AM','p.m':'PM'}
        if dttype == 'start':
            self.start_time = '{:02d}:{:02d} {}'.format(timestr[0],timestr[1],ampm[timestr[2]])
            self.start_datetime = '{} {}'.format(self.start_date,self.start_time)
            self.__btn_body_view_log_start_date['text'] = '{} {}'.format(self.start_date,self.start_time)
        if dttype == 'end':
            self.end_time = '{:02d}:{:02d} {}'.format(timestr[0],timestr[1],ampm[timestr[2]])
            self.end_datetime = '{} {}'.format(self.end_date,self.end_time)
            self.__btn_body_view_log_end_date['text'] = self.end_datetime
    def update_date(self,dttype,datestr):
        if dttype == 'start':
            self.start_date = datestr
            self.start_datetime = '{} {}'.format(self.start_date,self.start_time)
            self.__btn_body_view_log_start_date['text'] = '{} {}'.format(self.start_date,self.start_time)
        if dttype == 'end':
            self.end_date = datestr
            self.end_datetime = '{} {}'.format(self.end_date,self.end_time)
            self.__btn_body_view_log_end_date['text'] = self.end_datetime
    def __get_start_datetime(self):
        dt = DateTimePickerWindowClass(self.vars,'start')

    def __get_end_datetime(self):
        dt = DateTimePickerWindowClass(self.vars,'end')
    def __pull_processor_logs_ip(self):
        host = self.ip_address
        password = self.ip_password

        self.Hide(self.__frame_body_log)
        self.__lbl_controller_status['text'] = 'Fetching Data...'
        @Wait(1)
        def w():
            self.ResetDeviceInfoAndLogs()
            self.log_data.pull_data_from_ip(host,password,self.start_datetime,self.end_datetime)
    def __pull_processor_logs_local(self):
        self.Hide(self.__frame_body_log)
        self.__lbl_controller_status['text'] = 'Fetching Data...'
        @Wait(1)
        def w():
            self.ResetDeviceInfoAndLogs()
            self.log_data.pull_data_from_folder(self.start_datetime,self.end_datetime)
    def __create_pull_status_update_callback(self):
        def u(status):
            self.__lbl_controller_status['text'] = status
            if status == 'Idle':
                self.SetDeviceList()
                self.__body_log_view_enable()
        return u

    #menu methods
    def save_selected_logs(self):
        f = filedialog.asksaveasfile(mode='w', defaultextension="txt")
        if f is None: # asksaveasfile return `None` if dialog closed with "cancel".
            return
        text2save = self.vars.ui_view2.GetCurrentLog()
        f.write(text2save)
        f.close()

    def save_all_logs(self):
        f = filedialog.asksaveasfile(mode='w', defaultextension="txt")
        if f is None: # asksaveasfile return `None` if dialog closed with "cancel".
            return
        text2save = self.vars.ui_view2.GetAllLogs()
        f.write(text2save)
        f.close()
    def GetAllLogs(self):
        pass


    #class methods
    def __initialize_hide(self):
        self.Hide(self.__frame_body_log)
        self.Hide(self.__frame_header_body_nav)
        self.Show(self.__frame_header_body_nav)

    def Hide(self,frame=None):
        if frame:
            frame._grid_info = frame.grid_info()
            frame.grid_remove()
        else:
            self.__frame._grid_info = self.__frame.grid_info()
            self.__frame.grid_remove()
    def Show(self,frame=None):
        if frame:
            frame.grid(**frame._grid_info)
        else:
            self.__frame.grid(**self.__frame._grid_info)

    def __body_log_view_enable(self):

        #apply window scaling to frames
        self.__frame.rowconfigure(1, weight=1)
        self.__frame.columnconfigure(0, weight=1)
        self.__frame_body_log.rowconfigure(0, weight=1)
        self.__frame_body_log.columnconfigure(1, weight=1)
        self.__frame_body_log_left.rowconfigure(0, weight=1)
        self.__frame_body_log_left.columnconfigure(0, weight=1)
        self.__device_tree.rowconfigure(0, weight=1)
        self.__device_tree.columnconfigure(0, weight=1)
        self.__frame_body_log_right.rowconfigure(1, weight=1)
        self.__frame_body_log_right.columnconfigure(0, weight=1)
        self.__tb_log.rowconfigure(1, weight=1)
        self.__tb_log.columnconfigure(0, weight=1)

        self.__frame.rowconfigure(2, weight=0)

        self.Show(self.__frame_body_log)
        self.Show(self.__frame_header_body_nav)
    def __build_current_log_list(self):
        if not self.__device_log_busy:
            self.__device_log_busy = True
            log_list = []
            for id in self.__device_tree.get_checked():
                i = id.split('_')[0]
                log_list.extend(self.__device_logs[i][id])
            log_list2 = []
            for log in log_list:
                if self.__tb_search_flag:
                    matches = re.findall(self.__tb_search_text,log)
                    if matches:
                        log_list2.append(self.__set_device_log_hex_format(log))
                else:
                    log_list2.append(self.__set_device_log_hex_format(log))
            log_list2.sort()
            if self.__timestamp_newest_first:
                log_list2.reverse()
            self.__current_log_list = log_list2
            self.__show_device_log()
            self.__device_log_busy = False
    def __add_to_current_log_list(self,log):
        log = self.__set_device_log_hex_format(log)
        if self.__timestamp_newest_first:
            self.__current_log_list.insert(0,log)
        else:
            self.__current_log_list.append(log)
    def __show_device_log(self):
        if self.__tb_pause_flag:
            return
        current_tb_log = '\n'.join(self.__current_log_list)
        self.__tb_log.delete('1.0','end')
        self.__tb_log.insert(tk.END,current_tb_log)
        self.__tb_log.update()
    def __toggle_tb_timestamp(self):
        self.__timestamp_newest_first = not self.__timestamp_newest_first

        vals = {True:'Newest',False:'Oldest'}
        self.__btn_tb_sort_timestamp['text'] = 'Timestamp:{}'.format(vals[self.__timestamp_newest_first])
        self.__build_current_log_list()
    def __get_device_log_key(self,device_id,log):
        i = ''
        if ',Command,' in log:
            i = '{}_Commands'.format(device_id)
        if ',Event,' in log:
            i = '{}_Events'.format(device_id)
        if ',From Device,' in log:
            i = '{}_Strings From Device'.format(device_id)
        if ',To Device,' in log:
            i = '{}_Strings To Device'.format(device_id)
        if ',Print,' in log:
            i = '{}_Print'.format(device_id)
        return i
    def __insert_log(self,data:'dict'):
        device_id = data['name']
        log = data['value']
        i = self.__get_device_log_key(device_id,data['value'])
        if device_id not in self.device_info:
            self.device_info[device_id] = {}
            self.device_info[device_id]['name'] = data['name']
        if 'value types' not in self.device_info[device_id]:
            self.device_info[device_id]['value types'] = []
        if data['v1'] not in self.device_info[device_id]['value types'] and data['v1'] != 'API':
            self.device_info[device_id]['value types'].append(data['v1'])
        elif  data['v2'] in ['From Device','To Device'] and data['v2'] not in self.device_info[device_id]['value types']:
            self.device_info[device_id]['value types'].append(data['v2'])
        if device_id not in self.__device_logs:self.__device_logs[device_id] = {}
        if i not in self.__device_logs[device_id]:self.__device_logs[device_id][i] = []
        if i and i in self.__device_logs[device_id]:
            if device_id in self.device_info:
                if self.__timestamp_newest_first:
                    self.__device_logs[device_id][i].insert(0,log)
                else:
                    self.__device_logs[device_id][i].append(log)
                if i in self.__device_tree.get_checked():
                    self.__add_to_current_log_list(log)
                    self.__show_device_log()
    def __format_device_log(self):
        self.__tb_hex_flag = not self.__tb_hex_flag
        if self.__tb_hex_flag:
            #self.__btn_tb_hex_format['bg'] = 'sky blue'
            self.__toggle_button(self.__btn_tb_hex_format,1)
            self.__btn_tb_hex_format['text'] = 'Displaying HEX'
        else:
            #self.__btn_tb_hex_format['bg'] = '#f0f0f0'
            self.__toggle_button(self.__btn_tb_hex_format,0)
            self.__btn_tb_hex_format['text'] = 'Display HEX'
        self.__build_current_log_list()
    def __toggle_search_text(self):
        self.__tb_search_flag = not self.__tb_search_flag
        if self.__tb_search_flag:
            #self.__btn_tb_search_toggle['bg'] = 'sky blue'
            self.__toggle_button(self.__btn_tb_search_toggle,1)
            self.__tb_search_text = self.__btn_tb_search_txt.get()
        else:
            #self.__btn_tb_search_toggle['bg'] = '#f0f0f0'
            self.__toggle_button(self.__btn_tb_search_toggle,0)
        self.__build_current_log_list()
    def __search_text_changed(self):
        def e(var,index,mode):
            if self.__tb_search_flag:
                self.__tb_search_flag = not self.__tb_search_flag
                #self.__btn_tb_search_toggle['bg'] = '#f0f0f0'
                self.__toggle_button(self.__btn_tb_search_toggle,0)
                self.__build_current_log_list()
        return e
    def __set_device_log_hex_format(self,log:'str'):
        if self.__tb_hex_flag:
            log = log.replace('\\\\r','\\r')
            log = log.replace('\\\\n','\\n')
            log = log.replace('\\r','\\x0d')
            log = log.replace('\\n','\\x0a')
            matches = re.findall('\\\\x(..)',log)
            for match in matches:
                match_str = '0x{}'.format(match.upper())
                an_integer = int(match_str,16)
                log = log.replace('\\x{}'.format(match),chr(an_integer))
            temp = '\\x'
            if ',To Device,' in log:
                parts = log.split(",To Device,")
                temp += "\x5Cx".join("{:02x}".format(ord(c)) for c in parts[1])
                return('{},To Device,{}'.format(parts[0],temp))
            elif ',From Device,' in log:
                parts = log.split(",From Device,")
                temp += "\x5Cx".join("{:02x}".format(ord(c)) for c in parts[1])
                return('{},From Device,{}'.format(parts[0],temp))
            else:
                return(log)
        return(log)
    def __event_device_tree_release(self):
        def e(*args):
            self.__tb_search_flag = False
            if self.__tb_search_flag:
                #self.__btn_tb_search_toggle['bg'] = 'sky blue'
                self.__toggle_button(self.__btn_tb_search_toggle,1)
                self.__tb_search_text = self.__btn_tb_search_txt.get()
            else:
                #self.__btn_tb_search_toggle['bg'] = '#f0f0f0'
                self.__toggle_button(self.__btn_tb_search_toggle,0)
            self.__build_current_log_list()
        return e

    def SetThemeColors(self,theme):
        btn = self.__btn_tb_sort_timestamp
        if theme == 'dark':# dark
            self.__btn_colors = {'inactive': '#1c1c1c', 'active': '#2f60d8', 'inactive text': '#fafafa', 'active text': '#ffffff'}
        else:
            self.__btn_colors = {'inactive': '#fafafa', 'active': '#2f60d8', 'inactive text': '#1c1c1c', 'active text': '#ffffff'}

    def __toggle_button(self,btn,state):
        if 'System' in btn.cget('background'):return
        if self.__btn_colors == None:
            self.__btn_colors = {'inactive':btn.cget('background'),'active':btn.cget('activebackground'),'inactive text':btn.cget('foreground'),'active text':btn.cget('activeforeground')}
            #self.__btn_colors = {'inactive':'#1c1c1c','active':'#2f60d8'}
        if state == 1:
            btn['relief'] = 'sunken'
            btn['background'] = self.__btn_colors['active']
            btn['foreground'] = self.__btn_colors['active text']
        else:
            btn['relief'] = 'raised'
            btn['background'] = self.__btn_colors['inactive']
            btn['foreground'] = self.__btn_colors['inactive text']

        #public functions
    def SetDeviceList(self):
        self.__initialize_hide()
        self.__tb_log.delete('1.0','end')
        key_list = list(self.device_info.keys()) #type:list
        key_list.sort()
        self.__device_list = []
        i = 0
        for name in key_list:
            value = self.device_info[name]['name']
            self.__device_list.append(value)
            if name not in self.__device_tree.get_children('System'):
                self.__device_tree.insert('System','end',name,text=name)
                vtypes = {'Command':'Commands','Event':'Events','To Device':'Strings To Device','From Device':'Strings From Device','Print':'Print'}
                for vtype in self.device_info[name]['value types']:
                    if vtype in vtypes:
                        self.__device_tree.insert(name,'end','{}_{}'.format(name,vtypes[vtype]),text=vtypes[vtype])
                i += 1

    def ResetDeviceInfoAndLogs(self):
        self.device_info = {}
        self.__device_logs = {}
        #run items in self.SetDeviceList()
        self.__tb_log.delete('1.0','end')
        self.__selected_module = None
        self.__device_list = []
        self.__device_tree.delete(*self.__device_tree.get_children())
        self.__device_tree.insert('', 'end', 'System', text='System')
    def UpdateDeviceLog(self):
        def e(data:'dict'):
            self.__insert_log(data)
        return e
    def GetAllLogs(self):
        all_logs = []
        for device_id in self.__device_logs:
            device_name = self.device_info[device_id]['name']
            for device_key in self.__device_logs[device_id]:
                cur_logs = copy.copy(self.__device_logs[device_id][device_key]) #type:list[str]
                for cur_log in cur_logs:
                    index = cur_logs.index(cur_log)
                all_logs.extend(cur_logs)
        all_logs.sort()
        all_logs_txt = '\r\n'.join(all_logs)
        return all_logs_txt
    def GetCurrentLog(self):
        all_logs = copy.copy(self.__current_log_list)
        all_logs.sort()
        all_logs_txt = '\r\n'.join(all_logs)
        return all_logs_txt
    def HideUIView(self):
        self.Hide()
    def ShowUIView(self):
        self.Show()
        self.Show(self.__frame_header_body_nav)