import socket,time,re
from typing import Union
from threading import Thread

socket.getaddrinfo('localhost',8080)

class EthernetClientInterface():
    """ This class provides an interface to a client ethernet socket. This class allows the user to send data over the ethernet port in a synchronous or asynchronous manner.

    Note: In synchronous mode, the user will use SendAndWait to wait for the response. In asynchronous mode, the user will assign a handler function to ReceiveData event handler. Then responses and unsolicited messages will be sent to the users receive data handler.

    Arguments:
        - Hostname (string) - DNS Name of the connection. Can be IP Address
        - IPPort (int) - IP port number of the connection
        - (optional) Protocol  (string) - Value for either 'TCP', 'UDP', or 'SSH'
        - (optional) ServicePort  (int) - Sets the port on which to listen for response data, UDP only, zero means listen on port OS assigns
        - (optional) Credentials  (tuple) - Username and password for SSH connection.

    Parameters:
        - Credentials - Returns (tuple, bool) - Username and password for SSH connection.
            - Note:
                - returns tuple: ('username', 'password') if provided otherwise None.
                - only applies when protocol 'SSH' is used.
        - Hostname - Returns (string) - server Host name
        - IPAddress - Returns (string) - server IP Address
        - IPPort - Returns (int) - IP port number of the connection
        - Protocol - Returns (string) - Value for either 'TCP', 'UDP', 'SSH' connection.
        - ServicePort - Returns (int) - the port on which the socket is listening for response data

    Events:
        - Connected - (Event) Triggers when socket connection is established.
        - Disconnected - (Event) Triggers when the socket connection is broken
        - ReceiveData - (Event) Receive Data event handler used for asynchronous transactions. The callback takes two arguments. The first one is the EthernetClientInterface instance triggering the event and the second one is a bytes string.
            - Note:
                - The maximum amount of data per ReceiveData event that will be passed into the handler is 1024 bytes. For payloads greater than 1024 bytes, multiple events will be triggered.
                - When UDP protocol is used, the data will be truncated to 1024 bytes.
    """

    def __init__(self, Hostname:'str', IPPort:'int', Protocol='TCP', ServicePort=0, Credentials=None):
        """ EthernetClientInterface class constructor.

        Arguments:
            - Hostname (string) - DNS Name of the connection. Can be IP Address
            - IPPort (int) - IP port number of the connection
            - (optional) Protocol  (string) - Value for either 'TCP', 'UDP', or 'SSH'
            - (optional) ServicePort  (int) - Sets the port on which to listen for response data, UDP only, zero means listen on port OS assigns
            - (optional) Credentials  (tuple) - Username and password for SSH connection.
        """
        self.Connected = None
        self.Disconnected = None
        self.ReceiveData = None

        self.__socket = None #type:socket.socket
        self.__client = None #type:Client
        self.__connected = False
        self.__rec_thread = None
        self.__rec_thread_stop = True
        self.__keepalive_thread = None
        self.__keepalive_thread_run = False

        self.Hostname = Hostname
        self.IPPort = IPPort
        self.Protocol = Protocol
        self.ServicePort = ServicePort
        self.Credentials = Credentials

    def Connect(self, timeout=None):
        """ Connect to the server

        Arguments:
            - (optional) timeout (float) - time in seconds to attempt connection before giving up.

        Returns
            - 'Connected' or 'ConnectedAlready' or reason for failure (string)

        Note: Does not apply to UDP connections.
        """
        if self.__connected:
            return
        if self.Protocol == 'UDP':
            pass
        if self.__connected:
            return('ConnectedAlready')
        self.__client = Client()
        self.__client.server = self
        self.__client.IPAddress = self.Hostname
        try:
            print('connecting to ip:{} port {}'.format(self.Hostname, self.IPPort))
            self.__socket = socket.create_connection((self.Hostname,self.IPPort))
        except Exception as e:
            self.__client.client = None
            print('failed to connect:{}'.format(str(e)))
            return('Connection Timeout')
        if self.__socket is not None:
            self.__connected = True
            if self.Protocol == 'TCP':
                self.__rec_thread_stop = False
                self.__rec_thread = Thread(target=self.__recv_func(self.__socket))
                self.__rec_thread.start()
            if self.Connected is not None:
                self.Connected(self.__client,'Connected')
            return('Connected')
        elif self.Disconnected is not None:
            self.Disconnected(self.__client,'Disconnected')
            return('Disconnected')

    def Disconnect(self):
        """ Disconnect the socket

        Note: Does not apply to UDP connections.
        """
        if not self.__connected:
            return
        self.__rec_thread_stop = True
        self.__socket.shutdown(socket.SHUT_RDWR)
        self.__socket.close()
        self.__connected = False
        self.__socket = None
        if self.__socket is None:
            self.StopKeepAlive()
            if self.Disconnected is not None:
                self.Disconnected(self.__client,'Disconnected')

    def Send(self, data:'str'):
        """ Send string over ethernet port if it's open

        Arguments:
            - data (bytes, string) - string to send out

        Raises:
            - TypeError
            - IOError
        """
        if not self.__connected:
            return
        try:
            if data:
                self.__socket.send(data.encode('utf-8'))
        except:
            pass

    def SendAndWait(self, data:'str', timeout:'float', deliTag:'bytes'='', deliRex:'str'='',deliLen:'int'=''):
        """ Send data to the controlled device and wait (blocking) for response. It returns after timeout seconds expires or immediately if the optional condition is satisfied.

        Note: In addition to data and timeout, the method accepts an optional delimiter, which is used to compare against the received response. It supports any one of the following conditions:
            -    > deliLen (int) - length of the response
            -    > deliTag (bytes) - suffix of the response
            -    > deliRex (regular expression object) - regular expression

        Note: The function will return an empty byte array if timeout expires and nothing is received, or the condition (if provided) is not met.

        Arguments:
            - data (bytes, string) - data to send.
            - timeout (float) - amount of time to wait for response.
            - delimiter (see above) - optional conditions to look for in response.

        Returns:
            - Response received data (may be empty) (bytes)
        """
        #return('')
        if not self.__connected:
            return('')
        buffer = b''
        self.__socket.send(data.encode('utf-8'))
        while True:
            if deliTag: #delimiter is bytes at which to stop reading
                delim = deliTag
                data += self.__socket.recv()
                if not data:
                    break
                buffer += data
                if delim in buffer:
                    index = buffer.index(delim)
                    buffer = buffer[:index+len(delim)]
                    break
            elif deliLen: #delimiter is a legnth to receive
                delim = deliLen
                data += self.__socket.recv(delim)
                if not data:
                    break
                buffer += data
                if len(buffer) >= deliLen:
                    buffer = buffer[:deliLen]
                    break
            elif deliRex: #delimiter should be a regular expression
                data += self.__socket.recv()
                if not data:
                    break
                buffer += data
                match = re.search(delim,data.decode())
                if match is not None:
                    buffer = buffer[:match.end()].encode('utf-8')
                    break
        return(buffer)

    def StartKeepAlive(self, interval:'int', data:'Union[bytes,str]'):
        """ Repeatedly sends data at the given interval

        Arguments:
            - interval (float) - Time in seconds between transmissions
            - data (bytes, string) - data bytes to send
        """
        if self.__keepalive_thread:
            self.__keepalive_thread_run = False
            self.__keepalive_thread.join()
        self.__keepalive_thread_run = True
        self.__keepalive_thread = Thread(target=self.__keepalive_func(self.__socket,interval,data))
        self.__keepalive_count = 0
        self.__keepalive_thread.start()


    def StopKeepAlive(self):
        """ Stop the currently running keep alive routine
        """
        self.__keepalive_thread_run = False
        if self.__keepalive_thread:
            self.__keepalive_thread.join()
        self.__keepalive_thread = None

    def __recv_func(self,client:'socket.socket'):
        def r():
            while True:
                if self.__rec_thread_stop:
                    break
                try:
                    data = client.recv(4096)
                except:
                    if self.Disconnected is not None:
                        self.Disconnected(self.__client,'Disconnected')
                    self.Disconnect()
                    data = b''
                if self.ReceiveData is not None and len(data):
                    self.ReceiveData(self,data)
                time.sleep(0.1)
        return r

    def __keepalive_func(self,client:'socket.socket',interval:'int',cmd:'str'):
        def k():
            while self.__keepalive_thread_run:
                if client and self.__keepalive_count > 0:
                    self.Send(cmd)
                time.sleep(interval)
                self.__keepalive_count += 1
        return k

class Client():

    IPAddress = ''
    client = None
    server = None
    def Send(self,data):
        self.server.Send(data)