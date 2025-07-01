from threading import Thread
import time

class Timer():
    """ The Timer class allows the user to execute programmed actions on a regular time differential schedule.

    Note:
        - The handler (Function) must accept exactly two parameters, which are the Timer that called it and the Count.
        - If the handler (Function) has not finished by the time the Interval has expired, Function will not be called and Count will not be incremented (i.e. that interval will be skipped).

    In addition to being used as a decorator, Timer can be named and modified.

    ---

    Arguments:
        - Interval (float) - How often to call the handler in seconds (minimum interval is 0.1s).
        - Function (function) - Handler function to execute each Interval.

    ---

    Parameters:
        - Count - Returns (int) - Number of events triggered by this timer.
        - Function - Returns (function) - Handler function to execute each Interval. Function must accept exactly two parameters, which are the Timer that called it and the Count.
        - Interval - Returns (float) - How often to call the handler in seconds.
        - State - Returns (string) - Current state of Timer ('Running', 'Paused', 'Stopped')

    ---

    Events:
        - StateChanged - (Event) Triggers when the timer state changes. The callback takes two arguments. The first is the Timer instance triggering the event and the second is a string ('Running', 'Paused', 'Stopped').
    """


    def __call__(self,func):
        """ Decorate a function to be the handler of an instance of the Wait class.

        The decorated function must have no parameters
        """
        if func is None:
            print('Timer Error: function is None')
            return
        def decorator(Interval):
            self.__init__(Interval,func)
        return decorator


    def __init__(self, Interval: float, Function: callable=None) -> None:
        """ Timer class constructor.

        Arguments:
            - Interval (float) - How often to call the handler in seconds (minimum interval is 0.1s).
            - Function (function) - Handler function to execute each Interval.
        """
        self.Count = 0

        self.__process__ = None #type:Thread
        self.__process_active__ = False

        self.Interval = Interval
        self.Function = Function
        self.__run_wait__()

    def Change(self, Interval: float) -> None:
        """ Set a new Interval value for future events in this instance.

        Arguments:
            - Interval (float) - How often to call the handler in seconds.

        """
        self.Interval = Interval

    def Pause(self) -> None:
        """ Pause the timer (i.e. stop calling the Function).

        Note: Does not reset the timer or the Count.
        """
        if self.__process_active__:
            self.__process_active__=False

    def Resume(self) -> None:
        """ Resume the timer after being paused or stopped.
        """
        if not self.__process_active__:
            self.__run_wait__()

    def Restart(self) -> None:
        """Restarts the timer – resets the Count and executes the Function in Interval seconds."""

        if self.__process_active__:
            self.Stop()
        self.__run_wait__()

    def Stop(self) -> None:
        """ Stop the timer.

        Note: Resets the timer and the Count.
        """
        if self.__process_active__:
            self.Count = 0
            self.__process_active__ = False



    def __run_wait__(self) -> None:

        self.__process__ = Thread(target=self.__func__(self.Interval))
        self.__process__.start()
        self.__process_active__ = True

    def __func__(self,Time:'float') -> None:
        def f():
            time.sleep(Time)
            try:
                if self.__process_active__:
                    self.Count += 1
                    self.Function(self,self.Count)
                    self.__process_active__ = False
                    self.__run_wait__()
            except:
                pass
        return f
