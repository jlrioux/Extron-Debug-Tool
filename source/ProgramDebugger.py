import copy
import pprint
from time import sleep
import tkinter as tk
from tkinter import filedialog
from ttkwidgets import CheckboxTreeview as CbTree
from Wait import Wait
import json
import re
from ProgramDebuggerLib import ProcessorCommunicationClass
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from variables import variablesclass
    from EthernetClientInterface import EthernetClientInterface



class ProgramDebuggerClass():
    def __init__(self,frame:'tk.Frame',vars:'variablesclass'):
        #class variables
        self.vars = vars
        self.__frame = frame
        self.__selected_module = None
        self.__selected_virtualui_mode = None
        self.__timestamp_newest_first = True
        self.__device_color_wait = None
        self.__device_color_wait_busy = False
        self.__setDeviceListWait = None
        self.__debug_view_mode = ''
        self.__module_view_mode = 'command'
        self.processor_communication = ProcessorCommunicationClass(self.vars)

        self.ip_address = ''
        self.system_connected_status = ''
        self.devices_client = None #type:EthernetClientInterface
        self.device_info = {}

        self.__device_logs = {} #type:dict[list[str]]
        self.__current_log_list = []
        self.__device_log_busy = False
        self.__tb_hex_flag = False
        self.__tb_pause_flag = False
        self.__device_list = []
        self.__reading_devices_busy = False

        self.__selected_device = tk.StringVar()
        self.__selected_device.trace_add('write',self.__selected_device_changed())

        self.__var_device_print_to_trace = tk.IntVar()
        #set up the UI

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

        self.__frame_header = tk.Frame(self.__frame)
        self.__frame_header.grid(column=0,row=0,sticky='nw')
        self.__frame_controller_status = tk.Frame(self.__frame_header)
        self.__frame_controller_status.grid(column=0,row=0,sticky='nw')
        self.__lbl_controller_status = tk.Label(self.__frame_controller_status,text = ' STATUS : Controller Disconnected')
        self.__lbl_controller_status.grid(column=0,row=0,sticky='nw')

        self.__frame_header_body_nav = tk.Frame(self.__frame_header)
        self.__frame_header_body_nav.grid(column=1,row=0,sticky='nw')
        self.__btn_body_view_log = tk.Button(self.__frame_header_body_nav,text="Log View",command=self.__body_log_view_enable)
        self.__btn_body_view_log.grid(column=0,row=0,sticky='nw')
        self.__btn_body_view_module = tk.Button(self.__frame_header_body_nav,text="Module View",command=self.__body_module_view_enable)
        self.__btn_body_view_module.grid(column=1,row=0,sticky='nw')

        self.__frame_devices_found = tk.Frame(self.__frame_header)
        self.__frame_devices_found.grid(column=0,row=1,sticky='nw')
        self.__lbl_devices_found = tk.Label(self.__frame_devices_found,text = '  ')
        self.__lbl_devices_found.grid(column=0,row=0)



        self.__frame_body_log = tk.PanedWindow(self.__frame,opaqueresize=True)
        self.__frame_body_log.grid(column=0,row=1,sticky='nsew')
        self.__frame_body_log_left = tk.Frame(self.__frame_body_log)
        self.__frame_body_log_left.grid(column=0,row=0,sticky='nsew')


        self.__device_tree = CbTree(self.__frame_body_log_left)
        self.__device_tree.grid(column=0,row=0,sticky='nsew',pady=2)
        self.__device_tree.insert('', 'end', 'System', text='System')
        self.__device_tree.bind('<ButtonRelease>',self.__event_device_tree_release())
        self.__scrollb_device_treey = tk.Scrollbar(self.__frame_body_log_left,command=self.__device_tree.yview)
        self.__scrollb_device_treey.grid(column=1,row=0,sticky='nsew')
        self.__device_tree.configure(yscrollcommand=self.__scrollb_device_treey.set)


        self.__frame_body_log_right = tk.Frame(self.__frame_body_log)
        self.__frame_body_log_right.grid(column=1,row=0,sticky='nsew')

        self.__frame_log_top = tk.Frame(self.__frame_body_log_right)
        self.__frame_log_top.grid(column=0,row=0,sticky='nw')
        self.__btn_tb_sort_timestamp = tk.Button(self.__frame_log_top,text="Timestamp:Newest",command=self.__toggle_tb_timestamp)
        self.__btn_tb_sort_timestamp.grid(column=0,row=0,sticky='nw')
        self.__btn_tb_pause_log = tk.Button(self.__frame_log_top,text="Pause Log",command=self.__pause_current_device_log)
        self.__btn_tb_pause_log.grid(column=1,row=0,sticky='nw')
        self.__btn_tb_hex_format = tk.Button(self.__frame_log_top,text="Display HEX",command=self.__format_device_log)
        self.__btn_tb_hex_format.grid(column=2,row=0,sticky='nw')
        self.__btn_tb_clear_all_logs = tk.Button(self.__frame_log_top,text="Clear Log",command=self.__clear_all_device_logs)
        self.__btn_tb_clear_all_logs.grid(column=3,row=0,sticky='nw')

        self.__tb_log = tk.Text(self.__frame_body_log_right,wrap='none')
        self.__tb_log.grid(column=0,row=1,sticky='nsew')
        #self.__tb_log.bind('<Tab>',focus_next_widget)
        self.__scrollb_logy = tk.Scrollbar(self.__frame_body_log_right,command=self.__tb_log.yview)
        self.__scrollb_logy.grid(column=1,row=1,sticky='nws')
        self.__tb_log['yscrollcommand'] = self.__scrollb_logy.set
        self.__scrollb_logx = tk.Scrollbar(self.__frame_body_log_right,orient='horizontal',command=self.__tb_log.xview)
        self.__scrollb_logx.grid(column=0,row=2,sticky='new')
        self.__tb_log['xscrollcommand'] = self.__scrollb_logx.set

        self.__frame_body_log.paneconfig(self.__frame_body_log_left,stretch='always')
        self.__frame_body_log.paneconfig(self.__frame_body_log_right,stretch='always')










        self.__frame_controller_module = tk.Frame(self.__frame)
        self.__frame_controller_module.grid(column=0,row=2,sticky='news')

        self.__frame_controller_module_left = tk.Frame(self.__frame_controller_module,bd=5)
        self.__frame_controller_module_left.grid(column=0,row=0,sticky='nws')

        # column 0 __frame_controller_module_left
        self.__frame_controller_selected_device = tk.Frame(self.__frame_controller_module_left)
        self.__frame_controller_selected_device.grid(column=0,row=0,sticky='nw')
        self.__lbl_selected_device_name = tk.Label(self.__frame_controller_selected_device,text = ' Selected: None')
        self.__lbl_selected_device_name.grid(column=0,row=0,sticky='nw')

        self.__om_devices = tk.OptionMenu(self.__frame_controller_module_left,self.__selected_device,self.__device_list)
        self.__om_devices.grid(column=0,row=1,sticky='nw')

        self.__frame_print_to_trace = tk.Frame(self.__frame_controller_module_left)
        self.__frame_print_to_trace.grid(column=0,row=2,sticky='nw')
        self.__chkbox_device_print_to_trace = tk.Checkbutton(self.__frame_print_to_trace,text='Print To Trace',variable=self.__var_device_print_to_trace,onvalue=1,offvalue=0,command=self.__cmd_device_print_to_trace())
        self.__chkbox_device_print_to_trace.grid(column=0,row=3,sticky='nw')

        self.__lbl_device_comm_detail1 = tk.Label(self.__frame_controller_module_left,text = ' ')
        self.__lbl_device_comm_detail1.grid(column=0,row=4,sticky='nw')
        self.__lbl_device_comm_detail2 = tk.Label(self.__frame_controller_module_left,text = ' ')
        self.__lbl_device_comm_detail2.grid(column=0,row=5,sticky='nw')
        self.__lbl_device_comm_detail3 = tk.Label(self.__frame_controller_module_left,text = ' ')
        self.__lbl_device_comm_detail3.grid(column=0,row=6,sticky='nw')
        self.__lbl_device_comm_detail4 = tk.Label(self.__frame_controller_module_left,text = ' ')
        self.__lbl_device_comm_detail4.grid(column=0,row=7,sticky='nw')
        self.__lbl_device_comm_detail5 = tk.Label(self.__frame_controller_module_left,text = ' ')
        self.__lbl_device_comm_detail5.grid(column=0,row=8,sticky='nw')
        self.__lbl_device_comm_detail6 = tk.Label(self.__frame_controller_module_left,text = ' ')
        self.__lbl_device_comm_detail6.grid(column=0,row=9,sticky='nw')
        self.__lbl_device_comm_detail7 = tk.Label(self.__frame_controller_module_left,text = ' ')
        self.__lbl_device_comm_detail7.grid(column=0,row=10,sticky='nw')

        self.__frame_device_reinit = tk.Frame(self.__frame_controller_module_left)
        self.__frame_device_reinit.grid(column=0,row=11,sticky='nw')
        self.__btn_device_reinit = tk.Button(self.__frame_device_reinit,text='Reinitialize Module',command=self.__cmd_reinitialize_selected_module)
        self.__btn_device_reinit.grid(column=0,row=0,sticky='nw')





        self.__frame_controller_module_right = tk.Frame(self.__frame_controller_module)
        self.__frame_controller_module_right.grid(column=1,row=0,sticky='news')
        # column 1
        self.__frame_controller_views = tk.Frame(self.__frame_controller_module_right)
        self.__frame_controller_views.grid(column=0,row=0,sticky='new')
        self.__btn_tb_view_command_view = tk.Button(self.__frame_controller_views,text="Command View",command=self.__controller_command_view_enable)
        self.__btn_tb_view_command_view.grid(column=0,row=0,sticky='nw')
        self.__btn_tb_view_status_view = tk.Button(self.__frame_controller_views,text="Status View",command=self.__controller_status_view_enable)
        self.__btn_tb_view_status_view.grid(column=1,row=0,sticky='nsew')


        self.__frame_controller_module_status_view = tk.Frame(self.__frame_controller_module_right)
        self.__frame_controller_module_status_view.grid(column=0,row=1,sticky='nsew')

        ''' device module status '''
        self.__frame_status = tk.Frame(self.__frame_controller_module_status_view,padx=10)
        self.__frame_status.grid(column=1,row=1,sticky='nsew')
        self.__tb_status = tk.Text(self.__frame_status,wrap='none')
        #self.__tb_status.bind('<Tab>',focus_next_widget)
        self.__tb_status.grid(column=0,row=0,sticky='nsew')
        self.__scrollb_statusy = tk.Scrollbar(self.__frame_status,command=self.__tb_status.yview)
        self.__scrollb_statusy.grid(column=1,row=0,sticky='nsw')
        self.__tb_status['yscrollcommand'] = self.__scrollb_statusy.set
        self.__scrollb_statusx = tk.Scrollbar(self.__frame_status,orient='horizontal',command=self.__tb_status.xview)
        self.__scrollb_statusx.grid(column=0,row=1,sticky='new')
        self.__tb_status['xscrollcommand'] = self.__scrollb_statusx.set


        self.__frame_controller_module_command_view = tk.Frame(self.__frame_controller_module_right)
        self.__frame_controller_module_command_view.grid(column=0,row=2,sticky='nsew')

        ''' device module commands '''
        self.__frame_device_commands = tk.Frame(self.__frame_controller_module_command_view,pady=10)
        self.__frame_device_commands.grid(column=0,row=1,sticky='nsew')

        self.__frame_device_commands_for_modules = tk.Frame(self.__frame_device_commands)
        self.__frame_device_commands_for_modules.grid(column=0,row=0,sticky='nw')
        self.__frame_device_commands_for_modules_top = tk.Frame(self.__frame_device_commands_for_modules)
        self.__frame_device_commands_for_modules_top.grid(column=0,row=0,sticky='nw')
        #Set(command,value,qualifier)
        self.__lbl_commands_module_set1 = tk.Label(self.__frame_device_commands_for_modules_top,text='Command')
        self.__lbl_commands_module_set1.grid(column=1,row=0,sticky='nw')
        self.__lbl_commands_module_set2 = tk.Label(self.__frame_device_commands_for_modules_top,text='Value')
        self.__lbl_commands_module_set2.grid(column=2,row=0,sticky='nw')
        self.__lbl_commands_module_set3 = tk.Label(self.__frame_device_commands_for_modules_top,text='Qualifier ( example: {"Output":"1"} )')
        self.__lbl_commands_module_set3.grid(column=3,row=0,sticky='nw')
        self.__btn_cmd_set = tk.Button(self.__frame_device_commands_for_modules_top,text="Set",width=15,command=self.__cmd_set_selected_module)
        self.__btn_cmd_set.bind('<Return>',enter_on_button(self.__cmd_set_selected_module))
        self.__btn_cmd_set.grid(column=0,row=1,sticky='nw')
        self.__tb_set_command1 = tk.Text(self.__frame_device_commands_for_modules_top,height=1,width=15,wrap='none')
        self.__tb_set_command1.bind('<Tab>',focus_next_widget)
        self.__tb_set_command1.grid(column=1,row=1,sticky='nw')
        self.__frame_commands_module_set_value = tk.Frame(self.__frame_device_commands_for_modules_top)
        self.__frame_commands_module_set_value.grid(column=2,row=1,sticky='nw')
        self.__sv_commands_module_set_value_type = tk.StringVar()
        self.__sv_commands_module_set_value_type.set('String')
        self.__list_commands_module_set_value_type_options = ['String','Float']
        self.__om_commands_module_set_value_type = tk.OptionMenu(self.__frame_commands_module_set_value,self.__sv_commands_module_set_value_type,*self.__list_commands_module_set_value_type_options)
        self.__om_commands_module_set_value_type.grid(column=0,row=0,sticky='nw')
        self.__tb_set_command2 = tk.Text(self.__frame_commands_module_set_value,height=1,width=20,wrap='none')
        self.__tb_set_command2.bind('<Tab>',focus_next_widget)
        self.__tb_set_command2.grid(column=1,row=0,sticky='nw')
        self.__tb_set_command3 = tk.Text(self.__frame_device_commands_for_modules_top,height=1,width=30,wrap='none')
        self.__tb_set_command3.bind('<Tab>',focus_target_widget(self.__btn_cmd_set))
        self.__tb_set_command3.grid(column=3,row=1,sticky='nw')
        #Update(command,qualifier)
        self.__lbl_commands_module_update1 = tk.Label(self.__frame_device_commands_for_modules_top,text='Command')
        self.__lbl_commands_module_update1.grid(column=1,row=2,sticky='nw')
        self.__lbl_commands_module_update2 = tk.Label(self.__frame_device_commands_for_modules_top,text='Qualifier ( example: {"Output":"1"} )')
        self.__lbl_commands_module_update2.grid(column=3,row=2,sticky='nw')
        self.__btn_cmd_update = tk.Button(self.__frame_device_commands_for_modules_top,text='Update',width=15,command=self.__cmd_update_selected_module)
        self.__btn_cmd_update.bind('<Return>',enter_on_button(self.__cmd_update_selected_module))
        self.__btn_cmd_update.grid(column=0,row=3,sticky='nw')
        self.__tb_update_command1 = tk.Text(self.__frame_device_commands_for_modules_top,height=1,width=15,wrap='none')
        self.__tb_update_command1.bind('<Tab>',focus_next_widget)
        self.__tb_update_command1.grid(column=1,row=3,sticky='nw')
        self.__tb_update_command2 = tk.Text(self.__frame_device_commands_for_modules_top,height=1,width=30,wrap='none')
        self.__tb_update_command2.bind('<Tab>',focus_target_widget(self.__btn_cmd_update))
        self.__tb_update_command2.grid(column=3,row=3,sticky='nw')
        #WriteStatus(command,value,qualifier)
        self.__lbl_commands_module_writestatus1 = tk.Label(self.__frame_device_commands_for_modules_top,text='Command')
        self.__lbl_commands_module_writestatus1.grid(column=1,row=4,sticky='nw')
        self.__lbl_commands_module_writestatus2 = tk.Label(self.__frame_device_commands_for_modules_top,text='Value')
        self.__lbl_commands_module_writestatus2.grid(column=2,row=4,sticky='nw')
        self.__lbl_commands_module_writestatus3 = tk.Label(self.__frame_device_commands_for_modules_top,text='Qualifier ( example: {"Output":"1"} )')
        self.__lbl_commands_module_writestatus3.grid(column=3,row=4,sticky='nw')
        self.__btn_cmd_writestatus = tk.Button(self.__frame_device_commands_for_modules_top,text='WriteStatus',width=15,command=self.__cmd_writestatus_selected_module)
        self.__btn_cmd_writestatus.bind('<Return>',enter_on_button(self.__cmd_writestatus_selected_module))
        self.__btn_cmd_writestatus.grid(column=0,row=5,sticky='nw')
        self.__tb_writestatus_command1 = tk.Text(self.__frame_device_commands_for_modules_top,height=1,width=15,wrap='none')
        self.__tb_writestatus_command1.bind('<Tab>',focus_next_widget)
        self.__tb_writestatus_command1.grid(column=1,row=5,sticky='nw')
        self.__frame_commands_module_writestatus_value = tk.Frame(self.__frame_device_commands_for_modules_top)
        self.__frame_commands_module_writestatus_value.grid(column=2,row=5,sticky='nw')
        self.__sv_commands_module_writestatus_value_type = tk.StringVar()
        self.__sv_commands_module_writestatus_value_type.set('String')
        self.__list_commands_module_writestatus_value_type_options = ['String','Float']
        self.__om_commands_module_writestatus_value_type = tk.OptionMenu(self.__frame_commands_module_writestatus_value,self.__sv_commands_module_writestatus_value_type,*self.__list_commands_module_writestatus_value_type_options)
        self.__om_commands_module_writestatus_value_type.grid(column=0,row=0,sticky='nw')
        self.__tb_writestatus_command2 = tk.Text(self.__frame_commands_module_writestatus_value,height=1,width=20,wrap='none')
        self.__tb_writestatus_command2.bind('<Tab>',focus_next_widget)
        self.__tb_writestatus_command2.grid(column=1,row=0,sticky='nw')
        self.__tb_writestatus_command3 = tk.Text(self.__frame_device_commands_for_modules_top,height=1,width=30,wrap='none')
        self.__tb_writestatus_command3.bind('<Tab>',focus_target_widget(self.__btn_cmd_writestatus))
        self.__tb_writestatus_command3.grid(column=3,row=5,sticky='nw')
        self.__frame_device_commands_for_modules_bottom = tk.Frame(self.__frame_device_commands_for_modules)
        self.__frame_device_commands_for_modules_bottom.grid(column=0,row=1,sticky='nw')
        #Passthrough
        self.__lbl_passthrough_commmand = tk.Label(self.__frame_device_commands_for_modules_bottom,text='Command ( example: power on\\x0d\\x0a )')
        self.__lbl_passthrough_commmand.grid(column=1,row=0,sticky='nw')
        self.__btn_cmd_passthrough = tk.Button(self.__frame_device_commands_for_modules_bottom,text='Passthrough',width=15,command=self.__cmd_passthrough_selected_module)
        self.__btn_cmd_passthrough.bind('<Return>',enter_on_button(self.__cmd_passthrough_selected_module))
        self.__btn_cmd_passthrough.grid(column=0,row=1,sticky='nw')
        self.__tb_passthrough_command = tk.Text(self.__frame_device_commands_for_modules_bottom,height=1,width=65,wrap='none')
        self.__tb_passthrough_command.bind('<Tab>',focus_target_widget(self.__btn_cmd_passthrough))
        self.__tb_passthrough_command.grid(column=1,row=1,sticky='nw')

        ''' circuit breaker '''
        self.__frame_device_commands_for_circuit_breaker = tk.Frame(self.__frame_device_commands)
        self.__frame_device_commands_for_circuit_breaker.grid(column=0,row=1,sticky='nw')
        #none

        ''' contact '''
        self.__frame_device_commands_for_contact = tk.Frame(self.__frame_device_commands)
        self.__frame_device_commands_for_contact.grid(column=0,row=2,sticky='nw')
        #none

        ''' digital input '''
        self.__frame_device_commands_for_digital_input = tk.Frame(self.__frame_device_commands)
        self.__frame_device_commands_for_digital_input.grid(column=0,row=3,sticky='nw')
        #Initialize (host,port,pullup)
        self.__lbl_device_commands_digital_input_initialize1 = tk.Label(self.__frame_device_commands_for_digital_input,text='Pullup')
        self.__lbl_device_commands_digital_input_initialize1.grid(column=1,row=0,sticky='nw')
        self.__btn_cmd_digital_input_initialize = tk.Button(self.__frame_device_commands_for_digital_input,text='Initialize',width=15,command=self.__cmd_initialize_selected_device)
        self.__btn_cmd_digital_input_initialize.bind('<Return>',enter_on_button(self.__cmd_initialize_selected_device))
        self.__btn_cmd_digital_input_initialize.grid(column=0,row=1,sticky='nw')
        self.__tb_cmd_digital_input_initialize1 = tk.Text(self.__frame_device_commands_for_digital_input,height=1,width=20,wrap='none')
        self.__tb_cmd_digital_input_initialize1.bind('<Tab>',focus_target_widget(self.__btn_cmd_digital_input_initialize))
        self.__tb_cmd_digital_input_initialize1.grid(column=1,row=1,sticky='nw')

        ''' digital io '''
        self.__frame_device_commands_for_digital_io = tk.Frame(self.__frame_device_commands)
        self.__frame_device_commands_for_digital_io.grid(column=0,row=4,sticky='nw')
        #Initialize (host,port,pullup)
        self.__lbl_device_commands_digital_io_initialize1 = tk.Label(self.__frame_device_commands_for_digital_io,text='Mode')
        self.__lbl_device_commands_digital_io_initialize1.grid(column=1,row=0,sticky='nw')
        self.__lbl_device_commands_digital_io_initialize2 = tk.Label(self.__frame_device_commands_for_digital_io,text='Pullup')
        self.__lbl_device_commands_digital_io_initialize2.grid(column=2,row=0,sticky='nw')
        self.__btn_cmd_digital_io_initialize = tk.Button(self.__frame_device_commands_for_digital_io,text='Initialize',width=15,command=self.__cmd_initialize_selected_device)
        self.__btn_cmd_digital_io_initialize.bind('<Return>',enter_on_button(self.__cmd_initialize_selected_device))
        self.__btn_cmd_digital_io_initialize.grid(column=0,row=1,sticky='nw')
        self.__tb_cmd_digital_io_initialize1 = tk.Text(self.__frame_device_commands_for_digital_io,height=1,width=20,wrap='none')
        self.__tb_cmd_digital_io_initialize1.bind('<Tab>',focus_next_widget)
        self.__tb_cmd_digital_io_initialize1.grid(column=1,row=1,sticky='nw')
        self.__tb_cmd_digital_io_initialize2 = tk.Text(self.__frame_device_commands_for_digital_io,height=1,width=20,wrap='none')
        self.__tb_cmd_digital_io_initialize2.bind('<Tab>',focus_target_widget(self.__btn_cmd_digital_io_initialize))
        self.__tb_cmd_digital_io_initialize2.grid(column=2,row=1,sticky='nw')
        #Pulse(duration)
        self.__lbl_device_commands_digital_io_pulse1 = tk.Label(self.__frame_device_commands_for_digital_io,text='Duration')
        self.__lbl_device_commands_digital_io_pulse1.grid(column=1,row=2,sticky='nw')
        self.__btn_cmd_digital_io_pulse = tk.Button(self.__frame_device_commands_for_digital_io,text='Pulse',width=15,command=self.__cmd_pulse_selected_device)
        self.__btn_cmd_digital_io_pulse.bind('<Return>',enter_on_button(self.__cmd_pulse_selected_device))
        self.__btn_cmd_digital_io_pulse.grid(column=0,row=3,sticky='nw')
        self.__tb_cmd_digital_io_pulse1 = tk.Text(self.__frame_device_commands_for_digital_io,height=1,width=20,wrap='none')
        self.__tb_cmd_digital_io_pulse1.bind('<Tab>',focus_target_widget(self.__btn_cmd_digital_io_pulse))
        self.__tb_cmd_digital_io_pulse1.grid(column=1,row=3,sticky='nw')
        #State('On' or 'Off')
        self.__lbl_device_commands_digital_io_state1 = tk.Label(self.__frame_device_commands_for_digital_io,text='On or Off')
        self.__lbl_device_commands_digital_io_state1.grid(column=1,row=4,sticky='nw')
        self.__btn_cmd_digital_io_state = tk.Button(self.__frame_device_commands_for_digital_io,text='State',width=15,command=self.__cmd_state_selected_device)
        self.__btn_cmd_digital_io_state.bind('<Return>',enter_on_button(self.__cmd_state_selected_device))
        self.__btn_cmd_digital_io_state.grid(column=0,row=5,sticky='nw')
        self.__tb_cmd_digital_io_state1 = tk.Text(self.__frame_device_commands_for_digital_io,height=1,width=20,wrap='none')
        self.__tb_cmd_digital_io_state1.bind('<Tab>',focus_target_widget(self.__btn_cmd_digital_io_state))
        self.__tb_cmd_digital_io_state1.grid(column=1,row=5,sticky='nw')
        #Toggle
        self.__btn_cmd_digital_io_toggle = tk.Button(self.__frame_device_commands_for_digital_io,text='Toggle',width=15,command=self.__cmd_state_selected_device)
        self.__btn_cmd_digital_io_toggle.grid(column=0,row=6,sticky='nw')

        ''' flex io '''
        self.__frame_device_commands_for_flex_io = tk.Frame(self.__frame_device_commands)
        self.__frame_device_commands_for_flex_io.grid(column=0,row=5,sticky='nw')
        #initialize (mode,pullup,upper,lower)
        self.__lbl_device_commands_flex_io_initialize1 = tk.Label(self.__frame_device_commands_for_flex_io,text='Mode')
        self.__lbl_device_commands_flex_io_initialize1.grid(column=1,row=0,sticky='nw')
        self.__lbl_device_commands_flex_io_initialize2 = tk.Label(self.__frame_device_commands_for_flex_io,text='Pullup')
        self.__lbl_device_commands_flex_io_initialize2.grid(column=2,row=0,sticky='nw')
        self.__lbl_device_commands_flex_io_initialize3 = tk.Label(self.__frame_device_commands_for_flex_io,text='Upper')
        self.__lbl_device_commands_flex_io_initialize3.grid(column=3,row=0,sticky='nw')
        self.__lbl_device_commands_flex_io_initialize4 = tk.Label(self.__frame_device_commands_for_flex_io,text='Lower')
        self.__lbl_device_commands_flex_io_initialize4.grid(column=4,row=0,sticky='nw')
        self.__btn_cmd_flex_io_initialize = tk.Button(self.__frame_device_commands_for_flex_io,text='Initialize',width=15,command=self.__cmd_initialize_selected_device)
        self.__btn_cmd_flex_io_initialize.bind('<Return>',enter_on_button(self.__cmd_initialize_selected_device))
        self.__btn_cmd_flex_io_initialize.grid(column=0,row=1,sticky='nw')
        self.__tb_cmd_flex_io_initialize1 = tk.Text(self.__frame_device_commands_for_flex_io,height=1,width=20,wrap='none')
        self.__tb_cmd_flex_io_initialize1.bind('<Tab>',focus_next_widget)
        self.__tb_cmd_flex_io_initialize1.grid(column=1,row=1,sticky='nw')
        self.__tb_cmd_flex_io_initialize2 = tk.Text(self.__frame_device_commands_for_flex_io,height=1,width=20,wrap='none')
        self.__tb_cmd_flex_io_initialize2.bind('<Tab>',focus_next_widget)
        self.__tb_cmd_flex_io_initialize2.grid(column=2,row=1,sticky='nw')
        self.__tb_cmd_flex_io_initialize3 = tk.Text(self.__frame_device_commands_for_flex_io,height=1,width=20,wrap='none')
        self.__tb_cmd_flex_io_initialize3.bind('<Tab>',focus_next_widget)
        self.__tb_cmd_flex_io_initialize3.grid(column=3,row=1,sticky='nw')
        self.__tb_cmd_flex_io_initialize4 = tk.Text(self.__frame_device_commands_for_flex_io,height=1,width=20,wrap='none')
        self.__tb_cmd_flex_io_initialize4.bind('<Tab>',focus_target_widget(self.__btn_cmd_flex_io_initialize))
        self.__tb_cmd_flex_io_initialize4.grid(column=4,row=1,sticky='nw')
        #Pulse(duration)
        self.__lbl_device_commands_flex_io_pulse1 = tk.Label(self.__frame_device_commands_for_flex_io,text='Duration')
        self.__lbl_device_commands_flex_io_pulse1.grid(column=1,row=2,sticky='nw')
        self.__btn_cmd_flex_io_pulse = tk.Button(self.__frame_device_commands_for_flex_io,text='Pulse',width=15,command=self.__cmd_pulse_selected_device)
        self.__btn_cmd_flex_io_pulse.bind('<Return>',enter_on_button(self.__cmd_pulse_selected_device))
        self.__btn_cmd_flex_io_pulse.grid(column=0,row=3,sticky='nw')
        self.__tb_cmd_flex_io_pulse1 = tk.Text(self.__frame_device_commands_for_flex_io,height=1,width=20,wrap='none')
        self.__tb_cmd_flex_io_pulse1.bind('<Tab>',focus_target_widget(self.__btn_cmd_flex_io_pulse))
        self.__tb_cmd_flex_io_pulse1.grid(column=1,row=3,sticky='nw')
        #State('On' or 'Off')
        self.__lbl_device_commands_flex_io_state1 = tk.Label(self.__frame_device_commands_for_flex_io,text='On or Off')
        self.__lbl_device_commands_flex_io_state1.grid(column=1,row=4,sticky='nw')
        self.__btn_cmd_flex_io_state = tk.Button(self.__frame_device_commands_for_flex_io,text='State',width=15,command=self.__cmd_state_selected_device)
        self.__btn_cmd_flex_io_state.bind('<Return>',enter_on_button(self.__cmd_state_selected_device))
        self.__btn_cmd_flex_io_state.grid(column=0,row=5,sticky='nw')
        self.__tb_cmd_flex_io_state1 = tk.Text(self.__frame_device_commands_for_flex_io,height=1,width=20,wrap='none')
        self.__tb_cmd_flex_io_state1.bind('<Tab>',focus_target_widget(self.__btn_cmd_flex_io_state))
        self.__tb_cmd_flex_io_state1.grid(column=1,row=5,sticky='nw')
        #Toggle
        self.__btn_cmd_flex_io_toggle = tk.Button(self.__frame_device_commands_for_flex_io,text='Toggle',width=15,command=self.__cmd_toggle_selected_device)
        self.__btn_cmd_flex_io_toggle.grid(column=0,row=6,sticky='nw')

        ''' ir '''
        self.__frame_device_commands_for_ir = tk.Frame(self.__frame_device_commands)
        self.__frame_device_commands_for_ir.grid(column=0,row=6,sticky='nw')
        #PlayContinuous(command)
        self.__lbl_device_commands_ir_playcontinuous1 = tk.Label(self.__frame_device_commands_for_ir,text='Command')
        self.__lbl_device_commands_ir_playcontinuous1.grid(column=1,row=0,sticky='nw')
        self.__btn_cmd_ir_playcontinuous = tk.Button(self.__frame_device_commands_for_ir,text='PlayContinuous',width=15,command=self.__cmd_playcontinuous_selected_device)
        self.__btn_cmd_ir_playcontinuous.bind('<Return>',enter_on_button(self.__cmd_playcontinuous_selected_device))
        self.__btn_cmd_ir_playcontinuous.grid(column=0,row=1,sticky='nw')
        self.__tb_cmd_ir_playcontinuous1 = tk.Text(self.__frame_device_commands_for_ir,height=1,width=20,wrap='none')
        self.__tb_cmd_ir_playcontinuous1.bind('<Tab>',focus_target_widget(self.__btn_cmd_ir_playcontinuous))
        self.__tb_cmd_ir_playcontinuous1.grid(column=1,row=1,sticky='nw')
        #PlayTime(command,duration)
        self.__lbl_device_commands_ir_playtime1 = tk.Label(self.__frame_device_commands_for_ir,text='Command')
        self.__lbl_device_commands_ir_playtime1.grid(column=1,row=2,sticky='nw')
        self.__lbl_device_commands_ir_playtime2 = tk.Label(self.__frame_device_commands_for_ir,text='Duration')
        self.__lbl_device_commands_ir_playtime2.grid(column=2,row=2,sticky='nw')
        self.__btn_cmd_ir_playtime = tk.Button(self.__frame_device_commands_for_ir,text='PlayTime',width=15,command=self.__cmd_playtime_selected_device)
        self.__btn_cmd_ir_playtime.bind('<Return>',enter_on_button(self.__cmd_playtime_selected_device))
        self.__btn_cmd_ir_playtime.grid(column=0,row=3,sticky='nw')
        self.__tb_cmd_ir_playtime1 = tk.Text(self.__frame_device_commands_for_ir,height=1,width=20,wrap='none')
        self.__tb_cmd_ir_playtime1.bind('<Tab>',focus_next_widget)
        self.__tb_cmd_ir_playtime1.grid(column=1,row=3,sticky='nw')
        self.__tb_cmd_ir_playtime2 = tk.Text(self.__frame_device_commands_for_ir,height=1,width=20,wrap='none')
        self.__tb_cmd_ir_playtime2.bind('<Tab>',focus_target_widget(self.__btn_cmd_ir_playtime))
        self.__tb_cmd_ir_playtime2.grid(column=2,row=3,sticky='nw')
        #PlayCount(comand,count)
        self.__lbl_device_commands_ir_playcount1 = tk.Label(self.__frame_device_commands_for_ir,text='Command')
        self.__lbl_device_commands_ir_playcount1.grid(column=1,row=4,sticky='nw')
        self.__lbl_device_commands_ir_playcount2 = tk.Label(self.__frame_device_commands_for_ir,text='Count')
        self.__lbl_device_commands_ir_playcount2.grid(column=2,row=4,sticky='nw')
        self.__btn_cmd_ir_playcount = tk.Button(self.__frame_device_commands_for_ir,text='PlayCount',width=15,command=self.__cmd_playcount_selected_device)
        self.__btn_cmd_ir_playcount.bind('<Return>',enter_on_button(self.__cmd_playcount_selected_device))
        self.__btn_cmd_ir_playcount.grid(column=0,row=5,sticky='nw')
        self.__tb_cmd_ir_playcount1 = tk.Text(self.__frame_device_commands_for_ir,height=1,width=20,wrap='none')
        self.__tb_cmd_ir_playcount1.bind('<Tab>',focus_next_widget)
        self.__tb_cmd_ir_playcount1.grid(column=1,row=5,sticky='nw')
        self.__tb_cmd_ir_playcount2 = tk.Text(self.__frame_device_commands_for_ir,height=1,width=20,wrap='none')
        self.__tb_cmd_ir_playcount2.bind('<Tab>',focus_target_widget(self.__btn_cmd_ir_playcount))
        self.__tb_cmd_ir_playcount2.grid(column=2,row=5,sticky='nw')
        #Stop
        self.__btn_cmd_ir_stop = tk.Button(self.__frame_device_commands_for_ir,text='Stop',width=15,command=self.__cmd_stop_selected_device)
        self.__btn_cmd_ir_stop.grid(column=0,row=6,sticky='nw')
        #Initialize(file)
        self.__lbl_device_commands_ir_initialize1 = tk.Label(self.__frame_device_commands_for_ir,text='File Name')
        self.__lbl_device_commands_ir_initialize1.grid(column=1,row=7,sticky='nw')
        self.__btn_cmd_ir_initialize = tk.Button(self.__frame_device_commands_for_ir,text='Initialize',width=15,command=self.__cmd_initialize_selected_device)
        self.__btn_cmd_ir_initialize.bind('<Return>',enter_on_button(self.__cmd_initialize_selected_device))
        self.__btn_cmd_ir_initialize.grid(column=0,row=8,sticky='nw')
        self.__tb_cmd_ir_initialize1 = tk.Text(self.__frame_device_commands_for_ir,height=1,width=20,wrap='none')
        self.__tb_cmd_ir_initialize1.bind('<Tab>',focus_target_widget(self.__btn_cmd_ir_initialize))
        self.__tb_cmd_ir_initialize1.grid(column=1,row=8,sticky='nw')

        ''' PoE '''
        self.__frame_device_commands_for_poe = tk.Frame(self.__frame_device_commands)
        self.__frame_device_commands_for_poe.grid(column=0,row=7,sticky='nw')
        #State('On' or 'Off')
        self.__lbl_device_commands_poe_state1 = tk.Label(self.__frame_device_commands_for_poe,text='On or Off')
        self.__lbl_device_commands_poe_state1.grid(column=1,row=0,sticky='nw')
        self.__btn_cmd_poe_state = tk.Button(self.__frame_device_commands_for_poe,text='State',width=15,command=self.__cmd_state_selected_device)
        self.__btn_cmd_poe_state.bind('<Return>',enter_on_button(self.__cmd_state_selected_device))
        self.__btn_cmd_poe_state.grid(column=0,row=1,sticky='nw')
        self.__tb_cmd_poe_state1 = tk.Text(self.__frame_device_commands_for_poe,height=1,width=20,wrap='none')
        self.__tb_cmd_poe_state1.bind('<Tab>',focus_target_widget(self.__btn_cmd_poe_state))
        self.__tb_cmd_poe_state1.grid(column=1,row=1,sticky='nw')
        #Toggle
        self.__btn_cmd_poe_toggle = tk.Button(self.__frame_device_commands_for_poe,text='Toggle',width=15,command=self.__cmd_toggle_selected_device)
        self.__btn_cmd_poe_toggle.grid(column=0,row=2,sticky='nw')

        ''' relay '''
        self.__frame_device_commands_for_relay = tk.Frame(self.__frame_device_commands)
        self.__frame_device_commands_for_relay.grid(column=0,row=8,sticky='nw')
        #Pulse(duration)
        self.__lbl_device_commands_relay_pulse1 = tk.Label(self.__frame_device_commands_for_relay,text='Duration')
        self.__lbl_device_commands_relay_pulse1.grid(column=1,row=0,sticky='nw')
        self.__btn_cmd_relay_pulse = tk.Button(self.__frame_device_commands_for_relay,text='Pulse',width=15,command=self.__cmd_pulse_selected_device)
        self.__btn_cmd_relay_pulse.bind('<Return>',enter_on_button(self.__cmd_pulse_selected_device))
        self.__btn_cmd_relay_pulse.grid(column=0,row=1,sticky='nw')
        self.__tb_cmd_relay_pulse1 = tk.Text(self.__frame_device_commands_for_relay,height=1,width=20,wrap='none')
        self.__tb_cmd_relay_pulse1.bind('<Tab>',focus_target_widget(self.__btn_cmd_relay_pulse))
        self.__tb_cmd_relay_pulse1.grid(column=1,row=1,sticky='nw')
        #State('Open' or 'Close')
        self.__lbl_device_commands_relay_state1 = tk.Label(self.__frame_device_commands_for_relay,text='Open or Close')
        self.__lbl_device_commands_relay_state1.grid(column=1,row=2,sticky='nw')
        self.__btn_cmd_relay_state = tk.Button(self.__frame_device_commands_for_relay,text='State',width=15,command=self.__cmd_state_selected_device)
        self.__btn_cmd_relay_state.bind('<Return>',enter_on_button(self.__cmd_state_selected_device))
        self.__btn_cmd_relay_state.grid(column=0,row=3,sticky='nw')
        self.__tb_cmd_relay_state1 = tk.Text(self.__frame_device_commands_for_relay,height=1,width=20,wrap='none')
        self.__tb_cmd_relay_state1.bind('<Tab>',focus_target_widget(self.__btn_cmd_relay_state))
        self.__tb_cmd_relay_state1.grid(column=1,row=3,sticky='nw')
        #Toggle
        self.__btn_cmd_relay_toggle = tk.Button(self.__frame_device_commands_for_relay,text='Toggle',width=15,command=self.__cmd_toggle_selected_device)
        self.__btn_cmd_relay_toggle.grid(column=0,row=4,sticky='nw')

        ''' swac receptacle '''
        self.__frame_device_commands_for_swac_receptacle = tk.Frame(self.__frame_device_commands)
        self.__frame_device_commands_for_swac_receptacle.grid(column=0,row=9,sticky='nw')
        #State('On' or 'Off')
        self.__lbl_device_commands_swac_receptacle_state1 = tk.Label(self.__frame_device_commands_for_swac_receptacle,text='On or Off')
        self.__lbl_device_commands_swac_receptacle_state1.grid(column=1,row=0,sticky='nw')
        self.__btn_cmd_swac_receptacle_state = tk.Button(self.__frame_device_commands_for_swac_receptacle,text='State',width=15,command=self.__cmd_state_selected_device)
        self.__btn_cmd_swac_receptacle_state.bind('<Return>',enter_on_button(self.__cmd_state_selected_device))
        self.__btn_cmd_swac_receptacle_state.grid(column=0,row=1,sticky='nw')
        self.__tb_cmd_swac_receptacle_state1 = tk.Text(self.__frame_device_commands_for_swac_receptacle,height=1,width=20,wrap='none')
        self.__tb_cmd_swac_receptacle_state1.bind('<Tab>',focus_target_widget(self.__btn_cmd_swac_receptacle_state))
        self.__tb_cmd_swac_receptacle_state1.grid(column=1,row=1,sticky='nw')
        #Toggle
        self.__btn_cmd_swac_receptacle_toggle = tk.Button(self.__frame_device_commands_for_swac_receptacle,text='Toggle',width=15,command=self.__cmd_state_selected_device)
        self.__btn_cmd_swac_receptacle_toggle.bind('<Return>',enter_on_button(self.__cmd_state_selected_device))
        self.__btn_cmd_swac_receptacle_toggle.grid(column=0,row=2,sticky='nw')

        ''' sw power '''
        self.__frame_device_commands_for_sw_power = tk.Frame(self.__frame_device_commands)
        self.__frame_device_commands_for_sw_power.grid(column=0,row=10,sticky='nw')
        #Pulse(duration)
        self.__lbl_device_commands_sw_power_pulse1 = tk.Label(self.__frame_device_commands_for_sw_power,text='Duration')
        self.__lbl_device_commands_sw_power_pulse1.grid(column=1,row=0,sticky='nw')
        self.__btn_cmd_sw_power_pulse = tk.Button(self.__frame_device_commands_for_sw_power,text='Pulse',width=15,command=self.__cmd_pulse_selected_device)
        self.__btn_cmd_sw_power_pulse.bind('<Return>',enter_on_button(self.__cmd_pulse_selected_device))
        self.__btn_cmd_sw_power_pulse.grid(column=0,row=1,sticky='nw')
        self.__tb_cmd_sw_power_pulse1 = tk.Text(self.__frame_device_commands_for_sw_power,height=1,width=20,wrap='none')
        self.__tb_cmd_sw_power_pulse1.bind('<Tab>',focus_target_widget(self.__btn_cmd_sw_power_pulse))
        self.__tb_cmd_sw_power_pulse1.grid(column=1,row=1,sticky='nw')
        #State('Open' or 'Close')
        self.__lbl_device_commands_sw_power_state1 = tk.Label(self.__frame_device_commands_for_sw_power,text='Open or Close')
        self.__lbl_device_commands_sw_power_state1.grid(column=1,row=2,sticky='nw')
        self.__btn_cmd_sw_power_state = tk.Button(self.__frame_device_commands_for_sw_power,text='State',width=15,command=self.__cmd_state_selected_device)
        self.__btn_cmd_sw_power_state.bind('<Return>',enter_on_button(self.__cmd_state_selected_device))
        self.__btn_cmd_sw_power_state.grid(column=0,row=3,sticky='nw')
        self.__tb_cmd_sw_power_state1 = tk.Text(self.__frame_device_commands_for_sw_power,height=1,width=20,wrap='none')
        self.__tb_cmd_sw_power_state1.bind('<Tab>',focus_target_widget(self.__btn_cmd_sw_power_state))
        self.__tb_cmd_sw_power_state1.grid(column=1,row=3,sticky='nw')
        #Toggle
        self.__btn_cmd_sw_power_toggle = tk.Button(self.__frame_device_commands_for_sw_power,text='Toggle',width=15,command=self.__cmd_toggle_selected_device)
        self.__btn_cmd_sw_power_toggle.grid(column=0,row=4,sticky='nw')

        ''' tally '''
        self.__frame_device_commands_for_tally = tk.Frame(self.__frame_device_commands)
        self.__frame_device_commands_for_tally.grid(column=0,row=11,sticky='nw')
        #Pulse(duration)
        self.__lbl_device_commands_tally_pulse1 = tk.Label(self.__frame_device_commands_for_tally,text='Duration')
        self.__lbl_device_commands_tally_pulse1.grid(column=1,row=0,sticky='nw')
        self.__btn_cmd_tally_pulse = tk.Button(self.__frame_device_commands_for_tally,text='Pulse',width=15,command=self.__cmd_pulse_selected_device)
        self.__btn_cmd_tally_pulse.bind('<Return>',enter_on_button(self.__cmd_pulse_selected_device))
        self.__btn_cmd_tally_pulse.grid(column=0,row=1,sticky='nw')
        self.__tb_cmd_tally_pulse1 = tk.Text(self.__frame_device_commands_for_tally,height=1,width=20,wrap='none')
        self.__tb_cmd_tally_pulse1.bind('<Tab>',focus_target_widget(self.__btn_cmd_tally_pulse))
        self.__tb_cmd_tally_pulse1.grid(column=1,row=1,sticky='nw')
        #State('On' or 'Off')
        self.__lbl_device_commands_tally_state1 = tk.Label(self.__frame_device_commands_for_tally,text='On or Off')
        self.__lbl_device_commands_tally_state1.grid(column=1,row=2,sticky='nw')
        self.__btn_cmd_tally_state = tk.Button(self.__frame_device_commands_for_tally,text='State',width=15,command=self.__cmd_state_selected_device)
        self.__btn_cmd_tally_state.bind('<Return>',enter_on_button(self.__cmd_state_selected_device))
        self.__btn_cmd_tally_state.grid(column=0,row=3,sticky='nw')
        self.__tb_cmd_tally_state1 = tk.Text(self.__frame_device_commands_for_tally,height=1,width=20,wrap='none')
        self.__tb_cmd_tally_state1.bind('<Tab>',focus_target_widget(self.__btn_cmd_tally_state))
        self.__tb_cmd_tally_state1.grid(column=1,row=3,sticky='nw')
        #Toggle
        self.__btn_cmd_tally_toggle = tk.Button(self.__frame_device_commands_for_tally,text='Toggle',width=15,command=self.__cmd_toggle_selected_device)
        self.__btn_cmd_tally_toggle.grid(column=0,row=4,sticky='nw')

        ''' volume '''
        self.__frame_device_commands_for_volume = tk.Frame(self.__frame_device_commands)
        self.__frame_device_commands_for_volume.grid(column=0,row=12,sticky='nw')
        #Level(value)
        self.__lbl_device_commands_volume_level1 = tk.Label(self.__frame_device_commands_for_volume,text='Number')
        self.__lbl_device_commands_volume_level1.grid(column=1,row=0,sticky='nw')
        self.__btn_cmd_volume_level = tk.Button(self.__frame_device_commands_for_volume,text='Volume',width=15,command=self.__cmd_level_selected_device)
        self.__btn_cmd_volume_level.bind('<Return>',enter_on_button(self.__cmd_level_selected_device))
        self.__btn_cmd_volume_level.grid(column=0,row=1,sticky='nw')
        self.__tb_cmd_volume_level1 = tk.Text(self.__frame_device_commands_for_volume,height=1,width=20,wrap='none')
        self.__tb_cmd_volume_level1.bind('<Tab>',focus_target_widget(self.__btn_cmd_volume_level))
        self.__tb_cmd_volume_level1.grid(column=1,row=1,sticky='nw')
        #Mute('On' or 'Off')
        self.__lbl_device_commands_volume_mute1 = tk.Label(self.__frame_device_commands_for_volume,text='On or Off')
        self.__lbl_device_commands_volume_mute1.grid(column=1,row=2,sticky='nw')
        self.__btn_cmd_volume_mute = tk.Button(self.__frame_device_commands_for_volume,text='Mute',width=15,command=self.__cmd_mute_selected_device)
        self.__btn_cmd_volume_mute.bind('<Return>',enter_on_button(self.__cmd_mute_selected_device))
        self.__btn_cmd_volume_mute.grid(column=0,row=3,sticky='nw')
        self.__tb_cmd_volume_mute1 = tk.Text(self.__frame_device_commands_for_volume,height=1,width=20,wrap='none')
        self.__tb_cmd_volume_mute1.bind('<Tab>',focus_target_widget(self.__btn_cmd_volume_mute))
        self.__tb_cmd_volume_mute1.grid(column=1,row=3,sticky='nw')
        #Range(min,max)
        self.__lbl_device_commands_volume_range1 = tk.Label(self.__frame_device_commands_for_volume,text='Min')
        self.__lbl_device_commands_volume_range1.grid(column=1,row=4,sticky='nw')
        self.__lbl_device_commands_volume_range1 = tk.Label(self.__frame_device_commands_for_volume,text='Max')
        self.__lbl_device_commands_volume_range1.grid(column=2,row=4,sticky='nw')
        self.__btn_cmd_volume_range = tk.Button(self.__frame_device_commands_for_volume,text='Range',width=15,command=self.__cmd_range_selected_device)
        self.__btn_cmd_volume_range.bind('<Return>',enter_on_button(self.__cmd_range_selected_device))
        self.__btn_cmd_volume_range.grid(column=0,row=5,sticky='nw')
        self.__tb_cmd_volume_range1 = tk.Text(self.__frame_device_commands_for_volume,height=1,width=20,wrap='none')
        self.__tb_cmd_volume_range1.bind('<Tab>',focus_next_widget)
        self.__tb_cmd_volume_range1.grid(column=1,row=5,sticky='nw')
        self.__tb_cmd_volume_range2 = tk.Text(self.__frame_device_commands_for_volume,height=1,width=20,wrap='none')
        self.__tb_cmd_volume_range2.bind('<Tab>',focus_target_widget(self.__btn_cmd_volume_range))
        self.__tb_cmd_volume_range2.grid(column=2,row=5,sticky='nw')
        #SoftStart('Enabled' or 'Disabled')
        self.__lbl_device_commands_volume_softstart1 = tk.Label(self.__frame_device_commands_for_volume,text='Enabled or Disabled')
        self.__lbl_device_commands_volume_softstart1.grid(column=1,row=6,sticky='nw')
        self.__btn_cmd_volume_softstart = tk.Button(self.__frame_device_commands_for_volume,text='SoftStart',width=15,command=self.__cmd_softstart_selected_device)
        self.__btn_cmd_volume_softstart.bind('<Return>',enter_on_button(self.__cmd_softstart_selected_device))
        self.__btn_cmd_volume_softstart.grid(column=0,row=7,sticky='nw')
        self.__tb_cmd_volume_softstart1 = tk.Text(self.__frame_device_commands_for_volume,height=1,width=20,wrap='none')
        self.__tb_cmd_volume_softstart1.bind('<Tab>',focus_target_widget(self.__btn_cmd_volume_softstart))
        self.__tb_cmd_volume_softstart1.grid(column=1,row=7,sticky='nw')

        ''' processor '''
        self.__frame_device_commands_for_processor = tk.Frame(self.__frame_device_commands)
        self.__frame_device_commands_for_processor.grid(column=0,row=13,sticky='nw')
        #Reboot()
        self.__btn_cmd_processor_reboot = tk.Button(self.__frame_device_commands_for_processor,text='Reboot',width=15,command=self.__cmd_reboot_selected_device)
        self.__btn_cmd_processor_reboot.grid(column=0,row=0,sticky='nw')
        #SaveProgramLog()
        self.__btn_cmd_processor_savepgmlog = tk.Button(self.__frame_device_commands_for_processor,text='SaveProgramLog',width=15,command=self.__cmd_savepgmlog_selected_device)
        self.__btn_cmd_processor_savepgmlog.grid(column=0,row=1,sticky='nw')
        #ExecutiveMode(int)
        self.__lbl_device_commands_processor_executivemode1 = tk.Label(self.__frame_device_commands_for_processor,text='Only available on PCS1 models')
        self.__lbl_device_commands_processor_executivemode1.grid(column=1,row=2,sticky='nw')
        self.__btn_cmd_processor_executivemode = tk.Button(self.__frame_device_commands_for_processor,text='ExecutiveMode',width=15,command=self.__cmd_executivemode_selected_device)
        self.__btn_cmd_processor_executivemode.bind('<Return>',enter_on_button(self.__cmd_executivemode_selected_device))
        self.__btn_cmd_processor_executivemode.grid(column=0,row=3,sticky='nw')
        self.__tb_cmd_processor_executivemode1 = tk.Text(self.__frame_device_commands_for_processor,height=1,width=20,wrap='none')
        self.__tb_cmd_processor_executivemode1.bind('<Tab>',focus_target_widget(self.__btn_cmd_processor_executivemode))
        self.__tb_cmd_processor_executivemode1.grid(column=1,row=3,sticky='nw')

        ''' spdevice '''
        self.__frame_device_commands_for_spdevice = tk.Frame(self.__frame_device_commands)
        self.__frame_device_commands_for_spdevice.grid(column=0,row=14,sticky='nw')
        #Reboot()
        self.__btn_cmd_spdevice_reboot = tk.Button(self.__frame_device_commands_for_spdevice,text='Reboot',width=15,command=self.__cmd_reboot_selected_device)
        self.__btn_cmd_spdevice_reboot.grid(column=0,row=0,sticky='nw')
        ''' ebusdevice '''
        self.__frame_device_commands_for_ebusdevice = tk.Frame(self.__frame_device_commands)
        self.__frame_device_commands_for_ebusdevice.grid(column=0,row=14,sticky='nw')
        #Reboot()
        self.__btn_cmd_ebusdevice_reboot = tk.Button(self.__frame_device_commands_for_ebusdevice,text='Reboot',width=15,command=self.__cmd_reboot_selected_device)
        self.__btn_cmd_ebusdevice_reboot.grid(column=0,row=0,sticky='nw')
        #Wake()
        self.__btn_cmd_ebusdevice_wake = tk.Button(self.__frame_device_commands_for_ebusdevice,text='Wake',width=15,command=self.__cmd_wake_selected_device)
        self.__btn_cmd_ebusdevice_wake.grid(column=0,row=1,sticky='nw')
        #Sleep()
        self.__btn_cmd_ebusdevice_sleep = tk.Button(self.__frame_device_commands_for_ebusdevice,text='Sleep',width=15,command=self.__cmd_sleep_selected_device)
        self.__btn_cmd_ebusdevice_sleep.grid(column=0,row=2,sticky='nw')
        #Mute('On' or 'Off')
        self.__lbl_device_commands_ebusdevice_mute1 = tk.Label(self.__frame_device_commands_for_ebusdevice,text='On or Off')
        self.__lbl_device_commands_ebusdevice_mute1.grid(column=1,row=3,sticky='nw')
        self.__btn_cmd_ebusdevice_mute = tk.Button(self.__frame_device_commands_for_ebusdevice,text='Mute',width=15,command=self.__cmd_mute_selected_device)
        self.__btn_cmd_ebusdevice_mute.bind('<Return>',enter_on_button(self.__cmd_mute_selected_device))
        self.__btn_cmd_ebusdevice_mute.grid(column=0,row=4,sticky='nw')
        self.__tb_cmd_ebusdevice_mute1 = tk.Text(self.__frame_device_commands_for_ebusdevice,height=1,width=20,wrap='none')
        self.__tb_cmd_ebusdevice_mute1.bind('<Tab>',focus_target_widget(self.__btn_cmd_ebusdevice_mute))
        self.__tb_cmd_ebusdevice_mute1.grid(column=1,row=4,sticky='nw')

        ''' ui '''
        self.__frame_device_commands_for_ui = tk.Frame(self.__frame_device_commands)
        self.__frame_device_commands_for_ui.grid(column=0,row=15,sticky='nw')
        #ShowPage(str)
        self.__lbl_device_commands_ui_showpage1 = tk.Label(self.__frame_device_commands_for_ui,text='Page Name')
        self.__lbl_device_commands_ui_showpage1.grid(column=1,row=0,sticky='nw')
        self.__btn_cmd_ui_showpage = tk.Button(self.__frame_device_commands_for_ui,text='ShowPage',width=15,command=self.__cmd_showpage_selected_device)
        self.__btn_cmd_ui_showpage.bind('<Return>',enter_on_button(self.__cmd_showpage_selected_device))
        self.__btn_cmd_ui_showpage.grid(column=0,row=1,sticky='nw')
        self.__tb_cmd_ui_showpage1 = tk.Text(self.__frame_device_commands_for_ui,height=1,width=20,wrap='none')
        self.__tb_cmd_ui_showpage1.bind('<Tab>',focus_target_widget(self.__btn_cmd_ui_showpage))
        self.__tb_cmd_ui_showpage1.grid(column=1,row=1,sticky='nw')
        #ShowPopup(str,int)
        self.__lbl_device_commands_ui_showpopup1 = tk.Label(self.__frame_device_commands_for_ui,text='Popup Name')
        self.__lbl_device_commands_ui_showpopup1.grid(column=1,row=2,sticky='nw')
        self.__lbl_device_commands_ui_showpopup2 = tk.Label(self.__frame_device_commands_for_ui,text='Duration(int,optional)')
        self.__lbl_device_commands_ui_showpopup2.grid(column=2,row=2,sticky='nw')
        self.__btn_cmd_ui_showpopup = tk.Button(self.__frame_device_commands_for_ui,text='ShowPopup',width=15,command=self.__cmd_showpopup_selected_device)
        self.__btn_cmd_ui_showpopup.bind('<Return>',enter_on_button(self.__cmd_showpopup_selected_device))
        self.__btn_cmd_ui_showpopup.grid(column=0,row=3,sticky='nw')
        self.__tb_cmd_ui_showpopup1 = tk.Text(self.__frame_device_commands_for_ui,height=1,width=20,wrap='none')
        self.__tb_cmd_ui_showpopup1.bind('<Tab>',focus_next_widget)
        self.__tb_cmd_ui_showpopup1.grid(column=1,row=3,sticky='nw')
        self.__tb_cmd_ui_showpopup2 = tk.Text(self.__frame_device_commands_for_ui,height=1,width=20,wrap='none')
        self.__tb_cmd_ui_showpopup2.bind('<Tab>',focus_target_widget(self.__btn_cmd_ui_showpopup))
        self.__tb_cmd_ui_showpopup2.grid(column=2,row=3,sticky='nw')
        #HidePopup(str)
        self.__lbl_device_commands_ui_hidepopup1 = tk.Label(self.__frame_device_commands_for_ui,text='Page Name')
        self.__lbl_device_commands_ui_hidepopup1.grid(column=1,row=4,sticky='nw')
        self.__btn_cmd_ui_hidepopup = tk.Button(self.__frame_device_commands_for_ui,text='HidePopup',width=15,command=self.__cmd_hidepopup_selected_device)
        self.__btn_cmd_ui_hidepopup.bind('<Return>',enter_on_button(self.__cmd_hidepopup_selected_device))
        self.__btn_cmd_ui_hidepopup.grid(column=0,row=5,sticky='nw')
        self.__tb_cmd_ui_hidepopup1 = tk.Text(self.__frame_device_commands_for_ui,height=1,width=20,wrap='none')
        self.__tb_cmd_ui_hidepopup1.bind('<Tab>',focus_target_widget(self.__btn_cmd_ui_hidepopup))
        self.__tb_cmd_ui_hidepopup1.grid(column=1,row=5,sticky='nw')
        #HidePopupGroup(int)
        self.__lbl_device_commands_ui_hidepopupgroup1 = tk.Label(self.__frame_device_commands_for_ui,text='Group ID(int)')
        self.__lbl_device_commands_ui_hidepopupgroup1.grid(column=1,row=4,sticky='nw')
        self.__btn_cmd_ui_hidepopupgroup = tk.Button(self.__frame_device_commands_for_ui,text='HidePopupGroup',width=15,command=self.__cmd_hidepopupgroup_selected_device)
        self.__btn_cmd_ui_hidepopupgroup.bind('<Return>',enter_on_button(self.__cmd_hidepopupgroup_selected_device))
        self.__btn_cmd_ui_hidepopupgroup.grid(column=0,row=5,sticky='nw')
        self.__tb_cmd_ui_hidepopupgroup1 = tk.Text(self.__frame_device_commands_for_ui,height=1,width=20,wrap='none')
        self.__tb_cmd_ui_hidepopupgroup1.bind('<Tab>',focus_target_widget(self.__btn_cmd_ui_hidepopupgroup))
        self.__tb_cmd_ui_hidepopupgroup1.grid(column=1,row=5,sticky='nw')
        #HideAllPopups()
        self.__btn_cmd_ui_hideallpopups = tk.Button(self.__frame_device_commands_for_ui,text='HideAllPopups',width=15,command=self.__cmd_hideallpopups_selected_device)
        self.__btn_cmd_ui_hideallpopups.grid(column=0,row=6,sticky='nw')
        #Wake()
        self.__btn_cmd_ui_wake = tk.Button(self.__frame_device_commands_for_ui,text='Wake',width=15,command=self.__cmd_wake_selected_device)
        self.__btn_cmd_ui_wake.grid(column=0,row=7,sticky='nw')
        #Sleep()
        self.__btn_cmd_ui_sleep = tk.Button(self.__frame_device_commands_for_ui,text='Sleep',width=15,command=self.__cmd_sleep_selected_device)
        self.__btn_cmd_ui_sleep.grid(column=0,row=8,sticky='nw')
        #Reboot()
        self.__btn_cmd_ui_reboot = tk.Button(self.__frame_device_commands_for_ui,text='Reboot',width=15,command=self.__cmd_reboot_selected_device)
        self.__btn_cmd_ui_reboot.grid(column=0,row=9,sticky='nw')

        ''' print ui '''
        self.__frame_device_print = tk.Frame(self.__frame_device_commands)
        self.__frame_device_print.grid(column=0,row=16,sticky='nw')

        ''' virtual ui '''
        self.__frame_device_virtualui = tk.Frame(self.__frame_device_commands)
        self.__frame_device_virtualui.grid(column=0,row=17,sticky='nw')

        self.__frame_device_modes_for_virtualui = tk.Frame(self.__frame_device_virtualui)
        self.__frame_device_modes_for_virtualui.grid(column=0,row=0,sticky='nw')
        self.__btn_mode_virtualui_navigation = tk.Button(self.__frame_device_modes_for_virtualui,text='Navigation',width=15,command=self.__set_device_virtualui_mode('Navigation'))
        self.__btn_mode_virtualui_navigation.grid(column=0,row=0,sticky='nw')
        self.__btn_mode_virtualui_buttons = tk.Button(self.__frame_device_modes_for_virtualui,text='Button',width=15,command=self.__set_device_virtualui_mode('Button'))
        self.__btn_mode_virtualui_buttons.grid(column=1,row=0,sticky='nw')
        self.__btn_mode_virtualui_knobs = tk.Button(self.__frame_device_modes_for_virtualui,text='Knob',width=15,command=self.__set_device_virtualui_mode('Knob'))
        self.__btn_mode_virtualui_knobs.grid(column=2,row=0,sticky='nw')
        self.__btn_mode_virtualui_labels = tk.Button(self.__frame_device_modes_for_virtualui,text='Label',width=15,command=self.__set_device_virtualui_mode('Label'))
        self.__btn_mode_virtualui_labels.grid(column=3,row=0,sticky='nw')
        self.__btn_mode_virtualui_levels = tk.Button(self.__frame_device_modes_for_virtualui,text='Level',width=15,command=self.__set_device_virtualui_mode('Level'))
        self.__btn_mode_virtualui_levels.grid(column=4,row=0,sticky='nw')
        self.__btn_mode_virtualui_sliders = tk.Button(self.__frame_device_modes_for_virtualui,text='Slider',width=15,command=self.__set_device_virtualui_mode('Slider'))
        self.__btn_mode_virtualui_sliders.grid(column=5,row=0,sticky='nw')

        self.__frame_device_commands_for_virtualui_navigation = tk.Frame(self.__frame_device_virtualui)
        self.__frame_device_commands_for_virtualui_navigation.grid(column=0,row=1,sticky='nw')
        #ShowPage(str)
        self.__lbl_device_commands_virtualui_showpage1 = tk.Label(self.__frame_device_commands_for_virtualui_navigation,text='Page Name')
        self.__lbl_device_commands_virtualui_showpage1.grid(column=1,row=0,sticky='nw')
        self.__btn_cmd_virtualui_showpage = tk.Button(self.__frame_device_commands_for_virtualui_navigation,text='ShowPage',width=15,command=self.__cmd_showpage_selected_device)
        self.__btn_cmd_virtualui_showpage.bind('<Return>',enter_on_button(self.__cmd_showpage_selected_device))
        self.__btn_cmd_virtualui_showpage.grid(column=0,row=1,sticky='nw')
        self.__tb_cmd_virtualui_showpage1 = tk.Text(self.__frame_device_commands_for_virtualui_navigation,height=1,width=20,wrap='none')
        self.__tb_cmd_virtualui_showpage1.bind('<Tab>',focus_target_widget(self.__btn_cmd_virtualui_showpage))
        self.__tb_cmd_virtualui_showpage1.grid(column=1,row=1,sticky='nw')
        #ShowPopup(str,int)
        self.__lbl_device_commands_virtualui_showpopup1 = tk.Label(self.__frame_device_commands_for_virtualui_navigation,text='Popup Name')
        self.__lbl_device_commands_virtualui_showpopup1.grid(column=1,row=2,sticky='nw')
        self.__lbl_device_commands_virtualui_showpopup2 = tk.Label(self.__frame_device_commands_for_virtualui_navigation,text='Duration(int,optional)')
        self.__lbl_device_commands_virtualui_showpopup2.grid(column=2,row=2,sticky='nw')
        self.__btn_cmd_virtualui_showpopup = tk.Button(self.__frame_device_commands_for_virtualui_navigation,text='ShowPopup',width=15,command=self.__cmd_showpopup_selected_device)
        self.__btn_cmd_virtualui_showpopup.bind('<Return>',enter_on_button(self.__cmd_showpopup_selected_device))
        self.__btn_cmd_virtualui_showpopup.grid(column=0,row=3,sticky='nw')
        self.__tb_cmd_virtualui_showpopup1 = tk.Text(self.__frame_device_commands_for_virtualui_navigation,height=1,width=20,wrap='none')
        self.__tb_cmd_virtualui_showpopup1.bind('<Tab>',focus_next_widget)
        self.__tb_cmd_virtualui_showpopup1.grid(column=1,row=3,sticky='nw')
        self.__tb_cmd_virtualui_showpopup2 = tk.Text(self.__frame_device_commands_for_virtualui_navigation,height=1,width=20,wrap='none')
        self.__tb_cmd_virtualui_showpopup2.bind('<Tab>',focus_target_widget(self.__btn_cmd_virtualui_showpopup))
        self.__tb_cmd_virtualui_showpopup2.grid(column=2,row=3,sticky='nw')
        #HidePopup(str)
        self.__lbl_device_commands_virtualui_hidepopup1 = tk.Label(self.__frame_device_commands_for_virtualui_navigation,text='Page Name')
        self.__lbl_device_commands_virtualui_hidepopup1.grid(column=1,row=4,sticky='nw')
        self.__btn_cmd_virtualui_hidepopup = tk.Button(self.__frame_device_commands_for_virtualui_navigation,text='HidePopup',width=15,command=self.__cmd_hidepopup_selected_device)
        self.__btn_cmd_virtualui_hidepopup.bind('<Return>',enter_on_button(self.__cmd_hidepopup_selected_device))
        self.__btn_cmd_virtualui_hidepopup.grid(column=0,row=5,sticky='nw')
        self.__tb_cmd_virtualui_hidepopup1 = tk.Text(self.__frame_device_commands_for_virtualui_navigation,height=1,width=20,wrap='none')
        self.__tb_cmd_virtualui_hidepopup1.bind('<Tab>',focus_target_widget(self.__btn_cmd_virtualui_hidepopup))
        self.__tb_cmd_virtualui_hidepopup1.grid(column=1,row=5,sticky='nw')
        #HidePopupGroup(int)
        self.__lbl_device_commands_virtualui_hidepopupgroup1 = tk.Label(self.__frame_device_commands_for_virtualui_navigation,text='Group ID(int)')
        self.__lbl_device_commands_virtualui_hidepopupgroup1.grid(column=1,row=6,sticky='nw')
        self.__btn_cmd_virtualui_hidepopupgroup = tk.Button(self.__frame_device_commands_for_virtualui_navigation,text='HidePopupGroup',width=15,command=self.__cmd_hidepopupgroup_selected_device)
        self.__btn_cmd_virtualui_hidepopupgroup.bind('<Return>',enter_on_button(self.__cmd_hidepopupgroup_selected_device))
        self.__btn_cmd_virtualui_hidepopupgroup.grid(column=0,row=7,sticky='nw')
        self.__tb_cmd_virtualui_hidepopupgroup1 = tk.Text(self.__frame_device_commands_for_virtualui_navigation,height=1,width=20,wrap='none')
        self.__tb_cmd_virtualui_hidepopupgroup1.bind('<Tab>',focus_target_widget(self.__btn_cmd_virtualui_hidepopupgroup))
        self.__tb_cmd_virtualui_hidepopupgroup1.grid(column=1,row=7,sticky='nw')
        #HideAllPopups()
        self.__btn_cmd_virtualui_hideallpopups = tk.Button(self.__frame_device_commands_for_virtualui_navigation,text='HideAllPopups',width=15,command=self.__cmd_hideallpopups_selected_device)
        self.__btn_cmd_virtualui_hideallpopups.grid(column=0,row=8,sticky='nw')

        self.__frame_device_commands_for_virtualui_button = tk.Frame(self.__frame_device_virtualui)
        self.__frame_device_commands_for_virtualui_button.grid(column=0,row=2,sticky='nw')
        #SetState(list[int],int)
        self.__lbl_device_commands_virtualui_button_setstate1 = tk.Label(self.__frame_device_commands_for_virtualui_button,text='IDs(comma separated list of ints)')
        self.__lbl_device_commands_virtualui_button_setstate1.grid(column=1,row=0,sticky='nw')
        self.__lbl_device_commands_virtualui_button_setstate2 = tk.Label(self.__frame_device_commands_for_virtualui_button,text='State(int)')
        self.__lbl_device_commands_virtualui_button_setstate2.grid(column=2,row=0,sticky='nw')
        self.__btn_cmd_virtualui_button_setstate = tk.Button(self.__frame_device_commands_for_virtualui_button,text='SetState',width=15,command=self.__cmd_setstate_selected_device)
        self.__btn_cmd_virtualui_button_setstate.bind('<Return>',enter_on_button(self.__cmd_setstate_selected_device))
        self.__btn_cmd_virtualui_button_setstate.grid(column=0,row=1,sticky='nw')
        self.__tb_cmd_virtualui_button_setstate1 = tk.Text(self.__frame_device_commands_for_virtualui_button,height=1,width=20,wrap='none')
        self.__tb_cmd_virtualui_button_setstate1.bind('<Tab>',focus_next_widget)
        self.__tb_cmd_virtualui_button_setstate1.grid(column=1,row=1,sticky='nw')
        self.__tb_cmd_virtualui_button_setstate2 = tk.Text(self.__frame_device_commands_for_virtualui_button,height=1,width=20,wrap='none')
        self.__tb_cmd_virtualui_button_setstate2.bind('<Tab>',focus_target_widget(self.__btn_cmd_virtualui_button_setstate))
        self.__tb_cmd_virtualui_button_setstate2.grid(column=2,row=1,sticky='nw')
        #SetText(list[int],str)
        self.__lbl_device_commands_virtualui_button_settext1 = tk.Label(self.__frame_device_commands_for_virtualui_button,text='IDs(comma separated list of ints)')
        self.__lbl_device_commands_virtualui_button_settext1.grid(column=1,row=2,sticky='nw')
        self.__lbl_device_commands_virtualui_button_settext2 = tk.Label(self.__frame_device_commands_for_virtualui_button,text='Text')
        self.__lbl_device_commands_virtualui_button_settext2.grid(column=2,row=2,sticky='nw')
        self.__btn_cmd_virtualui_button_settext = tk.Button(self.__frame_device_commands_for_virtualui_button,text='SetText',width=15,command=self.__cmd_settext_selected_device)
        self.__btn_cmd_virtualui_button_settext.bind('<Return>',enter_on_button(self.__cmd_settext_selected_device))
        self.__btn_cmd_virtualui_button_settext.grid(column=0,row=3,sticky='nw')
        self.__tb_cmd_virtualui_button_settext1 = tk.Text(self.__frame_device_commands_for_virtualui_button,height=1,width=20,wrap='none')
        self.__tb_cmd_virtualui_button_settext1.bind('<Tab>',focus_next_widget)
        self.__tb_cmd_virtualui_button_settext1.grid(column=1,row=3,sticky='nw')
        self.__tb_cmd_virtualui_button_settext2 = tk.Text(self.__frame_device_commands_for_virtualui_button,height=1,width=20,wrap='none')
        self.__tb_cmd_virtualui_button_settext2.bind('<Tab>',focus_target_widget(self.__btn_cmd_virtualui_button_settext))
        self.__tb_cmd_virtualui_button_settext2.grid(column=2,row=3,sticky='nw')
        #SetVisible(list[int],bool)
        self.__lbl_device_commands_virtualui_button_setvisible1 = tk.Label(self.__frame_device_commands_for_virtualui_button,text='IDs(comma separated list of ints)')
        self.__lbl_device_commands_virtualui_button_setvisible1.grid(column=1,row=4,sticky='nw')
        self.__lbl_device_commands_virtualui_button_setvisible2 = tk.Label(self.__frame_device_commands_for_virtualui_button,text='True or False')
        self.__lbl_device_commands_virtualui_button_setvisible2.grid(column=2,row=4,sticky='nw')
        self.__btn_cmd_virtualui_button_setvisible = tk.Button(self.__frame_device_commands_for_virtualui_button,text='SetVisible',width=15,command=self.__cmd_setvisible_selected_device)
        self.__btn_cmd_virtualui_button_setvisible.bind('<Return>',enter_on_button(self.__cmd_setvisible_selected_device))
        self.__btn_cmd_virtualui_button_setvisible.grid(column=0,row=5,sticky='nw')
        self.__tb_cmd_virtualui_button_setvisible1 = tk.Text(self.__frame_device_commands_for_virtualui_button,height=1,width=20,wrap='none')
        self.__tb_cmd_virtualui_button_setvisible1.bind('<Tab>',focus_next_widget)
        self.__tb_cmd_virtualui_button_setvisible1.grid(column=1,row=5,sticky='nw')
        self.__tb_cmd_virtualui_button_setvisible2 = tk.Text(self.__frame_device_commands_for_virtualui_button,height=1,width=20,wrap='none')
        self.__tb_cmd_virtualui_button_setvisible2.bind('<Tab>',focus_target_widget(self.__btn_cmd_virtualui_button_setvisible))
        self.__tb_cmd_virtualui_button_setvisible2.grid(column=2,row=5,sticky='nw')
        #SetEnable(list[int],bool)
        self.__lbl_device_commands_virtualui_button_setenable1 = tk.Label(self.__frame_device_commands_for_virtualui_button,text='IDs(comma separated list of ints)')
        self.__lbl_device_commands_virtualui_button_setenable1.grid(column=1,row=6,sticky='nw')
        self.__lbl_device_commands_virtualui_button_setenable2 = tk.Label(self.__frame_device_commands_for_virtualui_button,text='True or False')
        self.__lbl_device_commands_virtualui_button_setenable2.grid(column=2,row=6,sticky='nw')
        self.__btn_cmd_virtualui_button_setenable = tk.Button(self.__frame_device_commands_for_virtualui_button,text='SetEnable',width=15,command=self.__cmd_setenable_selected_device)
        self.__btn_cmd_virtualui_button_setenable.bind('<Return>',enter_on_button(self.__cmd_setenable_selected_device))
        self.__btn_cmd_virtualui_button_setenable.grid(column=0,row=7,sticky='nw')
        self.__tb_cmd_virtualui_button_setenable1 = tk.Text(self.__frame_device_commands_for_virtualui_button,height=1,width=20,wrap='none')
        self.__tb_cmd_virtualui_button_setenable1.bind('<Tab>',focus_next_widget)
        self.__tb_cmd_virtualui_button_setenable1.grid(column=1,row=7,sticky='nw')
        self.__tb_cmd_virtualui_button_setenable2 = tk.Text(self.__frame_device_commands_for_virtualui_button,height=1,width=20,wrap='none')
        self.__tb_cmd_virtualui_button_setenable2.bind('<Tab>',focus_target_widget(self.__btn_cmd_virtualui_button_setenable))
        self.__tb_cmd_virtualui_button_setenable2.grid(column=2,row=7,sticky='nw')
        #SetBlinking(list[int],str,list[int])
        self.__lbl_device_commands_virtualui_button_setblinking1 = tk.Label(self.__frame_device_commands_for_virtualui_button,text='IDs(comma separated list of ints)')
        self.__lbl_device_commands_virtualui_button_setblinking1.grid(column=1,row=8,sticky='nw')
        self.__lbl_device_commands_virtualui_button_setblinking2 = tk.Label(self.__frame_device_commands_for_virtualui_button,text='Rate(Slow,Medium,Fast)')
        self.__lbl_device_commands_virtualui_button_setblinking2.grid(column=2,row=8,sticky='nw')
        self.__lbl_device_commands_virtualui_button_setblinking3 = tk.Label(self.__frame_device_commands_for_virtualui_button,text='States(comma separated list of ints)')
        self.__lbl_device_commands_virtualui_button_setblinking3.grid(column=3,row=8,sticky='nw')
        self.__btn_cmd_virtualui_button_setblinking = tk.Button(self.__frame_device_commands_for_virtualui_button,text='SetBlinking',width=15,command=self.__cmd_setblinking_selected_device)
        self.__btn_cmd_virtualui_button_setblinking.bind('<Return>',enter_on_button(self.__cmd_setblinking_selected_device))
        self.__btn_cmd_virtualui_button_setblinking.grid(column=0,row=9,sticky='nw')
        self.__tb_cmd_virtualui_button_setblinking1 = tk.Text(self.__frame_device_commands_for_virtualui_button,height=1,width=20,wrap='none')
        self.__tb_cmd_virtualui_button_setblinking1.bind('<Tab>',focus_next_widget)
        self.__tb_cmd_virtualui_button_setblinking1.grid(column=1,row=9,sticky='nw')
        self.__tb_cmd_virtualui_button_setblinking2 = tk.Text(self.__frame_device_commands_for_virtualui_button,height=1,width=20,wrap='none')
        self.__tb_cmd_virtualui_button_setblinking2.bind('<Tab>',focus_next_widget)
        self.__tb_cmd_virtualui_button_setblinking2.grid(column=2,row=9,sticky='nw')
        self.__tb_cmd_virtualui_button_setblinking3 = tk.Text(self.__frame_device_commands_for_virtualui_button,height=1,width=20,wrap='none')
        self.__tb_cmd_virtualui_button_setblinking3.bind('<Tab>',focus_target_widget(self.__btn_cmd_virtualui_button_setblinking))
        self.__tb_cmd_virtualui_button_setblinking3.grid(column=3,row=9,sticky='nw')
        #Emulate(int,str)
        self.__lbl_device_commands_virtualui_button_emulate1 = tk.Label(self.__frame_device_commands_for_virtualui_button,text='ID(int)')
        self.__lbl_device_commands_virtualui_button_emulate1.grid(column=1,row=10,sticky='nw')
        self.__lbl_device_commands_virtualui_button_emulate2 = tk.Label(self.__frame_device_commands_for_virtualui_button,text='Event Type\n(Pressed,Released,Held,Tapped)')
        self.__lbl_device_commands_virtualui_button_emulate2.grid(column=2,row=10,sticky='nw')
        self.__btn_cmd_virtualui_button_emulate = tk.Button(self.__frame_device_commands_for_virtualui_button,text='Emulate',width=15,command=self.__cmd_emulate_selected_device)
        self.__btn_cmd_virtualui_button_emulate.bind('<Return>',enter_on_button(self.__cmd_emulate_selected_device))
        self.__btn_cmd_virtualui_button_emulate.grid(column=0,row=11,sticky='nw')
        self.__tb_cmd_virtualui_button_emulate1 = tk.Text(self.__frame_device_commands_for_virtualui_button,height=1,width=20,wrap='none')
        self.__tb_cmd_virtualui_button_emulate1.bind('<Tab>',focus_next_widget)
        self.__tb_cmd_virtualui_button_emulate1.grid(column=1,row=11,sticky='nw')
        self.__tb_cmd_virtualui_button_emulate2 = tk.Text(self.__frame_device_commands_for_virtualui_button,height=1,width=20,wrap='none')
        self.__tb_cmd_virtualui_button_emulate2.bind('<Tab>',focus_target_widget(self.__btn_cmd_virtualui_button_emulate))
        self.__tb_cmd_virtualui_button_emulate2.grid(column=2,row=11,sticky='nw')

        self.__frame_device_commands_for_virtualui_knob = tk.Frame(self.__frame_device_virtualui)
        self.__frame_device_commands_for_virtualui_knob.grid(column=0,row=3,sticky='nw')
        #Emulate(int,str)
        self.__lbl_device_commands_virtualui_knob_emulate1 = tk.Label(self.__frame_device_commands_for_virtualui_knob,text='ID(int)')
        self.__lbl_device_commands_virtualui_knob_emulate1.grid(column=1,row=10,sticky='nw')
        self.__lbl_device_commands_virtualui_knob_emulate2 = tk.Label(self.__frame_device_commands_for_virtualui_knob,text='Turn Direction Steps(int)')
        self.__lbl_device_commands_virtualui_knob_emulate2.grid(column=2,row=10,sticky='nw')
        self.__btn_cmd_virtualui_knob_emulate = tk.Button(self.__frame_device_commands_for_virtualui_knob,text='Emulate',width=15,command=self.__cmd_emulate_selected_device)
        self.__btn_cmd_virtualui_knob_emulate.bind('<Return>',enter_on_button(self.__cmd_emulate_selected_device))
        self.__btn_cmd_virtualui_knob_emulate.grid(column=0,row=11,sticky='nw')
        self.__tb_cmd_virtualui_knob_emulate1 = tk.Text(self.__frame_device_commands_for_virtualui_knob,height=1,width=20,wrap='none')
        self.__tb_cmd_virtualui_knob_emulate1.bind('<Tab>',focus_next_widget)
        self.__tb_cmd_virtualui_knob_emulate1.grid(column=1,row=11,sticky='nw')
        self.__tb_cmd_virtualui_knob_emulate2 = tk.Text(self.__frame_device_commands_for_virtualui_knob,height=1,width=20,wrap='none')
        self.__tb_cmd_virtualui_knob_emulate2.bind('<Tab>',focus_target_widget(self.__btn_cmd_virtualui_knob_emulate))
        self.__tb_cmd_virtualui_knob_emulate2.grid(column=2,row=11,sticky='nw')

        self.__frame_device_commands_for_virtualui_label = tk.Frame(self.__frame_device_virtualui)
        self.__frame_device_commands_for_virtualui_label.grid(column=0,row=4,sticky='nw')
        #SetText(list[int],str)
        self.__lbl_device_commands_virtualui_label_settext1 = tk.Label(self.__frame_device_commands_for_virtualui_label,text='IDs(comma separated list of ints)')
        self.__lbl_device_commands_virtualui_label_settext1.grid(column=1,row=0,sticky='nw')
        self.__lbl_device_commands_virtualui_label_settext2 = tk.Label(self.__frame_device_commands_for_virtualui_label,text='Text')
        self.__lbl_device_commands_virtualui_label_settext2.grid(column=2,row=0,sticky='nw')
        self.__btn_cmd_virtualui_label_settext = tk.Button(self.__frame_device_commands_for_virtualui_label,text='SetText',width=15,command=self.__cmd_settext_selected_device)
        self.__btn_cmd_virtualui_label_settext.bind('<Return>',enter_on_button(self.__cmd_settext_selected_device))
        self.__btn_cmd_virtualui_label_settext.grid(column=0,row=1,sticky='nw')
        self.__tb_cmd_virtualui_label_settext1 = tk.Text(self.__frame_device_commands_for_virtualui_label,height=1,width=20,wrap='none')
        self.__tb_cmd_virtualui_label_settext1.bind('<Tab>',focus_next_widget)
        self.__tb_cmd_virtualui_label_settext1.grid(column=1,row=1,sticky='nw')
        self.__tb_cmd_virtualui_label_settext2 = tk.Text(self.__frame_device_commands_for_virtualui_label,height=1,width=20,wrap='none')
        self.__tb_cmd_virtualui_label_settext2.bind('<Tab>',focus_target_widget(self.__btn_cmd_virtualui_label_settext))
        self.__tb_cmd_virtualui_label_settext2.grid(column=2,row=1,sticky='nw')
        #SetVisible(list[int],bool)
        self.__lbl_device_commands_virtualui_label_setvisible1 = tk.Label(self.__frame_device_commands_for_virtualui_label,text='IDs(comma separated list of ints)')
        self.__lbl_device_commands_virtualui_label_setvisible1.grid(column=1,row=2,sticky='nw')
        self.__lbl_device_commands_virtualui_label_setvisible2 = tk.Label(self.__frame_device_commands_for_virtualui_label,text='True or False')
        self.__lbl_device_commands_virtualui_label_setvisible2.grid(column=2,row=2,sticky='nw')
        self.__btn_cmd_virtualui_label_setvisible = tk.Button(self.__frame_device_commands_for_virtualui_label,text='SetVisible',width=15,command=self.__cmd_setvisible_selected_device)
        self.__btn_cmd_virtualui_label_setvisible.bind('<Return>',enter_on_button(self.__cmd_setvisible_selected_device))
        self.__btn_cmd_virtualui_label_setvisible.grid(column=0,row=3,sticky='nw')
        self.__tb_cmd_virtualui_label_setvisible1 = tk.Text(self.__frame_device_commands_for_virtualui_label,height=1,width=20,wrap='none')
        self.__tb_cmd_virtualui_label_setvisible1.bind('<Tab>',focus_next_widget)
        self.__tb_cmd_virtualui_label_setvisible1.grid(column=1,row=3,sticky='nw')
        self.__tb_cmd_virtualui_label_setvisible2 = tk.Text(self.__frame_device_commands_for_virtualui_label,height=1,width=20,wrap='none')
        self.__tb_cmd_virtualui_label_setvisible2.bind('<Tab>',focus_target_widget(self.__btn_cmd_virtualui_label_setvisible))
        self.__tb_cmd_virtualui_label_setvisible2.grid(column=2,row=3,sticky='nw')

        self.__frame_device_commands_for_virtualui_level = tk.Frame(self.__frame_device_virtualui)
        self.__frame_device_commands_for_virtualui_level.grid(column=0,row=4,sticky='nw')
        #SetLevel(list[int],bool)
        self.__lbl_device_commands_virtualui_level_setlevel1 = tk.Label(self.__frame_device_commands_for_virtualui_level,text='IDs(comma separated list of ints)')
        self.__lbl_device_commands_virtualui_level_setlevel1.grid(column=1,row=0,sticky='nw')
        self.__lbl_device_commands_virtualui_level_setlevel2 = tk.Label(self.__frame_device_commands_for_virtualui_level,text='Value(int)')
        self.__lbl_device_commands_virtualui_level_setlevel2.grid(column=2,row=0,sticky='nw')
        self.__btn_cmd_virtualui_level_setlevel = tk.Button(self.__frame_device_commands_for_virtualui_level,text='SetLevel',width=15,command=self.__cmd_setlevel_selected_device)
        self.__btn_cmd_virtualui_level_setlevel.bind('<Return>',enter_on_button(self.__cmd_setlevel_selected_device))
        self.__btn_cmd_virtualui_level_setlevel.grid(column=0,row=1,sticky='nw')
        self.__tb_cmd_virtualui_level_setlevel1 = tk.Text(self.__frame_device_commands_for_virtualui_level,height=1,width=20,wrap='none')
        self.__tb_cmd_virtualui_level_setlevel1.bind('<Tab>',focus_target_widget(self.__btn_cmd_virtualui_level_setlevel))
        self.__tb_cmd_virtualui_level_setlevel1.grid(column=1,row=1,sticky='nw')
        #SetVisible(list[int],bool)
        self.__lbl_device_commands_virtualui_level_setvisible1 = tk.Label(self.__frame_device_commands_for_virtualui_level,text='IDs(comma separated list of ints)')
        self.__lbl_device_commands_virtualui_level_setvisible1.grid(column=1,row=2,sticky='nw')
        self.__lbl_device_commands_virtualui_level_setvisible2 = tk.Label(self.__frame_device_commands_for_virtualui_level,text='True or False')
        self.__lbl_device_commands_virtualui_level_setvisible2.grid(column=2,row=2,sticky='nw')
        self.__btn_cmd_virtualui_level_setvisible = tk.Button(self.__frame_device_commands_for_virtualui_level,text='SetVisible',width=15,command=self.__cmd_setvisible_selected_device)
        self.__btn_cmd_virtualui_level_setvisible.bind('<Return>',enter_on_button(self.__cmd_setvisible_selected_device))
        self.__btn_cmd_virtualui_level_setvisible.grid(column=0,row=3,sticky='nw')
        self.__tb_cmd_virtualui_level_setvisible1 = tk.Text(self.__frame_device_commands_for_virtualui_level,height=1,width=20,wrap='none')
        self.__tb_cmd_virtualui_level_setvisible1.bind('<Tab>',focus_next_widget)
        self.__tb_cmd_virtualui_level_setvisible1.grid(column=1,row=3,sticky='nw')
        self.__tb_cmd_virtualui_level_setvisible2 = tk.Text(self.__frame_device_commands_for_virtualui_level,height=1,width=20,wrap='none')
        self.__tb_cmd_virtualui_level_setvisible2.bind('<Tab>',focus_target_widget(self.__btn_cmd_virtualui_level_setvisible))
        self.__tb_cmd_virtualui_level_setvisible2.grid(column=2,row=3,sticky='nw')
        #SetRange(list[int],int,int,int)
        self.__lbl_device_commands_virtualui_level_setrange1 = tk.Label(self.__frame_device_commands_for_virtualui_level,text='IDs(comma separated list of ints)')
        self.__lbl_device_commands_virtualui_level_setrange1.grid(column=1,row=4,sticky='nw')
        self.__lbl_device_commands_virtualui_level_setrange2 = tk.Label(self.__frame_device_commands_for_virtualui_level,text='Min(int)')
        self.__lbl_device_commands_virtualui_level_setrange2.grid(column=2,row=4,sticky='nw')
        self.__lbl_device_commands_virtualui_level_setrange3 = tk.Label(self.__frame_device_commands_for_virtualui_level,text='Max(int)')
        self.__lbl_device_commands_virtualui_level_setrange3.grid(column=3,row=4,sticky='nw')
        self.__lbl_device_commands_virtualui_level_setrange4 = tk.Label(self.__frame_device_commands_for_virtualui_level,text='Step(int,optional)')
        self.__lbl_device_commands_virtualui_level_setrange4.grid(column=4,row=4,sticky='nw')
        self.__btn_cmd_virtualui_level_setrange = tk.Button(self.__frame_device_commands_for_virtualui_level,text='SetRange',width=15,command=self.__cmd_setrange_selected_device)
        self.__btn_cmd_virtualui_level_setrange.bind('<Return>',enter_on_button(self.__cmd_setrange_selected_device))
        self.__btn_cmd_virtualui_level_setrange.grid(column=0,row=5,sticky='nw')
        self.__tb_cmd_virtualui_level_setrange1 = tk.Text(self.__frame_device_commands_for_virtualui_level,height=1,width=20,wrap='none')
        self.__tb_cmd_virtualui_level_setrange1.bind('<Tab>',focus_next_widget)
        self.__tb_cmd_virtualui_level_setrange1.grid(column=1,row=5,sticky='nw')
        self.__tb_cmd_virtualui_level_setrange2 = tk.Text(self.__frame_device_commands_for_virtualui_level,height=1,width=20,wrap='none')
        self.__tb_cmd_virtualui_level_setrange2.bind('<Tab>',focus_next_widget)
        self.__tb_cmd_virtualui_level_setrange2.grid(column=2,row=5,sticky='nw')
        self.__tb_cmd_virtualui_level_setrange3 = tk.Text(self.__frame_device_commands_for_virtualui_level,height=1,width=20,wrap='none')
        self.__tb_cmd_virtualui_level_setrange3.bind('<Tab>',focus_next_widget)
        self.__tb_cmd_virtualui_level_setrange3.grid(column=3,row=5,sticky='nw')
        self.__tb_cmd_virtualui_level_setrange4 = tk.Text(self.__frame_device_commands_for_virtualui_level,height=1,width=20,wrap='none')
        self.__tb_cmd_virtualui_level_setrange4.bind('<Tab>',focus_target_widget(self.__btn_cmd_virtualui_level_setrange))
        self.__tb_cmd_virtualui_level_setrange4.grid(column=4,row=5,sticky='nw')
        #Inc()
        self.__lbl_device_commands_virtualui_level_inc1 = tk.Label(self.__frame_device_commands_for_virtualui_level,text='IDs(comma separated list of ints)')
        self.__lbl_device_commands_virtualui_level_inc1.grid(column=1,row=6,sticky='nw')
        self.__btn_cmd_virtualui_level_inc = tk.Button(self.__frame_device_commands_for_virtualui_level,text='Increment',width=15,command=self.__cmd_inc_selected_device)
        self.__btn_cmd_virtualui_level_inc.bind('<Return>',enter_on_button(self.__cmd_inc_selected_device))
        self.__btn_cmd_virtualui_level_inc.grid(column=0,row=7,sticky='nw')
        self.__tb_cmd_virtualui_level_inc1 = tk.Text(self.__frame_device_commands_for_virtualui_level,height=1,width=20,wrap='none')
        self.__tb_cmd_virtualui_level_inc1.bind('<Tab>',focus_target_widget(self.__btn_cmd_virtualui_level_inc))
        self.__tb_cmd_virtualui_level_inc1.grid(column=1,row=7,sticky='nw')
        #Dec()
        self.__lbl_device_commands_virtualui_level_dec1 = tk.Label(self.__frame_device_commands_for_virtualui_level,text='IDs(comma separated list of ints)')
        self.__lbl_device_commands_virtualui_level_dec1.grid(column=1,row=8,sticky='nw')
        self.__btn_cmd_virtualui_level_dec = tk.Button(self.__frame_device_commands_for_virtualui_level,text='Decrement',width=15,command=self.__cmd_dec_selected_device)
        self.__btn_cmd_virtualui_level_dec.bind('<Return>',enter_on_button(self.__cmd_dec_selected_device))
        self.__btn_cmd_virtualui_level_dec.grid(column=0,row=9,sticky='nw')
        self.__tb_cmd_virtualui_level_dec1 = tk.Text(self.__frame_device_commands_for_virtualui_level,height=1,width=20,wrap='none')
        self.__tb_cmd_virtualui_level_dec1.bind('<Tab>',focus_target_widget(self.__btn_cmd_virtualui_level_dec))
        self.__tb_cmd_virtualui_level_dec1.grid(column=1,row=9,sticky='nw')


        self.__frame_device_commands_for_virtualui_slider = tk.Frame(self.__frame_device_virtualui)
        self.__frame_device_commands_for_virtualui_slider.grid(column=0,row=5,sticky='nw')
        #setfill(list[int],bool)
        self.__lbl_device_commands_virtualui_slider_setfill1 = tk.Label(self.__frame_device_commands_for_virtualui_slider,text='IDs(comma separated list of ints)')
        self.__lbl_device_commands_virtualui_slider_setfill1.grid(column=1,row=0,sticky='nw')
        self.__lbl_device_commands_virtualui_slider_setfill2 = tk.Label(self.__frame_device_commands_for_virtualui_slider,text='Value(int)')
        self.__lbl_device_commands_virtualui_slider_setfill2.grid(column=2,row=0,sticky='nw')
        self.__btn_cmd_virtualui_slider_setfill = tk.Button(self.__frame_device_commands_for_virtualui_slider,text='Setfill',width=15,command=self.__cmd_setfill_selected_device)
        self.__btn_cmd_virtualui_slider_setfill.bind('<Return>',enter_on_button(self.__cmd_setfill_selected_device))
        self.__btn_cmd_virtualui_slider_setfill.grid(column=0,row=1,sticky='nw')
        self.__tb_cmd_virtualui_slider_setfill1 = tk.Text(self.__frame_device_commands_for_virtualui_slider,height=1,width=20,wrap='none')
        self.__tb_cmd_virtualui_slider_setfill1.bind('<Tab>',focus_next_widget)
        self.__tb_cmd_virtualui_slider_setfill1.grid(column=1,row=1,sticky='nw')
        self.__tb_cmd_virtualui_slider_setfill2 = tk.Text(self.__frame_device_commands_for_virtualui_slider,height=1,width=20,wrap='none')
        self.__tb_cmd_virtualui_slider_setfill2.bind('<Tab>',focus_target_widget(self.__btn_cmd_virtualui_slider_setfill))
        self.__tb_cmd_virtualui_slider_setfill2.grid(column=2,row=1,sticky='nw')
        #SetVisible(list[int],bool)
        self.__lbl_device_commands_virtualui_slider_setvisible1 = tk.Label(self.__frame_device_commands_for_virtualui_slider,text='IDs(comma separated list of ints)')
        self.__lbl_device_commands_virtualui_slider_setvisible1.grid(column=1,row=2,sticky='nw')
        self.__lbl_device_commands_virtualui_slider_setvisible2 = tk.Label(self.__frame_device_commands_for_virtualui_slider,text='True or False')
        self.__lbl_device_commands_virtualui_slider_setvisible2.grid(column=2,row=2,sticky='nw')
        self.__btn_cmd_virtualui_slider_setvisible = tk.Button(self.__frame_device_commands_for_virtualui_slider,text='SetVisible',width=15,command=self.__cmd_setvisible_selected_device)
        self.__btn_cmd_virtualui_slider_setvisible.bind('<Return>',enter_on_button(self.__cmd_setvisible_selected_device))
        self.__btn_cmd_virtualui_slider_setvisible.grid(column=0,row=3,sticky='nw')
        self.__tb_cmd_virtualui_slider_setvisible1 = tk.Text(self.__frame_device_commands_for_virtualui_slider,height=1,width=20,wrap='none')
        self.__tb_cmd_virtualui_slider_setvisible1.bind('<Tab>',focus_next_widget)
        self.__tb_cmd_virtualui_slider_setvisible1.grid(column=1,row=3,sticky='nw')
        self.__tb_cmd_virtualui_slider_setvisible2 = tk.Text(self.__frame_device_commands_for_virtualui_slider,height=1,width=20,wrap='none')
        self.__tb_cmd_virtualui_slider_setvisible2.bind('<Tab>',focus_target_widget(self.__btn_cmd_virtualui_slider_setvisible))
        self.__tb_cmd_virtualui_slider_setvisible2.grid(column=2,row=3,sticky='nw')
        #SetEnable(list[int],bool)
        self.__lbl_device_commands_virtualui_slider_setenable1 = tk.Label(self.__frame_device_commands_for_virtualui_slider,text='IDs(comma separated list of ints)')
        self.__lbl_device_commands_virtualui_slider_setenable1.grid(column=1,row=4,sticky='nw')
        self.__lbl_device_commands_virtualui_slider_setenable2 = tk.Label(self.__frame_device_commands_for_virtualui_slider,text='True or False')
        self.__lbl_device_commands_virtualui_slider_setenable2.grid(column=2,row=4,sticky='nw')
        self.__btn_cmd_virtualui_slider_setenable = tk.Button(self.__frame_device_commands_for_virtualui_slider,text='SetEnable',width=15,command=self.__cmd_setenable_selected_device)
        self.__btn_cmd_virtualui_slider_setenable.bind('<Return>',enter_on_button(self.__cmd_setenable_selected_device))
        self.__btn_cmd_virtualui_slider_setenable.grid(column=0,row=5,sticky='nw')
        self.__tb_cmd_virtualui_slider_setenable1 = tk.Text(self.__frame_device_commands_for_virtualui_slider,height=1,width=20,wrap='none')
        self.__tb_cmd_virtualui_slider_setenable1.bind('<Tab>',focus_next_widget)
        self.__tb_cmd_virtualui_slider_setenable1.grid(column=1,row=5,sticky='nw')
        self.__tb_cmd_virtualui_slider_setenable2 = tk.Text(self.__frame_device_commands_for_virtualui_slider,height=1,width=20,wrap='none')
        self.__tb_cmd_virtualui_slider_setenable2.bind('<Tab>',focus_target_widget(self.__btn_cmd_virtualui_slider_setenable))
        self.__tb_cmd_virtualui_slider_setenable2.grid(column=2,row=5,sticky='nw')
        #SetRange(list[int],int,int,int)
        self.__lbl_device_commands_virtualui_slider_setrange1 = tk.Label(self.__frame_device_commands_for_virtualui_slider,text='IDs(comma separated list of ints)')
        self.__lbl_device_commands_virtualui_slider_setrange1.grid(column=1,row=6,sticky='nw')
        self.__lbl_device_commands_virtualui_slider_setrange2 = tk.Label(self.__frame_device_commands_for_virtualui_slider,text='Min(int)')
        self.__lbl_device_commands_virtualui_slider_setrange2.grid(column=2,row=6,sticky='nw')
        self.__lbl_device_commands_virtualui_slider_setrange3 = tk.Label(self.__frame_device_commands_for_virtualui_slider,text='Max(int)')
        self.__lbl_device_commands_virtualui_slider_setrange3.grid(column=3,row=6,sticky='nw')
        self.__lbl_device_commands_virtualui_slider_setrange4 = tk.Label(self.__frame_device_commands_for_virtualui_slider,text='Step(int,optional)')
        self.__lbl_device_commands_virtualui_slider_setrange4.grid(column=4,row=6,sticky='nw')
        self.__btn_cmd_virtualui_slider_setrange = tk.Button(self.__frame_device_commands_for_virtualui_slider,text='SetRange',width=15,command=self.__cmd_setrange_selected_device)
        self.__btn_cmd_virtualui_slider_setrange.bind('<Return>',enter_on_button(self.__cmd_setrange_selected_device))
        self.__btn_cmd_virtualui_slider_setrange.grid(column=0,row=7,sticky='nw')
        self.__tb_cmd_virtualui_slider_setrange1 = tk.Text(self.__frame_device_commands_for_virtualui_slider,height=1,width=20,wrap='none')
        self.__tb_cmd_virtualui_slider_setrange1.bind('<Tab>',focus_next_widget)
        self.__tb_cmd_virtualui_slider_setrange1.grid(column=1,row=7,sticky='nw')
        self.__tb_cmd_virtualui_slider_setrange2 = tk.Text(self.__frame_device_commands_for_virtualui_slider,height=1,width=20,wrap='none')
        self.__tb_cmd_virtualui_slider_setrange2.bind('<Tab>',focus_next_widget)
        self.__tb_cmd_virtualui_slider_setrange2.grid(column=2,row=7,sticky='nw')
        self.__tb_cmd_virtualui_slider_setrange3 = tk.Text(self.__frame_device_commands_for_virtualui_slider,height=1,width=20,wrap='none')
        self.__tb_cmd_virtualui_slider_setrange3.bind('<Tab>',focus_next_widget)
        self.__tb_cmd_virtualui_slider_setrange3.grid(column=3,row=7,sticky='nw')
        self.__tb_cmd_virtualui_slider_setrange4 = tk.Text(self.__frame_device_commands_for_virtualui_slider,height=1,width=20,wrap='none')
        self.__tb_cmd_virtualui_slider_setrange4.bind('<Tab>',focus_target_widget(self.__btn_cmd_virtualui_slider_setrange))
        self.__tb_cmd_virtualui_slider_setrange4.grid(column=4,row=7,sticky='nw')
        #Emulate(int,str)
        self.__lbl_device_commands_virtualui_slider_emulate1 = tk.Label(self.__frame_device_commands_for_virtualui_slider,text='ID(int)')
        self.__lbl_device_commands_virtualui_slider_emulate1.grid(column=1,row=10,sticky='nw')
        self.__lbl_device_commands_virtualui_slider_emulate2 = tk.Label(self.__frame_device_commands_for_virtualui_slider,text='Event Type\n(Pressed,Released,Changed)')
        self.__lbl_device_commands_virtualui_slider_emulate2.grid(column=2,row=10,sticky='nw')
        self.__lbl_device_commands_virtualui_slider_emulate3 = tk.Label(self.__frame_device_commands_for_virtualui_slider,text='Value(int)')
        self.__lbl_device_commands_virtualui_slider_emulate3.grid(column=3,row=10,sticky='nw')
        self.__btn_cmd_virtualui_slider_emulate = tk.Button(self.__frame_device_commands_for_virtualui_slider,text='Emulate',width=15,command=self.__cmd_emulate_selected_device)
        self.__btn_cmd_virtualui_slider_emulate.bind('<Return>',enter_on_button(self.__cmd_emulate_selected_device))
        self.__btn_cmd_virtualui_slider_emulate.grid(column=0,row=11,sticky='nw')
        self.__tb_cmd_virtualui_slider_emulate1 = tk.Text(self.__frame_device_commands_for_virtualui_slider,height=1,width=20,wrap='none')
        self.__tb_cmd_virtualui_slider_emulate1.bind('<Tab>',focus_next_widget)
        self.__tb_cmd_virtualui_slider_emulate1.grid(column=1,row=11,sticky='nw')
        self.__tb_cmd_virtualui_slider_emulate2 = tk.Text(self.__frame_device_commands_for_virtualui_slider,height=1,width=20,wrap='none')
        self.__tb_cmd_virtualui_slider_emulate2.bind('<Tab>',focus_next_widget)
        self.__tb_cmd_virtualui_slider_emulate2.grid(column=2,row=11,sticky='nw')
        self.__tb_cmd_virtualui_slider_emulate3 = tk.Text(self.__frame_device_commands_for_virtualui_slider,height=1,width=20,wrap='none')
        self.__tb_cmd_virtualui_slider_emulate3.bind('<Tab>',focus_target_widget(self.__btn_cmd_virtualui_slider_emulate))
        self.__tb_cmd_virtualui_slider_emulate3.grid(column=3,row=11,sticky='nw')



        self.__device_commands_frames = {
            'Circuit Breaker':self.__frame_device_commands_for_circuit_breaker,
            'Contact':self.__frame_device_commands_for_contact,
            'Digital Input':self.__frame_device_commands_for_digital_input,
            'Digital IO':self.__frame_device_commands_for_digital_io,
            'Flex IO':self.__frame_device_commands_for_flex_io,
            'IR':self.__frame_device_commands_for_ir,
            'Serial':self.__frame_device_commands_for_modules,
            'SerialOverEthernet':self.__frame_device_commands_for_modules,
            'Ethernet':self.__frame_device_commands_for_modules,
            'Dante':self.__frame_device_commands_for_modules,
            'SSH':self.__frame_device_commands_for_modules,
            'SPI':self.__frame_device_commands_for_modules,
            'PoE':self.__frame_device_commands_for_poe,
            'Relay':self.__frame_device_commands_for_relay,
            'SW Power':self.__frame_device_commands_for_sw_power,
            'SWAC Receptacle':self.__frame_device_commands_for_swac_receptacle,
            'Tally':self.__frame_device_commands_for_tally,
            'Volume':self.__frame_device_commands_for_volume,
            'Processor':self.__frame_device_commands_for_processor,
            'SPDevice':self.__frame_device_commands_for_spdevice,
            'eBUSDevice':self.__frame_device_commands_for_ebusdevice,
            'UI':self.__frame_device_commands_for_ui,
            'VirtualUI':self.__frame_device_virtualui,
            'Print':self.__frame_device_print}
        self.__device_virtualui_mode_frames = {
            'Navigation':self.__frame_device_commands_for_virtualui_navigation,
            'Button':self.__frame_device_commands_for_virtualui_button,
            'Knob':self.__frame_device_commands_for_virtualui_knob,
            'Label':self.__frame_device_commands_for_virtualui_label,
            'Level':self.__frame_device_commands_for_virtualui_level,
            'Slider':self.__frame_device_commands_for_virtualui_slider}

        self.__btn_colors = None
        self.__initialize_hide()
        self.Hide()
        self.Show()

    #menu methods

    def open_connect_window(self):
        if self.__reading_devices_busy == True:return

        window2 = tk.Tk()
        window2.title(' Connect To System ')
        window2.geometry('250x75')

        lbl_instructions = tk.Label(window2,text = ' Enter the IP address of the Extron Controller:  ')
        lbl_instructions.grid(column=0,row=0)

        def clear_tb_ip():
            self.ip_address = tb_ip.get(1.0,'end')
            self.ip_address = self.ip_address.strip()
            window2.destroy()
            self.processor_communication.system_connection_start()
        def clear_tb_enter(event):
            clear_tb_ip()
        def focus_next_widget(event):
            event.widget.tk_focusNext().focus()
            return("break")
        tb_ip = tk.Text(window2,height=1,width=20)
        tb_ip.grid(column=0,row=2)
        tb_ip.bind('<Return>',clear_tb_enter)
        tb_ip.bind('<Tab>',focus_next_widget)
        tb_ip.insert(tk.END,self.ip_address)
        tb_ip.update()
        btn_submit = tk.Button(window2,text='Submit',width=10,height=1,command=clear_tb_ip)
        btn_submit.bind('<Return>',clear_tb_enter)
        btn_submit.grid(column=0,row=4)
        #apply focus
        window2.wm_deiconify()
        tb_ip.focus_set()
    def disconnect_from_system(self):
        self.processor_communication.system_connection_stop()
    def save_current_log(self):
        f = filedialog.asksaveasfile(mode='w', defaultextension="txt")
        if f is None: # asksaveasfile return `None` if dialog closed with "cancel".
            return
        text2save = self.vars.ui_view1.GetCurrentLog()
        f.write(text2save)
        f.close()
    def save_current_status(self):
        f = filedialog.asksaveasfile(mode='w', defaultextension="txt")
        if f is None: # asksaveasfile return `None` if dialog closed with "cancel".
            return
        text2save = self.vars.ui_view1.GetCurrentStatus()
        f.write(text2save)
        f.close()
    def save_all_logs(self):
        f = filedialog.asksaveasfile(mode='w', defaultextension="txt")
        if f is None: # asksaveasfile return `None` if dialog closed with "cancel".
            return
        text2save = self.vars.ui_view1.GetAllLogs()
        f.write(text2save)
        f.close()
    def save_all_status(self):
        f = filedialog.asksaveasfile(mode='w', defaultextension="txt")
        if f is None: # asksaveasfile return `None` if dialog closed with "cancel".
            return
        text2save = self.vars.ui_view1.GetAllStatus()
        f.write(text2save)
        f.close()


    #class methods
    def __initialize_hide(self):
        self.__hide_device_commands()
        self.Hide(self.__frame_header_body_nav)
        self.Hide(self.__frame_body_log)
        self.Hide(self.__frame_controller_module)
        self.Hide(self.__frame_controller_module_status_view)
        self.Hide(self.__frame_controller_module_command_view)
        self.Hide(self.__frame_print_to_trace)
        self.Hide(self.__frame_device_reinit)
        #self.__btn_body_view_module['bg'] = '#f0f0f0'
        self.__toggle_button(self.__btn_body_view_module,0)
        #self.__btn_body_view_log['bg'] = '#f0f0f0'
        self.__toggle_button(self.__btn_body_view_log,0)
        #self.__btn_tb_view_status_view['bg'] = '#f0f0f0'
        self.__toggle_button(self.__btn_tb_view_status_view,0)
        #self.__btn_tb_view_command_view['bg'] = '#f0f0f0'
        self.__toggle_button(self.__btn_tb_view_command_view,0)

    def refresh(self,obj):
        obj.destroy()
        obj.__init__()

    def __body_log_view_enable(self):
        self.__debug_view_mode = 'Log'

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

        self.Hide(self.__frame_controller_module)
        self.Show(self.__frame_body_log)
        #self.__btn_body_view_module['bg'] = '#f0f0f0'
        self.__toggle_button(self.__btn_body_view_module,0)
        #self.__btn_body_view_log['bg'] = 'sky blue'
        self.__toggle_button(self.__btn_body_view_log,1)
    def __body_module_view_enable(self):
        self.__debug_view_mode = 'Module'

        #apply window scaling to frames
        self.__frame.rowconfigure(1, weight=0)
        self.__frame.rowconfigure(2, weight=0)
        self.__frame.columnconfigure(0, weight=0)

        self.Hide(self.__frame_body_log)
        self.Show(self.__frame_controller_module)
        #self.__btn_body_view_log['bg'] = '#f0f0f0'
        self.__toggle_button(self.__btn_body_view_log,0)
        #self.__btn_body_view_module['bg'] = 'sky blue'
        self.__toggle_button(self.__btn_body_view_module,1)
        if self.__module_view_mode == 'command':
            self.__controller_command_view_enable()
        else:
            self.__controller_status_view_enable()

    def __controller_command_view_enable(self):
        self.__module_view_mode = 'command'
        self.__frame.rowconfigure(2, weight=0)
        self.__frame.columnconfigure(0, weight=0)

        self.Hide(self.__frame_controller_module_status_view)
        self.Show(self.__frame_controller_module_command_view)
        #self.__btn_tb_view_status_view['bg'] = '#f0f0f0'
        self.__toggle_button(self.__btn_tb_view_status_view,0)
        #self.__btn_tb_view_command_view['bg'] = 'sky blue'
        self.__toggle_button(self.__btn_tb_view_command_view,1)
    def __controller_status_view_enable(self):
        self.__module_view_mode = 'status'
        self.__frame.rowconfigure(2, weight=1)
        self.__frame.columnconfigure(0, weight=1)

        self.__frame_controller_module.rowconfigure(0, weight=1)
        self.__frame_controller_module.columnconfigure(1, weight=1)
        self.__frame_controller_module_right.rowconfigure(1, weight=1)
        self.__frame_controller_module_right.columnconfigure(0, weight=1)
        self.__frame_controller_module_status_view.rowconfigure(1, weight=1)
        self.__frame_controller_module_status_view.columnconfigure(1, weight=1)
        self.__frame_status.rowconfigure(0, weight=1)
        self.__frame_status.columnconfigure(0, weight=1)
        self.__tb_status.rowconfigure(0, weight=1)
        self.__tb_status.columnconfigure(0, weight=1)

        self.Hide(self.__frame_controller_module_command_view)
        self.Show(self.__frame_controller_module_status_view)
        #self.__btn_tb_view_command_view['bg'] = '#f0f0f0'
        self.__toggle_button(self.__btn_tb_view_command_view,0)
        #self.__btn_tb_view_status_view['bg'] = 'sky blue'
        self.__toggle_button(self.__btn_tb_view_status_view,1)


    def __selected_device_changed(self):
        def e(*args):
            selected_device = self.__selected_device.get()
            try:
                self.__selected_module = self.__device_list.index(selected_device)
            except:
                self.__selected_module = None
                return
            self.__set_device_communication_details(self.__selected_module)
            self.__show_device_status(self.__selected_module)
            self.__show_device_commands(self.__selected_module)
        return e

    def __cmd_reinitialize_selected_module(self):
        if self.__selected_module is not None:
            device_id = self.__get_device_log_id(self.__selected_module)
            cmd = '~Command~:{}:Reinit()'.format(device_id)
            self.processor_communication.SendToSystem(cmd)
    def __cmd_update_selected_module(self):
        if self.__selected_module is not None:
            device_id = self.__get_device_log_id(self.__selected_module)
            cmd_dict = {}
            cmd_dict['command'] = self.__tb_update_command1.get('1.0',tk.END)
            cmd_dict['command'] = cmd_dict['command'].strip()
            cmd_dict['qualifier'] = self.__tb_update_command2.get('1.0',tk.END)
            cmd_dict['qualifier'] = cmd_dict['qualifier'].strip()
            try:
                cmd_dict['qualifier'] = json.loads(cmd_dict['qualifier'])
            except:
                cmd_dict['qualifier'] = None
            if cmd_dict['command'] == '':
                return
            cmd_dict_str = json.dumps(cmd_dict)
            cmd = '~Command~:{}:Update({})'.format(device_id,cmd_dict_str)
            self.processor_communication.SendToSystem(cmd)
    def __cmd_set_selected_module(self):
        if self.__selected_module is not None:
            device_id = self.__get_device_log_id(self.__selected_module)
            cmd_dict = {}
            cmd_dict['command'] = self.__tb_set_command1.get('1.0',tk.END)
            cmd_dict['command'] = cmd_dict['command'].strip()
            cmd_dict['value'] = self.__tb_set_command2.get('1.0',tk.END)
            cmd_dict['value'] = cmd_dict['value'].strip()
            cmd_dict['valuetype'] = self.__sv_commands_module_set_value_type.get()
            cmd_dict['qualifier'] = self.__tb_set_command3.get('1.0',tk.END)
            cmd_dict['qualifier'] = cmd_dict['qualifier'].strip()
            try:
                cmd_dict['qualifier'] = json.loads(cmd_dict['qualifier'])
            except:
                cmd_dict['qualifier'] = None
            if cmd_dict['command'] == '' or cmd_dict['value'] == '':
                return
            cmd_dict_str = json.dumps(cmd_dict)
            cmd = '~Command~:{}:Set({})'.format(device_id,cmd_dict_str)
            self.processor_communication.SendToSystem(cmd)
    def __cmd_writestatus_selected_module(self):
        if self.__selected_module is not None:
            device_id = self.__get_device_log_id(self.__selected_module)
            cmd_dict = {}
            cmd_dict['command'] = self.__tb_writestatus_command1.get('1.0',tk.END)
            cmd_dict['command'] = cmd_dict['command'].strip()
            cmd_dict['value'] = self.__tb_writestatus_command2.get('1.0',tk.END)
            cmd_dict['value'] = cmd_dict['value'].strip()
            cmd_dict['valuetype'] = self.__sv_commands_module_writestatus_value_type.get()
            cmd_dict['qualifier'] = self.__tb_writestatus_command3.get('1.0',tk.END)
            cmd_dict['qualifier'] = cmd_dict['qualifier'].strip()
            try:
                cmd_dict['qualifier'] = json.loads(cmd_dict['qualifier'])
            except:
                cmd_dict['qualifier'] = None
            if cmd_dict['command'] == '' or cmd_dict['value'] == '':
                return
            cmd_dict_str = json.dumps(cmd_dict)
            cmd = '~Command~:{}:WriteStatus({})'.format(device_id,cmd_dict_str)
            self.processor_communication.SendToSystem(cmd)
    def __cmd_passthrough_selected_module(self):
        if self.__selected_module is not None:
            device_id = self.__get_device_log_id(self.__selected_module)
            txt = self.__tb_passthrough_command.get('1.0',tk.END)
            txt = txt.strip()
            txt = self.__eval_string(txt)
            cmd = '~Command~:{}:Passthrough("{}")'.format(device_id,txt)
            self.processor_communication.SendToSystem(cmd)
    def __cmd_initialize_selected_device(self):
        if self.__selected_module is not None:
            device_id = self.__get_device_log_id(self.__selected_module)
            cmd_dict = {}
            device_type = self.device_info[device_id]['type']
            tbs = {'Flex IO':[self.__tb_cmd_flex_io_initialize1,self.__tb_cmd_flex_io_initialize2,self.__tb_cmd_flex_io_initialize3,self.__tb_cmd_flex_io_initialize4],
                    'Digital IO':[self.__tb_cmd_digital_io_initialize1,self.__tb_cmd_digital_io_initialize2],
                    'Digital Input':[self.__tb_cmd_digital_input_initialize1],
                    'IR':[self.__tb_cmd_ir_initialize1]}
            if device_type not in tbs:
                return
            cmd_dict['value1'] = tbs[device_type][0].get('1.0',tk.END)
            cmd_dict['value1'] = cmd_dict['value1'].strip()
            if device_type in ['Digital IO','Flex IO']:
                cmd_dict['value2'] = tbs[device_type][1].get('1.0',tk.END)
                cmd_dict['value2'] = cmd_dict['value2'].strip()
                if device_type == 'Flex IO':
                    cmd_dict['value3'] = tbs[device_type][2].get('1.0',tk.END)
                    cmd_dict['value3'] = cmd_dict['value3'].strip()
                    cmd_dict['value4'] = tbs[device_type][3].get('1.0',tk.END)
                    cmd_dict['value4'] = cmd_dict['value4'].strip()
            for key in cmd_dict:
                if len(cmd_dict[key]) < 1:
                    cmd_dict[key] = None
                elif cmd_dict[key] == 'True':
                    cmd_dict[key] = True
                elif cmd_dict[key] == 'False':
                    cmd_dict[key] = False
            cmd_dict_str = json.dumps(cmd_dict)
            cmd = '~Command~:{}:Initialize({})'.format(device_id,cmd_dict_str)
            self.processor_communication.SendToSystem(cmd)
    def __cmd_pulse_selected_device(self):
        if self.__selected_module is not None:
            device_id = self.__get_device_log_id(self.__selected_module)
            cmd_dict = {}
            device_type = self.device_info[device_id]['type']
            tbs = {'Relay':[self.__tb_cmd_relay_pulse1],
                    'Tally':[self.__tb_cmd_tally_pulse1],
                    'Flex IO':[self.__tb_cmd_flex_io_pulse1],
                    'SW Power':[self.__tb_cmd_sw_power_pulse1],
                    'Digital IO':[self.__tb_cmd_digital_io_pulse1]}
            if device_type not in tbs:
                return
            cmd_dict['value1'] = tbs[device_type][0].get('1.0',tk.END)
            cmd_dict['value1'] = cmd_dict['value1'].strip()
            if cmd_dict['value1'] == '':
                return
            cmd_dict_str = json.dumps(cmd_dict)
            cmd = '~Command~:{}:Pulse({})'.format(device_id,cmd_dict_str)
            self.processor_communication.SendToSystem(cmd)
    def __cmd_state_selected_device(self):
        if self.__selected_module is not None:
            device_id = self.__get_device_log_id(self.__selected_module)
            cmd_dict = {}
            device_type = self.device_info[device_id]['type']
            tbs = {'PoE':[self.__tb_cmd_poe_state1],
                    'Relay':[self.__tb_cmd_relay_state1],
                    'Tally':[self.__tb_cmd_tally_state1],
                    'Flex IO':[self.__tb_cmd_flex_io_state1],
                    'SW Power':[self.__tb_cmd_sw_power_state1],
                    'Digital IO':[self.__tb_cmd_digital_io_state1],
                    'SWAC Receptacle':[self.__tb_cmd_swac_receptacle_state1]}
            if device_type not in tbs:
                return
            cmd_dict['value1'] = tbs[device_type][0].get('1.0',tk.END)
            cmd_dict['value1'] = cmd_dict['value1'].strip()
            if cmd_dict['value1'] == '':
                return
            cmd_dict_str = json.dumps(cmd_dict)
            cmd = '~Command~:{}:State({})'.format(device_id,cmd_dict_str)
            self.processor_communication.SendToSystem(cmd)
    def __cmd_toggle_selected_device(self):
        device_id = self.__get_device_log_id(self.__selected_module)
        cmd = '~Command~:{}:Toggle()'.format(device_id)
        self.processor_communication.SendToSystem(cmd)
    def __cmd_level_selected_device(self):
        if self.__selected_module is not None:
            device_id = self.__get_device_log_id(self.__selected_module)
            cmd_dict = {}
            cmd_dict['value1'] = self.__tb_cmd_volume_level1.get('1.0',tk.END)
            cmd_dict['value1'] = cmd_dict['value1'].strip()
            if cmd_dict['value1'] == '':
                return
            cmd_dict_str = json.dumps(cmd_dict)
            cmd = '~Command~:{}:Level({})'.format(device_id,cmd_dict_str)
            self.processor_communication.SendToSystem(cmd)
    def __cmd_mute_selected_device(self):
        if self.__selected_module is not None:
            device_id = self.__get_device_log_id(self.__selected_module)
            cmd_dict = {}
            cmd_dict['value1'] = self.__tb_cmd_volume_mute1.get('1.0',tk.END)
            cmd_dict['value1'] = cmd_dict['value1'].strip()
            if cmd_dict['value1'] == '':
                return
            cmd_dict_str = json.dumps(cmd_dict)
            cmd = '~Command~:{}:Mute({})'.format(device_id,cmd_dict_str)
            self.processor_communication.SendToSystem(cmd)
    def __cmd_range_selected_device(self):
        if self.__selected_module is not None:
            device_id = self.__get_device_log_id(self.__selected_module)
            cmd_dict = {}
            cmd_dict['value1'] = self.__tb_cmd_volume_range1.get('1.0',tk.END)
            cmd_dict['value1'] = cmd_dict['value1'].strip()
            cmd_dict['value2'] = self.__tb_cmd_volume_range2.get('1.0',tk.END)
            cmd_dict['value2'] = cmd_dict['value2'].strip()
            if cmd_dict['value1'] == '' or cmd_dict['value2'] == '':
                return
            cmd_dict_str = json.dumps(cmd_dict)
            cmd = '~Command~:{}:Range({})'.format(device_id,cmd_dict_str)
            self.processor_communication.SendToSystem(cmd)
    def __cmd_softstart_selected_device(self):
        if self.__selected_module is not None:
            device_id = self.__get_device_log_id(self.__selected_module)
            cmd_dict = {}
            cmd_dict['value1'] = self.__tb_cmd_volume_softstart1.get('1.0',tk.END)
            cmd_dict['value1'] = cmd_dict['value1'].strip()
            if cmd_dict['command'] == '':
                return
            cmd_dict_str = json.dumps(cmd_dict)
            cmd = '~Command~:{}:SoftStart({})'.format(device_id,cmd_dict_str)
            self.processor_communication.SendToSystem(cmd)
    def __cmd_playcontinuous_selected_device(self):
        if self.__selected_module is not None:
            device_id = self.__get_device_log_id(self.__selected_module)
            cmd_dict = {}
            cmd_dict['value1'] = self.__tb_cmd_ir_playcontinuous1.get('1.0',tk.END)
            cmd_dict['value1'] = cmd_dict['value1'].strip()
            if cmd_dict['value1'] == '':
                return
            cmd_dict_str = json.dumps(cmd_dict)
            cmd = '~Command~:{}:PlayContinuous({})'.format(device_id,cmd_dict_str)
            self.processor_communication.SendToSystem(cmd)
    def __cmd_playcount_selected_device(self):
        if self.__selected_module is not None:
            device_id = self.__get_device_log_id(self.__selected_module)
            cmd_dict = {}
            cmd_dict['value1'] = self.__tb_cmd_ir_playcount1.get('1.0',tk.END)
            cmd_dict['value1'] = cmd_dict['value1'].strip()
            cmd_dict['value2'] = self.__tb_cmd_ir_playcount2.get('1.0',tk.END)
            cmd_dict['value2'] = cmd_dict['value2'].strip()
            if cmd_dict['value1'] == '' or cmd_dict['value2'] == '':
                return
            cmd_dict_str = json.dumps(cmd_dict)
            cmd = '~Command~:{}:PlayCount({})'.format(device_id,cmd_dict_str)
            self.processor_communication.SendToSystem(cmd)
    def __cmd_playtime_selected_device(self):
        if self.__selected_module is not None:
            device_id = self.__get_device_log_id(self.__selected_module)
            cmd_dict = {}
            cmd_dict['value1'] = self.__tb_cmd_ir_playtime1.get('1.0',tk.END)
            cmd_dict['value1'] = cmd_dict['value1'].strip()
            cmd_dict['value2'] = self.__tb_cmd_ir_playtime2.get('1.0',tk.END)
            cmd_dict['value2'] = cmd_dict['value2'].strip()
            if cmd_dict['value1'] == '' or cmd_dict['value2'] == '':
                return
            cmd_dict_str = json.dumps(cmd_dict)
            cmd = '~Command~:{}:PlayTime({})'.format(device_id,cmd_dict_str)
            self.processor_communication.SendToSystem(cmd)
    def __cmd_stop_selected_device(self):
        if self.__selected_module is not None:
            device_id = self.__get_device_log_id(self.__selected_module)
            cmd = '~Command~:{}:Stop()'.format(device_id)
            self.processor_communication.SendToSystem(cmd)
    def __cmd_reboot_selected_device(self):
        if self.__selected_module is not None:
            device_id = self.__get_device_log_id(self.__selected_module)
            cmd = '~Command~:{}:Reboot()'.format(device_id)
            self.processor_communication.SendToSystem(cmd)
    def __cmd_savepgmlog_selected_device(self):
        if self.__selected_module is not None:
            device_id = self.__get_device_log_id(self.__selected_module)
            cmd = '~Command~:{}:SaveProgramLog()'.format(device_id)
            self.processor_communication.SendToSystem(cmd)
    def __cmd_executivemode_selected_device(self):
        if self.__selected_module is not None:
            device_id = self.__get_device_log_id(self.__selected_module)
            cmd_dict = {}
            cmd_dict['value1'] = self.__tb_cmd_processor_executivemode1.get('1.0',tk.END)
            cmd_dict['value1'] = cmd_dict['value1'].strip()
            if cmd_dict['value1'] == '':
                return
            cmd_dict_str = json.dumps(cmd_dict)
            cmd = '~Command~:{}:ExecutiveMode({})'.format(device_id,cmd_dict_str)
            self.processor_communication.SendToSystem(cmd)
    def __cmd_showpage_selected_device(self):
        if self.__selected_module is not None:
            device_id = self.__get_device_log_id(self.__selected_module)
            cmd_dict = {}
            device_type = self.device_info[device_id]['type']
            tbs = {'UI':[self.__tb_cmd_ui_showpage1],
                    'VirtualUI':[self.__tb_cmd_virtualui_showpage1]}
            if device_type not in tbs:
                return
            cmd_dict['value1'] = tbs[device_type][0].get('1.0',tk.END)
            cmd_dict['value1'] = cmd_dict['value1'].strip()
            if cmd_dict['value1'] == '':
                return
            cmd_dict_str = json.dumps(cmd_dict)
            cmd = '~Command~:{}:ShowPage({})'.format(device_id,cmd_dict_str)
            self.processor_communication.SendToSystem(cmd)
    def __cmd_showpopup_selected_device(self):
        if self.__selected_module is not None:
            device_id = self.__get_device_log_id(self.__selected_module)
            cmd_dict = {}
            device_type = self.device_info[device_id]['type']
            tbs = {'UI':[self.__tb_cmd_ui_showpopup1,self.__tb_cmd_ui_showpopup2],
                    'VirtualUI':[self.__tb_cmd_virtualui_showpopup1,self.__tb_cmd_virtualui_showpopup2]}
            if device_type not in tbs:
                return
            cmd_dict['value1'] = tbs[device_type][0].get('1.0',tk.END)
            cmd_dict['value1'] = cmd_dict['value1'].strip()
            cmd_dict['value2'] = tbs[device_type][1].get('1.0',tk.END)
            cmd_dict['value2'] = cmd_dict['value2'].strip()
            if cmd_dict['value1'] == '':
                return
            if cmd_dict['value2'] == '':
                cmd_dict['value2'] = '0'
            cmd_dict_str = json.dumps(cmd_dict)
            cmd = '~Command~:{}:ShowPopup({})'.format(device_id,cmd_dict_str)
            self.processor_communication.SendToSystem(cmd)
    def __cmd_hidepopup_selected_device(self):
        if self.__selected_module is not None:
            device_id = self.__get_device_log_id(self.__selected_module)
            cmd_dict = {}
            device_type = self.device_info[device_id]['type']
            tbs = {'UI':[self.__tb_cmd_ui_hidepopup1],
                    'VirtualUI':[self.__tb_cmd_virtualui_hidepopup1]}
            if device_type not in tbs:
                return
            cmd_dict['value1'] = tbs[device_type][0].get('1.0',tk.END)
            cmd_dict['value1'] = cmd_dict['value1'].strip()
            if cmd_dict['value1'] == '':
                return
            cmd_dict_str = json.dumps(cmd_dict)
            cmd = '~Command~:{}:HidePopup({})'.format(device_id,cmd_dict_str)
            self.processor_communication.SendToSystem(cmd)
    def __cmd_hidepopupgroup_selected_device(self):
        if self.__selected_module is not None:
            device_id = self.__get_device_log_id(self.__selected_module)
            cmd_dict = {}
            device_type = self.device_info[device_id]['type']
            tbs = {'UI':[self.__tb_cmd_ui_hidepopupgroup1],
                    'VirtualUI':[self.__tb_cmd_virtualui_hidepopupgroup1]}
            if device_type not in tbs:
                return
            cmd_dict['value1'] = tbs[device_type][0].get('1.0',tk.END)
            cmd_dict['value1'] = cmd_dict['value1'].strip()
            if cmd_dict['value1'] == '':
                return
            cmd_dict_str = json.dumps(cmd_dict)
            cmd = '~Command~:{}:HidePopupGroup({})'.format(device_id,cmd_dict_str)
            self.processor_communication.SendToSystem(cmd)
    def __cmd_hideallpopups_selected_device(self):
        if self.__selected_module is not None:
            device_id = self.__get_device_log_id(self.__selected_module)
            cmd = '~Command~:{}:HideAllPopups()'.format(device_id)
            self.processor_communication.SendToSystem(cmd)
    def __cmd_wake_selected_device(self):
        if self.__selected_module is not None:
            device_id = self.__get_device_log_id(self.__selected_module)
            cmd = '~Command~:{}:Wake()'.format(device_id)
            self.processor_communication.SendToSystem(cmd)
    def __cmd_sleep_selected_device(self):
        if self.__selected_module is not None:
            device_id = self.__get_device_log_id(self.__selected_module)
            cmd = '~Command~:{}:Sleep()'.format(device_id)
            self.processor_communication.SendToSystem(cmd)
    def __cmd_setstate_selected_device(self):
        if self.__selected_module is not None:
            device_id = self.__get_device_log_id(self.__selected_module)
            cmd_dict = {}
            device_type = self.__selected_virtualui_mode
            tbs = {'Button':[self.__tb_cmd_virtualui_button_setstate1,self.__tb_cmd_virtualui_button_setstate2]}
            if device_type not in tbs:
                return
            cmd_dict['value1'] = tbs[device_type][0].get('1.0',tk.END)
            cmd_dict['value1'] = cmd_dict['value1'].strip()
            cmd_dict['value2'] = tbs[device_type][1].get('1.0',tk.END)
            cmd_dict['value2'] = cmd_dict['value2'].strip()
            if cmd_dict['value1'] == '' or cmd_dict['value2'] == '':
                return
            cmd_dict['value1'] = cmd_dict['value1'].split(',')
            cmd_dict_str = json.dumps(cmd_dict)
            cmd = '~Command~:{}:SetState({})'.format(device_id,cmd_dict_str)
            self.processor_communication.SendToSystem(cmd)
    def __cmd_settext_selected_device(self):
        if self.__selected_module is not None:
            device_id = self.__get_device_log_id(self.__selected_module)
            cmd_dict = {}
            device_type = self.__selected_virtualui_mode
            tbs = {'Button':[self.__tb_cmd_virtualui_button_settext1,self.__tb_cmd_virtualui_button_settext2],
                    'Label':[self.__tb_cmd_virtualui_label_settext1,self.__tb_cmd_virtualui_label_settext2]}
            if device_type not in tbs:
                return
            cmd_dict['value1'] = tbs[device_type][0].get('1.0',tk.END)
            cmd_dict['value1'] = cmd_dict['value1'].strip()
            cmd_dict['value2'] = tbs[device_type][1].get('1.0',tk.END)
            cmd_dict['value2'] = cmd_dict['value2'].strip()
            if cmd_dict['value1'] == '':
                return
            cmd_dict['value1'] = cmd_dict['value1'].split(',')
            cmd_dict_str = json.dumps(cmd_dict)
            cmd = '~Command~:{}:SetText({})'.format(device_id,cmd_dict_str)
            self.processor_communication.SendToSystem(cmd)
    def __cmd_setblinking_selected_device(self):
        if self.__selected_module is not None:
            device_id = self.__get_device_log_id(self.__selected_module)
            cmd_dict = {}
            device_type = self.__selected_virtualui_mode
            tbs = {'Button':[self.__tb_cmd_virtualui_button_setblinking1,self.__tb_cmd_virtualui_button_setblinking2,self.__tb_cmd_virtualui_button_setblinking3]}
            if device_type not in tbs:
                return
            cmd_dict['value1'] = tbs[device_type][0].get('1.0',tk.END)
            cmd_dict['value1'] = cmd_dict['value1'].strip()
            cmd_dict['value2'] = tbs[device_type][1].get('1.0',tk.END)
            cmd_dict['value2'] = cmd_dict['value2'].strip()
            cmd_dict['value3'] = tbs[device_type][2].get('1.0',tk.END)
            cmd_dict['value3'] = cmd_dict['value3'].strip()
            if cmd_dict['value1'] == '' or cmd_dict['value2'] == '' or cmd_dict['value3'] == '':
                return
            cmd_dict['value1'] = cmd_dict['value1'].split(',')
            cmd_dict['value3'] = cmd_dict['value3'].split(',')
            cmd_dict_str = json.dumps(cmd_dict)
            cmd = '~Command~:{}:SetBlinking({})'.format(device_id,cmd_dict_str)
            self.processor_communication.SendToSystem(cmd)
    def __cmd_emulate_selected_device(self):
        if self.__selected_module is not None:
            device_id = self.__get_device_log_id(self.__selected_module)
            cmd_dict = {}
            device_type = self.__selected_virtualui_mode
            tbs = {'Button':[self.__tb_cmd_virtualui_button_emulate1,self.__tb_cmd_virtualui_button_emulate2],
                    'Knob':[self.__tb_cmd_virtualui_knob_emulate1,self.__tb_cmd_virtualui_knob_emulate2],
                    'Slider':[self.__tb_cmd_virtualui_slider_emulate1,self.__tb_cmd_virtualui_slider_emulate2,self.__tb_cmd_virtualui_slider_emulate3]}
            if device_type not in tbs:
                return
            cmd_dict['value1'] =  tbs[device_type][0].get('1.0',tk.END)
            cmd_dict['value1'] = cmd_dict['value1'].strip()
            cmd_dict['value2'] = tbs[device_type][1].get('1.0',tk.END)
            cmd_dict['value2'] = cmd_dict['value2'].strip()
            if cmd_dict['value1'] == '' or cmd_dict['value2'] == '':
                return
            try:
                cmd_dict['value1'] = int(cmd_dict['value1'])
            except:
                return
            if device_type == 'Knob':
                try:
                    cmd_dict['value2'] = int(cmd_dict['value2'])
                except:
                    return
            if device_type == 'Slider':
                cmd_dict['value3'] = tbs[device_type][2].get('1.0',tk.END)
                cmd_dict['value3'] = cmd_dict['value3'].strip()
                if cmd_dict['value3'] == '':
                    cmd_dict['value3'] = 0
                try:
                    cmd_dict['value3'] = int(cmd_dict['value3'])
                except:
                    return
            else:
                cmd_dict['value3'] = 0
            cmd_dict_str = json.dumps(cmd_dict)
            cmd = '~Command~:{}:Emulate({})'.format(device_id,cmd_dict_str)
            self.processor_communication.SendToSystem(cmd)
    def __cmd_setlevel_selected_device(self):
        if self.__selected_module is not None:
            device_id = self.__get_device_log_id(self.__selected_module)
            cmd_dict = {}
            device_type = self.__selected_virtualui_mode
            tbs = {'Level':[self.__tb_cmd_virtualui_level_setlevel1,self.__tb_cmd_virtualui_level_setlevel2]}
            if device_type not in tbs:
                return
            cmd_dict['value1'] = tbs[device_type][0].get('1.0',tk.END)
            cmd_dict['value1'] = cmd_dict['value1'].strip()
            cmd_dict['value2'] = tbs[device_type][1].get('1.0',tk.END)
            cmd_dict['value2'] = cmd_dict['value2'].strip()
            if cmd_dict['value1'] == '' or cmd_dict['value2'] == '':
                return
            cmd_dict['value1'] = cmd_dict['value1'].split(',')
            cmd_dict_str = json.dumps(cmd_dict)
            cmd = '~Command~:{}:SetLevel({})'.format(device_id,cmd_dict_str)
            self.processor_communication.SendToSystem(cmd)
    def __cmd_setfill_selected_device(self):
        if self.__selected_module is not None:
            device_id = self.__get_device_log_id(self.__selected_module)
            cmd_dict = {}
            device_type = self.__selected_virtualui_mode
            tbs = {'Slider':[self.__tb_cmd_virtualui_slider_setfill1,self.__tb_cmd_virtualui_slider_setfill2]}
            if device_type not in tbs:
                return
            cmd_dict['value1'] = tbs[device_type][0].get('1.0',tk.END)
            cmd_dict['value1'] = cmd_dict['value1'].strip()
            cmd_dict['value2'] = tbs[device_type][1].get('1.0',tk.END)
            cmd_dict['value2'] = cmd_dict['value2'].strip()
            if cmd_dict['value1'] == '' or cmd_dict['value2'] == '':
                return
            cmd_dict['value1'] = cmd_dict['value1'].split(',')
            cmd_dict_str = json.dumps(cmd_dict)
            cmd = '~Command~:{}:SetFill({})'.format(device_id,cmd_dict_str)
            self.processor_communication.SendToSystem(cmd)
    def __cmd_setenable_selected_device(self):
        if self.__selected_module is not None:
            device_id = self.__get_device_log_id(self.__selected_module)
            cmd_dict = {}
            device_type = self.__selected_virtualui_mode
            tbs = {'Button':[self.__tb_cmd_virtualui_button_setenable1,self.__tb_cmd_virtualui_button_setenable2],
                'Slider':[self.__tb_cmd_virtualui_slider_setenable1,self.__tb_cmd_virtualui_slider_setenable2]}
            if device_type not in tbs:
                return
            cmd_dict['value1'] = tbs[device_type][0].get('1.0',tk.END)
            cmd_dict['value1'] = cmd_dict['value1'].strip()
            cmd_dict['value2'] = tbs[device_type][1].get('1.0',tk.END)
            cmd_dict['value2'] = cmd_dict['value2'].strip()
            if cmd_dict['value1'] == '' or cmd_dict['value2'] not in ['True','False']:
                return
            cmd_dict['value1'] = cmd_dict['value1'].split(',')
            cmd_dict_str = json.dumps(cmd_dict)
            cmd = '~Command~:{}:SetEnable({})'.format(device_id,cmd_dict_str)
            self.processor_communication.SendToSystem(cmd)
    def __cmd_setvisible_selected_device(self):
        if self.__selected_module is not None:
            device_id = self.__get_device_log_id(self.__selected_module)
            cmd_dict = {}
            device_type = self.__selected_virtualui_mode
            tbs = {'Button':[self.__tb_cmd_virtualui_button_setvisible1,self.__tb_cmd_virtualui_button_setvisible2],
                'Label':[self.__tb_cmd_virtualui_label_setvisible1,self.__tb_cmd_virtualui_label_setvisible2],
                'Level':[self.__tb_cmd_virtualui_level_setvisible1,self.__tb_cmd_virtualui_level_setvisible2],
                'Slider':[self.__tb_cmd_virtualui_slider_setvisible1,self.__tb_cmd_virtualui_slider_setvisible2]}
            if device_type not in tbs:
                return
            cmd_dict['value1'] = tbs[device_type][0].get('1.0',tk.END)
            cmd_dict['value1'] = cmd_dict['value1'].strip()
            cmd_dict['value2'] = tbs[device_type][1].get('1.0',tk.END)
            cmd_dict['value2'] = cmd_dict['value2'].strip()
            if cmd_dict['value1'] == '' or cmd_dict['value2'] not in ['True','False']:
                return
            cmd_dict['value1'] = cmd_dict['value1'].split(',')
            cmd_dict_str = json.dumps(cmd_dict)
            cmd = '~Command~:{}:SetVisible({})'.format(device_id,cmd_dict_str)
            self.processor_communication.SendToSystem(cmd)
    def __cmd_setrange_selected_device(self):
        if self.__selected_module is not None:
            device_id = self.__get_device_log_id(self.__selected_module)
            cmd_dict = {}
            device_type = self.__selected_virtualui_mode
            tbs = {'Level':[self.__tb_cmd_virtualui_level_setrange1,self.__tb_cmd_virtualui_level_setrange2,self.__tb_cmd_virtualui_level_setrange3,self.__tb_cmd_virtualui_level_setrange4],
                'Slider':[self.__tb_cmd_virtualui_slider_setrange1,self.__tb_cmd_virtualui_slider_setrange2,self.__tb_cmd_virtualui_slider_setrange3,self.__tb_cmd_virtualui_slider_setrange4]}
            if device_type not in tbs:
                return
            cmd_dict['value1'] = tbs[device_type][0].get('1.0',tk.END)
            cmd_dict['value1'] = cmd_dict['value1'].strip()
            cmd_dict['value2'] = tbs[device_type][1].get('1.0',tk.END)
            cmd_dict['value2'] = cmd_dict['value2'].strip()
            cmd_dict['value3'] = tbs[device_type][2].get('1.0',tk.END)
            cmd_dict['value3'] = cmd_dict['value3'].strip()
            cmd_dict['value4'] = tbs[device_type][3].get('1.0',tk.END)
            cmd_dict['value4'] = cmd_dict['value4'].strip()
            if cmd_dict['value1'] == '' or cmd_dict['value2'] == '' or cmd_dict['value3'] == '':
                return
            if cmd_dict['value4'] == '':
                cmd_dict['value4'] = '1'
            cmd_dict['value1'] = cmd_dict['value1'].split(',')
            cmd_dict_str = json.dumps(cmd_dict)
            cmd = '~Command~:{}:SetRange({})'.format(device_id,cmd_dict_str)
            self.processor_communication.SendToSystem(cmd)
    def __cmd_inc_selected_device(self):
        if self.__selected_module is not None:
            device_id = self.__get_device_log_id(self.__selected_module)
            cmd_dict = {}
            device_type = self.__selected_virtualui_mode
            tbs = {'Level':[self.__tb_cmd_virtualui_level_inc1]}
            if device_type not in tbs:
                return
            cmd_dict['value1'] = tbs[device_type][0].get('1.0',tk.END)
            cmd_dict['value1'] = cmd_dict['value1'].strip()
            if cmd_dict['value1'] == '':
                return
            cmd_dict['value1'] = cmd_dict['value1'].split(',')
            cmd_dict_str = json.dumps(cmd_dict)
            cmd = '~Command~:{}:Inc({})'.format(device_id,cmd_dict_str)
            self.processor_communication.SendToSystem(cmd)
    def __cmd_dec_selected_device(self):
        if self.__selected_module is not None:
            device_id = self.__get_device_log_id(self.__selected_module)
            cmd_dict = {}
            device_type = self.__selected_virtualui_mode
            tbs = {'Level':[self.__tb_cmd_virtualui_level_inc1]}
            if device_type not in tbs:
                return
            cmd_dict['value1'] = tbs[device_type][0].get('1.0',tk.END)
            cmd_dict['value1'] = cmd_dict['value1'].strip()
            if cmd_dict['value1'] == '':
                return
            cmd_dict['value1'] = cmd_dict['value1'].split(',')
            cmd_dict_str = json.dumps(cmd_dict)
            cmd = '~Command~:{}:Dec({})'.format(device_id,cmd_dict_str)
            self.processor_communication.SendToSystem(cmd)

        #self.__btn_tb_view_status_view['bg'] = '#f0f0f0'
        self.__toggle_button(self.__btn_tb_view_status_view,1)
        #self.__btn_tb_view_command_view['bg'] = 'sky blue'
        self.__toggle_button(self.__btn_tb_view_command_view,0)
    def __set_device_virtualui_mode(self,mode):
        def f():
            self.__selected_virtualui_mode = mode
            nav_btns = [self.__btn_mode_virtualui_navigation,self.__btn_mode_virtualui_buttons,self.__btn_mode_virtualui_knobs,self.__btn_mode_virtualui_labels,self.__btn_mode_virtualui_levels,self.__btn_mode_virtualui_sliders]
            keys = ['Navigation','Button','Knob','Label','Level','Slider']
            for key in keys:
                index = keys.index(key)
                self.Hide(self.__device_virtualui_mode_frames[key])
                #nav_btns[index]['bg'] = '#f0f0f0'
                self.__toggle_button(nav_btns[index],0)
            self.Show(self.__device_virtualui_mode_frames[mode])
            index = keys.index(mode)
            #nav_btns[index]['bg'] = 'sky blue'
            self.__toggle_button(nav_btns[index],1)
        return f

    def __eval_string(self,text:'str'):
        text.replace('\\r','\\x0d')
        text.replace('\\n','\\x0a')
        while '\\x' in text:
            pos = text.find('\\x')
            temp = text[pos:pos+4]
            val = int(temp[2:],16)
            char = chr(val)
            text = text.replace(temp,char)
        return text
    def __get_device_log_id(self,pos):
        device_id = None
        pos = int(pos)
        key_list = []
        for cur in self.device_info:
            key_list.append(int(cur))
        key_list.sort()
        if len(key_list) > pos:
            device_id = key_list[pos]
        return str(device_id)
    def __get_device_log_pos(self,device_id):
        key_list = list(self.device_info.keys())
        key_list.sort()
        pos = None
        if device_id in key_list:
            pos = str(key_list.index(device_id))
        return pos
    def __build_current_log_list(self):
        if not self.__device_log_busy:
            self.__device_log_busy = True
            log_list = []
            for id in self.__device_tree.get_checked():
                i = id.split('_')[0]
                log_list.extend(self.__device_logs[i][id])
            log_list2 = []
            for log in log_list:
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
    def __show_device_status(self,pos):
        device_id = self.__get_device_log_id(pos)
        txt = ''
        if device_id in self.device_info:
            txt = json.dumps(self.device_info[device_id]['status'],sort_keys=True,indent=2)
        posy = self.__scrollb_statusy.get()
        self.__tb_status.delete('1.0','end')
        self.__tb_status.insert(tk.END,txt)
        self.__tb_status.yview_moveto(posy[0])
        self.__tb_status.update()

    def __hide_device_commands(self):
        for f in self.__device_commands_frames:
            self.Hide(self.__device_commands_frames[f])
        for f in self.__device_virtualui_mode_frames:
            self.Hide(self.__device_virtualui_mode_frames[f])
    def __show_device_commands(self,pos):
        self.__hide_device_commands()
        device_id = self.__get_device_log_id(pos)
        device_type = None
        if device_id in self.device_info:
            device_type = self.device_info[device_id]['type']
        if device_type in self.__device_commands_frames:
            self.Show(self.__device_commands_frames[device_type])

    def __cmd_device_print_to_trace(self):
        def e():
            if self.__selected_module is None:
                return
            device_id = self.__get_device_log_id(self.__selected_module)
            val = self.__var_device_print_to_trace.get()
            cmd_dict = {'option':'print to trace'}
            if val == 1:
                cmd_dict['value'] = True
            else:
                cmd_dict['value'] = False
            cmd_dict_str = json.dumps(cmd_dict)
            cmd = '~Option~:{}:Option({})'.format(device_id,cmd_dict_str)
            self.processor_communication.SendToSystem(cmd)
        return e

    def __toggle_tb_timestamp(self):
        self.__timestamp_newest_first = not self.__timestamp_newest_first

        vals = {True:'Newest',False:'Oldest'}
        self.__btn_tb_sort_timestamp['text'] = 'Timestamp:{}'.format(vals[self.__timestamp_newest_first])
        self.__build_current_log_list()

    def __clear_device_communication_details(self):
        self.__lbl_selected_device_name.config(text= ' Selected: None')
        self.__lbl_device_comm_detail1.config(text= ' ')
        self.__lbl_device_comm_detail2.config(text= ' ')
        self.__lbl_device_comm_detail3.config(text= ' ')
        self.__lbl_device_comm_detail4.config(text= ' ')
        self.__lbl_device_comm_detail5.config(text= ' ')
        self.__lbl_device_comm_detail6.config(text= ' ')
        self.__lbl_device_comm_detail7.config(text= ' ')
    def __set_device_communication_details(self,pos):
        self.__clear_device_communication_details()
        device_id = self.__get_device_log_id(pos)
        self.__lbl_selected_device_name.config(text= ' Selected: {} '.format(self.device_info[device_id]['name']))
        self.Show(self.__frame_print_to_trace)
        if self.device_info[device_id]['options']['print to trace']:
            self.__var_device_print_to_trace.set(1)
        else:
            self.__var_device_print_to_trace.set(0)
        if 'communication' in self.device_info[device_id]:
            self.Hide(self.__frame_device_reinit)
            conn_details = self.device_info[device_id]['communication']
            dtype = conn_details['type']
            self.__lbl_device_comm_detail1.config(text= ' Type: {} '.format(conn_details['type']))
            if dtype not in ['Processor','UI','VirtualUI','SPDevice','Print']:
                self.__lbl_device_comm_detail2.config(text= ' Host: {} '.format(conn_details['host']))
            if dtype in ['Processor','UI','SPDevice','eBUSDevice']:
                self.__lbl_device_comm_detail2.config(text= ' Alias: {} '.format(conn_details['alias']))
            if dtype == 'eBUSDevice':
                self.__lbl_device_comm_detail3.config(text= ' ID: {} '.format(conn_details['id']))
            if dtype == 'SPI':
                self.Show(self.__frame_device_reinit)
            if dtype == 'Serial':
                self.Show(self.__frame_device_reinit)
                self.__lbl_device_comm_detail3.config(text= ' Port: {} '.format(conn_details['port']))
                self.__lbl_device_comm_detail4.config(text= ' Mode: {} '.format(conn_details['mode']))
                self.__lbl_device_comm_detail5.config(text= ' Baud: {} '.format(conn_details['baud']))
            elif dtype == 'Ethernet' or dtype == 'SerialOverEthernet':
                self.Show(self.__frame_device_reinit)
                self.__lbl_device_comm_detail3.config(text= ' Port: {} '.format(conn_details['port']))
                self.__lbl_device_comm_detail4.config(text= ' Mode: {} '.format(conn_details['mode']))
                if conn_details['mode'] == 'UDP':
                    self.__lbl_device_comm_detail5.config(text= ' Service Port: {} '.format(conn_details['serviceport']))
            elif dtype == 'SSH':
                self.Show(self.__frame_device_reinit)
                self.__lbl_device_comm_detail3.config(text= ' Port: {} '.format(conn_details['port']))
                self.__lbl_device_comm_detail4.config(text= ' Mode: {} '.format(conn_details['mode']))
                self.__lbl_device_comm_detail5.config(text= ' Credentials: {} '.format(conn_details['credentials']))
            elif dtype == 'Dante':
                self.Show(self.__frame_device_reinit)
                self.__lbl_device_comm_detail3.config(text= ' DanteDomainManager: {} '.format(conn_details['dantedomainmanager']))
                self.__lbl_device_comm_detail4.config(text= ' Domain: {} '.format(conn_details['domain']))
            elif dtype == 'Circuit Breaker':
                self.__lbl_device_comm_detail3.config(text= ' Port: {} '.format(conn_details['port']))
            elif dtype == 'Contact':
                self.__lbl_device_comm_detail3.config(text= ' Port: {} '.format(conn_details['port']))
            elif dtype == 'Digital Input':
                self.__lbl_device_comm_detail3.config(text= ' Port: {} '.format(conn_details['port']))
                self.__lbl_device_comm_detail4.config(text= ' Pullup: {} '.format(conn_details['pullup']))
            elif dtype == 'Digital IO':
                self.__lbl_device_comm_detail3.config(text= ' Port: {} '.format(conn_details['port']))
                self.__lbl_device_comm_detail4.config(text= ' Mode: {} '.format(conn_details['mode']))
                self.__lbl_device_comm_detail5.config(text= ' Pullup: {} '.format(conn_details['pullup']))
            elif dtype == 'Flex IO':
                self.__lbl_device_comm_detail3.config(text= ' Port: {} '.format(conn_details['port']))
                self.__lbl_device_comm_detail4.config(text= ' Mode: {} '.format(conn_details['mode']))
                self.__lbl_device_comm_detail5.config(text= ' Pullup: {} '.format(conn_details['pullup']))
                self.__lbl_device_comm_detail6.config(text= ' Upper: {} '.format(conn_details['upper']))
                self.__lbl_device_comm_detail7.config(text= ' Lower: {} '.format(conn_details['lower']))
            elif dtype == 'IR':
                self.__lbl_device_comm_detail3.config(text= ' Port: {} '.format(conn_details['port']))
                self.__lbl_device_comm_detail4.config(text= ' File: {} '.format(conn_details['file']))
            elif dtype == 'Relay':
                self.__lbl_device_comm_detail3.config(text= ' Port: {} '.format(conn_details['port']))
            elif dtype == 'SWAC Receptacle':
                self.__lbl_device_comm_detail3.config(text= ' Port: {} '.format(conn_details['port']))
            elif dtype == 'SW Power':
                self.__lbl_device_comm_detail3.config(text= ' Port: {} '.format(conn_details['port']))
            elif dtype == 'Tally':
                self.__lbl_device_comm_detail3.config(text= ' Port: {} '.format(conn_details['port']))
            elif dtype == 'Volume':
                self.__lbl_device_comm_detail3.config(text= ' Port: {} '.format(conn_details['port']))
            elif dtype == 'Processor':
                pass
            elif dtype == 'UI':
                pass
            elif dtype == 'VirtualUI':
                pass
            elif dtype == 'Print':
                pass

    def __reset_logs_for_device(self,device_id):
        self.__device_logs[device_id] = {'{}_Commands'.format(device_id):[],
                                        '{}_Events'.format(device_id):[],
                                        '{}_ToDevice'.format(device_id):[],
                                        '{}_FromDevice'.format(device_id):[]}
    def __get_device_log_key(self,device_id,log):
        i = ''
        if ' command:' in log:
            i = '{}_Commands'.format(device_id)
        if ' event:' in log:
            i = '{}_Events'.format(device_id)
        if ' <<' in log:
            i = '{}_FromDevice'.format(device_id)
        if ' >>' in log:
            i = '{}_ToDevice'.format(device_id)
        return i
    def __insert_log(self,device_id,log:'str'):
        while self.__device_log_busy:
            sleep(0.1)
        i = self.__get_device_log_key(device_id,log)
        if i and i in self.__device_logs[device_id]:
            if device_id in self.device_info:
                if '>>' in log:
                    device_name = self.device_info[device_id]['name']
                    log = log.replace('>>','comms: To Device({})   >>'.format(device_name))
                elif '<<' in log:
                    device_name = self.device_info[device_id]['name']
                    log = log.replace('<<','comms: From Device({}) <<'.format(device_name))
                if self.__timestamp_newest_first and i:
                    self.__device_logs[device_id][i].insert(0,log)
                else:
                    self.__device_logs[device_id][i].append(log)
                if i in self.__device_tree.get_checked():
                    self.__add_to_current_log_list(log)
                    self.__show_device_log()

    def __clear_all_device_logs(self):
        for i in self.__device_logs:
            for id in self.__device_logs[i]:
                self.__device_logs[i][id] = []
        self.__build_current_log_list()

    def __pause_current_device_log(self):
        self.__tb_pause_flag = not self.__tb_pause_flag
        if self.__tb_pause_flag:
            self.__btn_tb_pause_log['text'] = 'Log Paused'
            #self.__btn_tb_pause_log['bg'] = 'sky blue'
            self.__toggle_button(self.__btn_tb_pause_log,1)
        else:
            self.__btn_tb_pause_log['text'] = 'Pause Log'
            #self.__btn_tb_pause_log['bg'] = '#f0f0f0'
            self.__toggle_button(self.__btn_tb_pause_log,0)
            if self.__selected_module != None:
                self.__show_device_log()

    def __format_device_log(self):
        self.__tb_hex_flag = not self.__tb_hex_flag
        if self.__tb_hex_flag:
        #    self.__btn_tb_hex_format['bg'] = 'sky blue'
            self.__toggle_button(self.__btn_tb_hex_format,1)
            self.__btn_tb_hex_format['text'] = 'Displaying HEX'
        else:
        #    self.__btn_tb_hex_format['bg'] = '#f0f0f0'
            self.__toggle_button(self.__btn_tb_hex_format,0)
            self.__btn_tb_hex_format['text'] = 'Display Hex'
        self.__build_current_log_list()

    def __format_new_log(self,log:'str'):
        log = log.replace('\\\\','\\')
        log = log.replace("-'<<",'-<<')
        log = log.replace("-'>>",'->>')
        if log[-2:] == '\'"':
            log = log[:-2]
        elif log[-1:] == '\'':
            log = log[:-1]
        return log
    def __set_device_log_hex_format(self,log:'str'):
        if self.__tb_hex_flag:
            log = log.replace('\\r','\x0d')
            log = log.replace('\\n','\x0a')
            matches = re.findall('\\\\x(..)',log)
            for match in matches:
                match_str = '0x{}'.format(match.upper())
                an_integer = int(match_str,16)
                log = log.replace('\\x{}'.format(match),chr(an_integer))
            temp = '\\x'
            if '>>' in log:
                parts = log.split(">>")
                temp += "\x5Cx".join("{:02x}".format(ord(c)) for c in parts[1])
                return('{}>>{}'.format(parts[0],temp))
            elif '<<' in log:
                parts = log.split("<<")
                temp += "\x5Cx".join("{:02x}".format(ord(c)) for c in parts[1])
                return('{}<<{}'.format(parts[0],temp))
            else:
                return(log)
        return(log)

    def __event_device_tree_release(self):
        def e(*args):
            self.__build_current_log_list()
        return e

    def SetThemeColors(self,theme):
        btn = self.__btn_tb_clear_all_logs
        if theme == 'dark':# dark
            self.__btn_colors = {'inactive': '#1c1c1c', 'active': '#2f60d8', 'inactive text': '#fafafa', 'active text': '#ffffff'}
        else:
            self.__btn_colors = {'inactive': '#fafafa', 'active': '#2f60d8', 'inactive text': '#1c1c1c', 'active text': '#ffffff'}



    def __toggle_button(self,btn,state):
        if 'System' in btn.cget('background'):return
        if self.__btn_colors == None:
            self.__btn_colors = {'inactive':btn.cget('background'),'active':btn.cget('activebackground'),'inactive text':btn.cget('foreground'),'active text':btn.cget('activeforeground')}
            #print(self.__btn_colors)
        if state == 1:
            btn['relief'] = 'sunken'
            btn['background'] = self.__btn_colors['active']
            btn['foreground'] = self.__btn_colors['active text']
        else:
            btn['relief'] = 'raised'
            btn['background'] = self.__btn_colors['inactive']
            btn['foreground'] = self.__btn_colors['inactive text']



    #public functions
    def ResetDeviceInfoAndLogs(self):
        self.device_info = {}
        self.__device_logs = {}
        #run items in self.SetDeviceList()
        self.__clear_device_communication_details()
        self.__hide_device_commands()
        self.Hide(self.__frame_print_to_trace)
        self.__tb_log.delete('1.0','end')
        self.__tb_status.delete('1.0','end')
        self.__selected_module = None
        menu = self.__om_devices.children['menu']
        menu.delete(0,tk.END)
        self.__device_list = []
        self.__selected_device.set('Select Device')
        self.__device_tree.delete(*self.__device_tree.get_children())
        self.__device_tree.insert('', 'end', 'System', text='System')


    def SetDeviceInfo(self,device_info):
        self.device_info.update(device_info)
    def UpdateDeviceLog(self,device:'str',data:'str'):
        data = self.__format_new_log(data)
        if device not in self.__device_logs.keys():
            self.__reset_logs_for_device(device)
        self.__insert_log(device,data)

    def UpdateDeviceInfo(self,key,update_is_online=False):
        id = self.__get_device_log_pos(key)
        if id == str(self.__selected_module):
            self.__show_device_status(id)
        if update_is_online and self.__device_color_wait:
            self.__device_color_wait.Restart()
    def UpdateDeviceOption(self,key,option,value):
        id = self.__get_device_log_pos(key)
        self.device_info[key]['options'][option] = value


    def SetDeviceList(self):
        def w():
            self.__clear_device_communication_details()
            self.__initialize_hide()
            self.__tb_log.delete('1.0','end')
            self.__tb_status.delete('1.0','end')
            self.__selected_module = None
            self.__om_devices['menu'].delete(0,tk.END)
            self.__device_list = []
            self.__selected_device.set('Select Device')
            key_list = list(self.device_info.keys()) #type:list
            for i in key_list:
                try:
                    key_list[key_list.index(i)] = int(i)
                except Exception as e:
                    print('Error parsing device key list:{}'.format(str(e)))
            key_list = list(set(key_list))
            key_list.sort()
            self.__device_list = []
            for i in key_list:
                value = self.device_info[str(i)]['name']
                self.__device_list.append(value)
                self.__om_devices['menu'].add_command(label=value, command=tk._setit(self.__selected_device,value))
                if str(i) not in self.__device_logs.keys():
                    self.__reset_logs_for_device(str(i))
                if str(i) not in self.__device_tree.get_children('System'):
                    self.__device_tree.insert('System','end',str(i),text=self.device_info[str(i)]['name'])
                    self.__device_tree.insert(str(i),'end','{}_{}'.format(str(i),'Commands'),text='Commands')
                    self.__device_tree.insert(str(i),'end','{}_{}'.format(str(i),'Events'),text='Events')
                    if self.device_info[str(i)]['type'] in ['Serial','Ethernet','SerialOverEthernet','SSH','Dante','SPI']:
                        self.__device_tree.insert(str(i),'end','{}_{}'.format(str(i),'FromDevice'),text='Strings From Device')
                        self.__device_tree.insert(str(i),'end','{}_{}'.format(str(i),'ToDevice'),text='Strings To Device')


            self.__set_device_list_colors()
            #self.__clear_all_device_logs()
            self.__lbl_devices_found['text'] = 'Devices Found : {}'.format(len(self.device_info))
            self.__reading_devices_busy = False
            self.Show(self.__frame_header_body_nav)
        if self.__setDeviceListWait == None:
            self.__setDeviceListWait = Wait(1,w)
        self.__lbl_devices_found['text'] = 'Searching For Devices...'
        self.__reading_devices_busy = True
        self.__setDeviceListWait.Restart()
    def __set_device_list_colors(self):
        def w():
            if self.__device_color_wait_busy:
                return
            self.__device_color_wait_busy = True
            key_list = list(self.device_info.keys()) #type:list
            for key in key_list:
                i = self.__get_device_log_pos(key)
                color = 'blue'
                device_id=self.__get_device_log_id(i)
                status = self.device_info[device_id]['status']
                if 'ConnectionStatus' in status:
                    connectionstatus = status['ConnectionStatus']['Status']
                    if 'Live' in connectionstatus:
                        if connectionstatus['Live'] == 'Connected':
                            color = 'green'
                        if connectionstatus['Live'] == 'Not Connected':
                            color = 'red'
                        if connectionstatus['Live'] == 'Disconnected':
                            color = 'red'
                elif 'OnlineStatus' in status:
                    onlinestatus = status['OnlineStatus']['Status']
                    if 'Live' in onlinestatus:
                        if onlinestatus['Live'] == 'Online':
                            color = 'green'
                        if onlinestatus['Live'] == 'Offline':
                            color = 'red'
                self.__device_tree.tag_configure(str(device_id),foreground=color) #todo
                menu = self.__om_devices.children['menu']
                menu.entryconfig(i,foreground=color)
            self.__device_color_wait_busy = False
            self.__reading_devices_busy = False
        if self.__device_color_wait is None:
            self.__device_color_wait = Wait(1,w)
        self.__device_color_wait.Restart()
    def SetConnectStatus(self,txt):
        self.__lbl_controller_status['text'] = 'Status : {} {}'.format(self.ip_address,txt)
        if txt == 'Connected':
            self.__initialize_hide()
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

    def GetAllLogs(self):
        all_logs = []
        for device_id in self.__device_logs:
            device_name = self.device_info[device_id]['name']
            for device_key in self.__device_logs[device_id]:
                cur_logs = copy.copy(self.__device_logs[device_id][device_key]) #type:list[str]
                for cur_log in cur_logs:
                    index = cur_logs.index(cur_log)
                    if '>>' in cur_log:
                        cur_logs[index] = cur_logs[index].replace('>>','{} >>'.format(device_name))
                    if '<<' in cur_log:
                        cur_logs[index] = cur_logs[index].replace('<<','{} <<'.format(device_name))
                all_logs.extend(cur_logs)
        all_logs.sort()
        all_logs_txt = '\r\n'.join(all_logs)
        return all_logs_txt
    def GetAllStatus(self):
        all_status = []
        for device_key in self.device_info:
            device_name = self.device_info[device_key]['name']
            cur_status = self.device_info[device_key]['status']
            cur_status_txt = '{}\r\n{}'.format(device_name,pprint.pformat(cur_status,indent=5))
            all_status.append(cur_status_txt)
        all_status_txt = '\r\n\r\n'.join(all_status)
        return all_status_txt

    def GetCurrentLog(self):
        all_logs = copy.copy(self.__current_log_list)
        all_logs.sort()
        all_logs_txt = '\r\n'.join(all_logs)
        return all_logs_txt
    def GetCurrentStatus(self):
        if self.__selected_module:
            all_status = []
            device_key = self.__get_device_log_id(self.__selected_module)
            if device_key in self.__device_logs:
                device_name = self.device_info[device_key]['name']
                cur_status = self.device_info[device_key]['status']
                cur_status_txt = '{}\r\n{}'.format(device_name,pprint.pformat(cur_status,indent=5))
                all_status.append(cur_status_txt)
            all_status_txt = '\r\n\r\n'.join(all_status)
            return all_status_txt

    def HideUIView(self):
        self.Hide()
    def ShowUIView(self):
        self.Show()