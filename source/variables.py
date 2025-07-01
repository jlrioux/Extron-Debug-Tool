from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ProgramDebugger import ProgramDebuggerClass
    from ProgramLogger import ProgramLoggerClass
    from ProgramDebuggerLib import ProcessorCommunicationClass

class variablesclass():
    def __init__(self):
        self.ui_view1 = None #type:ProgramDebuggerClass
        self.ui_view2 = None #type:ProgramLoggerClass
        self.ui_views = [] #type:list[ProgramDebuggerClass]
