from typing import Union
import os as _os

class File():
    """ Access to files located in user area. These files are stored in a location that can be accessed using 3rd party SFTP clients.

    Note: File class accesses user area with ‘admin’ privileges.

    ---

    Arguments:
        - Filename (string) - Name of file to open
        - mode (string) - the mode in which the files is opened.
        - encoding (string) - the name of the encoding used to decode/encode the file.
        - newline (string) - controls how universal newlines mode works

    Note:
        - mode, encoding, and newline have the same meanings as those passed to the built-in function open(). See the documentation at python.org.
        - ChangeDir(), DeleteDir(), DeleteFile(), Exists(), GetCurrentDir(), ListDir(), MakeDir(), and RenameFile() are all classmethods.

    Note: For restricted file access, substitute File with RFile in the examples above and below.

    ---

    Parameters:
        - Filename - Returns (string) - name of file
    """

    __cwd = '{}'.format(_os.getcwd())
    print('File: CWD: {}'.format(__cwd))
    __dir = ''

    def __init__(self, Filename: str, mode: str='r', encoding: str='ascii', newline: str='') -> None:
        """ File class constructor.

        Arguments:
            - Filename (string) - Name of file to open
            - mode (string) - the mode in which the files is opened.
            - encoding (string) - the name of the encoding used to decode/encode the file.
            - newline (string) - controls how universal newlines mode works
        """
        self.Filename = Filename
        self.mode = mode
        self.encoding = encoding
        self.newline = newline
        self.__dir = ''
        Filename = Filename.replace('/','\\')
        self.__handle = None
        try:
            self.__handle = open('{}{}{}'.format(File.__cwd,File.__dir,Filename),mode=mode,encoding=encoding,newline=newline)
        except Exception as e:
            print('File: Failed to open file "{}":{}'.format(Filename,e))

    def ChangeDir(path: str) -> None:
        """ Change the current working directory to path

        Arguments:
            - path (string) - path to directory
        """
        if path == '/':
            path = ''
        File.__dir = path.replace('/','\\')


    def DeleteDir(path: str) -> None:
        """ Remove a directory

        Arguments:
            - path (string) - path to directory
        """
        if File.Exists(path):
            path = path.replace('/','\\')
            return _os.rmdir('{}{}{}'.format(File.__cwd,File.__dir,path))
        print('File: Failed to remove Directory: "{}" does not exist'.format(path))


    def DeleteFile(filename: str) -> None:
        """ Delete a file

        Arguments:
            - filename (string) - the name of the file to be deleted (path to file)
        """
        if File.Exists(filename):
            filename = filename.replace('/','\\')
            return _os.remove('{}{}{}'.format(File.__cwd,File.__dir,filename))
        print('File: Failed to delete file: "{}" does not exist'.format(filename))

    def Exists(path: str) -> bool:
        """ Return True if path exists

        Arguments:
            - path (string) - path to directory

        Returns
            - true if exists else false (bool)
        """
        path = path.replace('/','\\')
        return _os.path.exists('{}{}{}'.format(File.__cwd,File.__dir,path))

    def GetCurrentDir() -> str:
        """ Get the current path.

        Returns
            - the current working directory (string)
        """
        if File.__dir:
            return File.__dir.replace('\\','/')
        else:
            return '/'

    def ListDir(path: str=None) -> list:
        """ List directory contents

        Arguments:
            - path (string) - if provided, path to directory to list, else list current directory

        Returns
            - directory listing (list)
        """
        if path:
            if File.Exists(path):
                path = path.replace('/','\\')
                return _os.listdir('{}{}{}'.format(File.__cwd,File.__dir,path))
            else:
                print('File: Failed to list Directory: "{}" does not exist'.format(path))
        else:
            return _os.listdir('{}{}'.format(File.__cwd,File.__dir))

    def MakeDir(path: str) -> None:
        """ Make a new directory

        Arguments:
            - path (string) - path to directory
        """
        if not File.Exists(path):
            path = path.replace('/','\\')
            _os.makedirs('{}{}{}'.format(File.__cwd,File.__dir,path))

    def RenameFile(oldname: str, newname: str) -> None:
        """ Rename a file from oldname to newname

        Arguments:
            - oldname (string) - the original filename
            - newname (string) - the filename to rename to
        """
        oldname = oldname.replace('/','\\')
        newname = newname.replace('/','\\')
        if File.Exists(oldname):
            _os.rename('{}{}{}'.format(File.__cwd,File.__dir,oldname),'{}{}{}'.format(File.__cwd,File.__dir,newname))
            return
        print('File: Failed to rename file or directory: "{}" does not exist'.format(oldname))


    def close(self) -> None:
        """ Close an already opened file """
        if self.__handle:
            self.__handle.close()

    def read(self, size:int=-1) -> bytes:
        """ Read data from opened file

        Arguments:
            - size (int) - max number of char/bytes to read

        Returns
            - data (bytes)
        """
        if self.__handle:
            return self.__handle.read(size)
        return b''

    def readline(self) -> bytes:
        """ Read from opened file until newline or EOF occurs

        Returns
            - data (bytes)
        """
        if self.__handle:
            return self.__handle.readline()
        return b''

    def seek(self, offset: int, whence: int=0) -> None:
        """ Change the stream position

        Arguments:
            - offset (int) - offset from the start of the file
            - (optional) whence (int) -
                -  0 = absolute file positioning
                -  1 = seek relative to the current position
                -  2 = seek relative to the file’s end.

        Note: Files opened in text mode (i.e. not using 'b'), only seeks relative to the beginning of the file are allowed – the exception being a seek to the very file end with seek(0,2).
        """
        if self.__handle:
            return self.__handle.seek(offset,whence)

    def tell(self) -> int:
        """ Returns the current cursor position

        Returns
            - the current cursor position (int)
        """
        return self.__handle.tell()

    def write(self, data) -> None:
        """ Write string or bytes to file

        Arguments:
            - data (string, bytes) - data to be written to file
        """
        if self.__handle:
            self.__handle.write(data)

    def writelines(self, seq: list) -> None:
        """ Write iterable object such as a list of strings

        Arguments:
            - seq (e.g. list of strings) - iterable sequence

        Raises:
            - FileNotOpenError
        """
        if self.__handle:
            self.__handle.writelines(seq)
