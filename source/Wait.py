from threading import Thread
import time



class Wait():
    """ The wait class allows the user to execute programmed actions after a desired delay without blocking other processor activity.

    In addition to being used as a one-shot (decorator), Wait can be named and reusable.

    ---

    Arguments:
        - Time (float) - Expiration time of the wait in seconds
        - Function (function) - Code to execute when Time expires

    ---

    Parameters:
        - Function - Returns (function) - Code to execute when Time expires.
        - Time - Returns (float) - Expiration time of the wait in seconds with 10ms precision.
    """

    def __call__(self,func):
        """ Decorate a function to be the handler of an instance of the Wait class.

        The decorated function must have no parameters
        """
        if func is None:
            print('Wait Error: function is None')
            return
        self.Function = func
        def decorator(Time):
            self.__init__(Time,func)
        return decorator




    def __init__(self, Time: float, Function: callable=None) -> None:
        """ File class constructor.

        Arguments:
            - Time (float) - Expiration time of the wait in seconds
            - Function (function) - Code to execute when Time expires
        """
        self.__process__ = None #type:Thread
        self.__process_active__ = False
        self.__current_run = 0

        self.Time = Time
        self.Function = Function
        self.__run_wait__()

    def Add(self, Time: float) -> None:
        """ Add time to current timer. """

    def Cancel(self) -> None:
        """ Stop wait Function from executing when the timer expires. """
        self.__current_run = self.__current_run+1

    def Change(self,Time:'float') -> None:
        """ Set a new Time value for current and future timers in this instance. """
        self.Time = Time


    def Restart(self) -> None:
        """ Restarts the timer – executes the Function in Time seconds. If the a timer is active, cancels that timer before starting the new timer.
        """
        self.Cancel()
        self.__run_wait__()


    def __run_wait__(self) -> None:
        self.__current_run = self.__current_run+1
        run_index = self.__current_run
        self.__process__ = Thread(target=self.__func__(self.Time,run_index))
        self.__process__.start()
        self.__process_active__ = True

    def __func__(self,Time:'float',run_index) -> None:
        def f():
            time.sleep(Time)
            if self.__current_run == run_index:
                self.Function()
        return f
