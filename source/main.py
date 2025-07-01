'''
Version: 1.8.0.6

Created By: Jean-Luc Rioux

Last Modified: 2025-03-06

Description: Provides debugging solutions to Extron control system programs that have implemented the InterfaceWrapper class located in tools.py

Changelog:
    https://docs.google.com/spreadsheets/d/1v7Mcngqx15kRCHPC9GCGSz0uw6Fbn0OK-kflxdNUjv4/edit#gid=0


'''

import os
from tkinter import Menu,Tk
from tkinter.ttk import Frame
from tkinter import messagebox
from ProgramDebugger import ProgramDebuggerClass
from ProgramLogger import ProgramLoggerClass
from variables import variablesclass
from File import File
import sv_ttk

vars = variablesclass()

theme = 'light'
saved_theme_file = File('\\_internal\\env_theme.conf','r')
theme_from_file = saved_theme_file.readline()
theme_from_file = theme_from_file
if 'dark' in theme_from_file:
    theme = 'dark'
saved_theme_file.close()



def on_closing():
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        if vars.ui_view1.processor_communication:
            vars.ui_view1.processor_communication.EndConnections()
        window.destroy()
        os._exit(1)


def show_view(view_num:'int'):
    def f():
        alt_view_num_dict = {1:0,0:1}
        alt_view_num = alt_view_num_dict[view_num]
        try:
            i = 0
            for ui in vars.ui_views:
                ui.HideUIView()
                i+=1
            window.config(menu=menus[view_num])
            vars.ui_views[view_num].ShowUIView()
        except:
            i = 0
            for ui in vars.ui_views:
                ui.HideUIView()
                i+=1
            window.config(menu=menus[alt_view_num])
            vars.ui_views[alt_view_num].ShowUIView()

            i = 0
            for ui in vars.ui_views:
                ui.HideUIView()
                i+=1
            window.config(menu=menus[view_num])
            vars.ui_views[view_num].ShowUIView()
            window.update()
    return f
def show_theme(theme_type:'str',save_value=True):
    def f():
        if theme_type == 'dark':
            sv_ttk.use_dark_theme()
        if theme_type == 'light':
            sv_ttk.use_light_theme()
        for view in vars.ui_views:
            view.SetThemeColors(theme_type)
        if save_value:
            saved_theme_file = File('\\_internal\\env_theme.conf','w')
            saved_theme_file.writelines([theme_type])
            saved_theme_file.close()
        window.update()
    return f


window = Tk()
window.title(' Global Scripter Debugger ')
window.geometry('1024x600')
window.rowconfigure(0,weight=1)
window.columnconfigure(0,weight=1)

mainframe = Frame(window)
mainframe.grid(column=0,row=0,sticky='news')
mainframe.rowconfigure(0,weight=1)
mainframe.columnconfigure(0,weight=1)

frame_view1 = Frame(mainframe)
frame_view1.grid(column=0,row=0,sticky='news')
frame_view2 = Frame(mainframe)
frame_view2.grid(column=0,row=0,sticky='news')

vars.ui_view1 = ProgramDebuggerClass(frame_view1,vars)
vars.ui_view2 = ProgramLoggerClass(frame_view2,vars)
vars.ui_views = [vars.ui_view1,vars.ui_view2]

if True:
    debugmenubar = Menu(frame_view1)
    debugfile = Menu(debugmenubar, tearoff=0)
    debugfile.add_command(label="Connect", command=vars.ui_view1.open_connect_window)
    debugfile.add_command(label="Disconnect", command=vars.ui_view1.disconnect_from_system)
    debugfile.add_command(label="Exit", command=on_closing)
    debugsave = Menu(debugmenubar, tearoff=0)
    debugsave.add_command(label="Save Selected Logs", command=vars.ui_view1.save_current_log)
    debugsave.add_command(label="Save Selected Status", command=vars.ui_view1.save_current_status)
    debugsave.add_command(label="Save All Logs", command=vars.ui_view1.save_all_logs)
    debugsave.add_command(label="Save All Status", command=vars.ui_view1.save_all_status)
    debugview = Menu(debugmenubar, tearoff=0)
    debugview.add_command(label="Processor Debug Log", command=show_view(1))
    debugmenubar.add_cascade(label="File", menu=debugfile)
    debugmenubar.add_cascade(label="Save", menu=debugsave)
    debugmenubar.add_cascade(label="View", menu=debugview)
    themeview = Menu(debugmenubar, tearoff=0)
    themeview.add_command(label="Light", command=show_theme('light'))
    themeview.add_command(label="Dark", command=show_theme('dark'))
    debugmenubar.add_cascade(label="Theme", menu=themeview)

    pgmlogmenubar = Menu(frame_view2)
    pgmlogfile = Menu(pgmlogmenubar, tearoff=0)
    pgmlogfile.add_command(label="Exit", command=on_closing)
    pgmlogsave = Menu(pgmlogmenubar, tearoff=0)
    pgmlogsave.add_command(label="Save Selected Logs", command=vars.ui_view2.save_selected_logs)
    pgmlogsave.add_command(label="Save All Logs", command=vars.ui_view2.save_all_logs)
    pgmlogview = Menu(debugmenubar, tearoff=0)
    pgmlogview.add_command(label="Live Debug Log", command=show_view(0))
    pgmlogmenubar.add_cascade(label="File", menu=pgmlogfile)
    pgmlogmenubar.add_cascade(label="Save", menu=pgmlogsave)
    pgmlogmenubar.add_cascade(label="View", menu=pgmlogview)
    themeview = Menu(pgmlogmenubar, tearoff=0)
    themeview.add_command(label="Light", command=show_theme('light'))
    themeview.add_command(label="Dark", command=show_theme('dark'))
    pgmlogmenubar.add_cascade(label="Theme", menu=themeview)


menus = [debugmenubar,pgmlogmenubar]
window.config(menu=debugmenubar)

for widget in window.winfo_children():
    try:
        widget.pack(fill='both',expand=1)
    except Exception as e:
        print('error resizing for {}:{}'.format(str(widget),e))

window.protocol("WM_DELETE_WINDOW", on_closing)

show_theme(theme,False)()

window.mainloop()