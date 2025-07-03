
# `tools.py` - Advanced AV Programming Toolkit

## Overview

This module provides a comprehensive suite of tools designed to enhance the development, debugging, and management of Extron ControlScript programs. It includes a powerful remote debugging server, advanced logging capabilities, and a set of wrapper classes that extend the functionality of standard Extron library objects for easier and more robust control system programming.

## Features

*   **Remote Debugging:** A TCP-based `DebugServer` allows for real-time inspection and interaction with the running program from a companion client application.
*   **Enhanced Logging:**
    *   `DebugPrint`: A replacement for the standard `print` function that integrates with the `DebugServer` and `DebugFileLogSaver`.
    *   `DebugFileLogSaver`: Automatically saves detailed, timestamped logs in CSV format, with built-in storage management to prevent filling up the controller's memory.
    *   `ProgramLogSaver`: Automatically saves the standard `ProgramLog` to a file on a regular interval.
*   **Device & Interface Wrappers:** A collection of classes that wrap standard Extron devices (`ProcessorDevice`, `UIDevice`, `eBUSDevice`) and interfaces (`SerialInterface`, `EthernetClientInterface`, `RelayInterface`, etc.). These wrappers provide:
    *   Automatic integration with the `DebugServer`.
    *   Detailed logging of commands, events, and data.
    *   Automatic network connection management for TCP/IP and SSH devices.
*   **Virtual UI Management:** The `VirtualUI` class allows multiple physical touch panels to be treated as a single logical UI, simplifying event handling and state synchronization across combined panels.
*   **Persistent Storage Utilities:**
    *   `NonvolatileValues`: An easy-to-use class for saving and retrieving program variables to a JSON file, persisting them across reboots.
    *   `PasswordManager`: A secure way to manage system passwords, built on top of `NonvolatileValues`.

## Core Components

### Debugging and Logging

The `DebugServer` is the core of the remote debugging functionality. It should be enabled once in your main program file. The `DebugPrint` class replaces the standard `print()` function to route all output to the `DebugServer` and the log files.

**Setup Example:**
```python
from tools import DebugServer, DebugPrint
print = DebugPrint.Print

# Enable the debug server on the AVLAN interface
DebugServer.EnableDebugServer('AVLAN')

# ... rest of your program ...
print("This message will go to the trace, the log file, and the debug client.")
```

**File Logging (`DebugFileLogSaver` & `ProgramLogSaver`)**

These classes provide robust, automatic logging to the controller's file system. They manage file creation, rotation, and storage usage to prevent the device from running out of space.

**Setup Example:**
```python
from tools import DebugFileLogSaver, ProgramLogSaver

# Set the primary processor alias to enable storage management
DebugFileLogSaver.SetProcessorAlias('ProcessorAlias')
# Enable logging to file
DebugFileLogSaver.SetEnableLogging(True)

# Enable automatic saving of the standard ProgramLog
ProgramLogSaver.EnableProgramLogSaver()
```

### Device & Interface Wrappers

Instead of instantiating Extron library objects directly, use the corresponding wrapper from `tools.py`. This automatically provides logging and debugging capabilities.

**Example: Wrapping a Relay**
```python
# Instead of:
# from extronlib.interface import RelayInterface
# relay = RelayInterface(ProcessorDevice, 'RLY1')

# Use the wrapper:
from tools import RelayInterfaceWrapper, ProcessorDeviceWrapper

processor = ProcessorDeviceWrapper('ProcessorAlias')
relay = RelayInterfaceWrapper(processor, 'RLY1', friendly_name='My Projector Screen Relay')

# Now you can use the relay object as usual, with added benefits
relay.SetState('Close')
```

**Example: Wrapping a device module (e.g., a projector)**
```python
from tools import EthernetModuleWrapper
from my_projector_module import DeviceClass as ProjectorModule

# Wrap the module class
projector = EthernetModuleWrapper(ProjectorModule, friendly_name='Projector 1')
# Create the device instance
projector.Create_Device('192.168.254.100', 23, Model='MyProjectorModel')

# Send commands through the wrapper
projector.Set('Power', 'On')
# Define a event handler
def handle_event(command,value,qualifier):
    print(f"projector {command} event: {value}")
    # ... logic
projector.SubscribeStatus('Power', None, handle_event)
```

### `VirtualUI` Class

The `VirtualUI` class simplifies managing multiple touch panels, especially in divisible or combined rooms. It treats a group of panels as one, broadcasting UI commands to all of them. It can also validate UI element IDs against `_WhereUsedReportSheet.csv` files exported from GUI Designer to prevent runtime errors.

**Usage Example:**
```python
from tools import VirtualUI, UIDeviceWrapper
from main_ids import btn_power_off, lbl_room_name

# Get wrapped UIDevice objects
tp1 = UIDeviceWrapper('panel0')

# Create a VirtualUI instance
vtp = VirtualUI(friendly_name='Room 1 Virtual Panel')

# Add a panel to the virtual UI
vtp.AddPanel(tp1)

# Add UI elements that exist on the panel
vtp.AddButton(btn_power_off)
vtp.AddLabel(lbl_room_name)

# Define a button handler
def handle_power_off(button, state):
    print(f"Power off pressed on {button.Host}")
    # ... power off logic ...

# Set the function for the button
vtp.SetFunction(btn_power_off, handle_power_off, 'Pressed')

# Now, sending a command goes to all panels in the VirtualUI
vtp.SetText(lbl_room_name, "My Room")
```

### Utility Classes

#### `NonvolatileValues`

This class provides a simple way to store and retrieve data that needs to persist after a reboot.

**Usage Example:**
```python
from tools import NonvolatileValues

#default startup values
var1 = ''
var2 = 0
var3 = [False,False]

# Create an instance tied to a specific file
nvram = NonvolatileValues('my_settings.json')
def handle_nvram_var1_var2(values):
    global var1
    global var2

    if 'var1key' in values:
        var1 = values['var1key']
    if 'var2key' in values:
        var2 = values['var2key']

def handle_nvram_var3(values:'dict'):
    global var3
    if 'var3key' in values:
        var3 = values['var3key']

nvram.AddSyncValuesFunction(handle_nvram_var1_var2)
nvram.AddSyncValuesFunction(handle_nvram_var3)
# Read values on startup
nvram.ReadValues()

# ... later in the code ...

# Set a new value
nvram.SetValue('var1key',var1)
nvram.SetValue('var2key',var2)
nvram.SetValue('var3key',var3)
# Save to the file
nvram.SaveValues()
```

#### `PasswordManager`

A secure way to manage system passwords, built on top of `NonvolatileValues`.

**Usage Example:**
```python
from tools import PasswordManager

pw_manager = PasswordManager('SystemPasswords')

# Set a password
pw_manager.SetPassword('Admin', '1234')

# Generate new password for new user
generated_password = pw_manager.GeneratePassword('User1')

# Check a password
is_correct = pw_manager.CheckPassword('Admin', '1234') # Returns True
```

## License

This software is distributed under the MIT License.

```
Copyright (c) 2025 Jean-Luc Rioux

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
```

## Author & Version

*   **Author:** Jean-Luc Rioux
*   **Company:** Valley Communications
*   **Version:** 1.8.0.9 (Last Modified: 2025-03-06)
*   **DISCLAIMER:** This readme generated by Gemini Code Assist then reviewed for accuracy
