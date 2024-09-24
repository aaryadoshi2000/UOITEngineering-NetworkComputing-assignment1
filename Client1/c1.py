import threading
import socket
import mimetypes
import platform
import sys
import os
from pathlib import Path
import time



class MyException(Exception):
    pass


class Client(object):
    def __init__(self, hostingserver='localhost', Version='P2P-CI/1.0', DIR='file'):
        self.hosting_server = hostingserver #name of the hosting server
        self.port_serving = 7734 #port no. at which server is there
        self.Vupdate = Version # given version
        self.patta = 'file'  # file directory
        Path(self.patta).mkdir(exist_ok=True) #making the directory file

        self.port_of_upload = None
        self.common = True

    def start(self): # start function is responsible for connecting the client to the server and starting the thread instance corresponding to it
        # Making a connection to the  server
        print('Connecting to the server %s:%s' %
              (self.hosting_server, self.port_serving))
        self.main_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try: # try except block is used if bychance the server is not avaialable error can be thrown
            self.main_server.connect((self.hosting_server, self.port_serving))
        except Exception:
            print('Server is Not Available.')
            return

        print('Client is Connected')
        processs_uploading_thread = threading.Thread(target=self.upload_initiate)
        processs_uploading_thread.start()
        while self.port_of_upload is None:
            # wait till the time upload port is initialized
            pass
        print('Clientis Listening on the upload port %s' % self.port_of_upload)

        # displaying the interactive options
        self.available_options()

    def available_options(self):
        #mapping_dict is used to map the functions to the option in the interactive shell
        mapping_dict = {'1': self.file_addition,
                        '2': self.file_lookup,
                        '3': self.file_listing,
                        '4': self.intiating_download,
                        '5': self.closedown}
        while True: #loop till we are getting the input
            try:
                req = input(
                    '\n1: Add, 2: Look Up, 3: List All, 4: Download, 5: Shut Down\nEnter your request: ')
                mapping_dict.setdefault(req, self.wrong_input)() # if input is wrong wrong_input is called
            except MyException as f:
                print(f)
            except Exception:
                print('Error in system.')
            except BaseException:
                self.closedown()

    def upload_initiate(self): #this function is responsible for initiating the the upload and then it is passed to upload_handler
        # upload port listening
        self.socket_uploading = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_uploading.bind(('', 0))
        self.port_of_upload = self.socket_uploading.getsockname()[1]
        self.socket_uploading.listen(5)

        while self.common: #while common is true it will work
            front_req, apata = self.socket_uploading.accept()
            thread_handler = threading.Thread(
                target=self.upload_handling, args=(front_req, apata))
            thread_handler.start() #starting the instance of thread using start()
        self.socket_uploading.close()

    def upload_handling(self, main_socket, addr):
        main_header_to_be_printed = main_socket.recv(1024).decode().splitlines()
        try:
            after_split_version = main_header_to_be_printed[0].split()[-1]# version is stored
            ank_no = main_header_to_be_printed[0].split()[-2] #
            defined_methods = main_header_to_be_printed[0].split()[0]# which method is used
            way = '%s/file%s.txt' % (self.patta, ank_no)#path of the file
            if after_split_version != self.Vupdate: #if version is not equal following error messa ge is encoded
                main_socket.sendall(str.encode(
                    self.Vupdate + ' 505 P2P-CI Version Not Supported\n'))
            elif not Path(way).is_file(): #if file is not found
                main_socket.sendall(str.encode(self.Vupdate + ' 404 Not Found\n'))
            elif defined_methods == 'GET': #if the defined  method is get
                main_header_to_be_printed = self.Vupdate + ' 200 OK\n'
                main_header_to_be_printed += 'Data: %s\n' % (time.strftime(
                    "%a, %d %b %Y %H:%M:%S GMT", time.gmtime()))
                main_header_to_be_printed += 'OS: %s\n' % (platform.platform())
                main_header_to_be_printed += 'Last-Modified: %s\n' % (time.strftime(
                    "%a, %d %b %Y %H:%M:%S GMT", time.gmtime(os.path.getmtime(way))))
                main_header_to_be_printed += 'Content-Length: %s\n' % (os.path.getsize(way))
                main_header_to_be_printed += 'Content-Type: %s\n' % (
                    mimetypes.MimeTypes().guess_type(way)[0])
                #in the above lines the response header is appended to get the required format
                with open(way) as f:
                    k=f.readlines()
                for i in k:
                    main_header_to_be_printed+='(%s)\n'%(i)
                main_socket.sendall(main_header_to_be_printed.encode())

                try:

                    length_of_file_sending = 0
                    with open(way, 'r') as file:
                        reading_the_file_to_send = file.read(1024)
                        while reading_the_file_to_send:
                            length_of_file_sending += len(reading_the_file_to_send.encode())
                            main_socket.sendall(reading_the_file_to_send.encode())
                            reading_the_file_to_send = file.read(1024)
                except Exception:
                    raise MyException('Uploading Failed')

                #print('FILE Uploading Completed.')
                print(
                    '\n1: Add, 2: Look Up, 3: List All, 4: Download\nEnter your request: ')
            else:
                raise MyException('Bad Request.')
        except Exception:
            main_socket.sendall(str.encode(self.Vupdate + '  400 Bad Request\n'))
        finally:
            main_socket.close()

    def file_addition(self, file_no=None, mount=None): #responsible for adding the file
        if not file_no:
            file_no = input('Enter the FILE number: ')
            if not file_no.isdigit(): #if the file no. is not digit
                raise MyException('Invalid Input.')
            mount = input('Enter the FILE title: ')
        file_doc = Path('%s/file%s.txt' % (self.patta, file_no))
        print(file_doc)
        if not file_doc.is_file():
            raise MyException('File Not Exists!')
        file_with_message = 'ADD FILE %s %s\n' % (file_no, self.Vupdate)
        file_with_message += 'Host: %s\n' % socket.gethostname()
        file_with_message += 'Port: %s\n' % self.port_of_upload
        file_with_message += 'Title: %s\n' % mount
        self.main_server.sendall(file_with_message.encode())
        res = self.main_server.recv(1024).decode()
        #the above lines appending the receive response to be sent to server
        print('Recieve response: \n%s' % res)

    def file_lookup(self): #responsible for the lookup  of the files from the available files.
        entered_file_for_lookup = input('Enter the FILE number: ')
        file_title_if_userwants = input('Enter the FILE title(optional): ')
        file_with_message = 'LOOKUP FILE %s %s\n' % (entered_file_for_lookup, self.Vupdate)
        file_with_message += 'Host: %s\n' % socket.gethostname()
        file_with_message += 'Port: %s\n' % self.port_of_upload
        file_with_message += 'Title: %s\n' % file_title_if_userwants
        self.main_server.sendall(file_with_message.encode())
        final_decoding_message = self.main_server.recv(1024).decode()
        print('Recieve response: \n%s' % final_decoding_message)

    def file_listing(self): #listing the files available in the required format
        a = 'LIST ALL %s\n' % self.Vupdate
        b = 'Host: %s\n' % socket.gethostname()
        c = 'Port: %s\n' % self.port_of_upload
        sandesha = a + b + c
        self.main_server.sendall(sandesha.encode())
        final_listing = self.main_server.recv(1024).decode()
        print('Recieve response: \n%s' % final_listing)

    def intiating_download(self):
        file_no = input('Enter the FILE number: ')
        complied_print = 'LOOKUP FILE %s %s\n' % (file_no, self.Vupdate)
        complied_print += 'Host: %s\n' % socket.gethostname()
        complied_print += 'Port: %s\n' % self.port_of_upload
        complied_print += 'Title: Unkown\n'
        self.main_server.sendall(complied_print.encode())
        sequence_of_text_in_lines = self.main_server.recv(1024).decode().splitlines()
        if sequence_of_text_in_lines[0].split()[1] == '200':
            # choosing peers from the available peers
            print('Available peers: ')
            for k, p in enumerate(sequence_of_text_in_lines[1:]):
                p = p.split()
                print('%s: %s:%s' % (k + 1, p[-2], p[-1]))

            try:
                integer_input_of_peer_index = int(input('Choose one peer to download: '))
                main_head = sequence_of_text_in_lines[integer_input_of_peer_index].rsplit(None, 2)[0].split(None, 2)[-1]
                hosting_peer = sequence_of_text_in_lines[integer_input_of_peer_index].split()[-2]
                port_no_of_peer = int(sequence_of_text_in_lines[integer_input_of_peer_index].split()[-1])
            except Exception:
                raise MyException('Invalid Input.')
            if((hosting_peer, port_no_of_peer) == (socket.gethostname(), self.port_of_upload)):
                raise MyException('Do not choose yourself.')
            self.final_download(file_no, main_head, hosting_peer, port_no_of_peer)
        elif sequence_of_text_in_lines[0].split()[1] == '404':
            raise MyException('File is not Available.')
        elif sequence_of_text_in_lines[0].split()[1] == '400':
            raise MyException('Input is Invalid.')
        elif sequence_of_text_in_lines[0].split()[1] == '500':
            raise MyException('Version Not Supported.')

    def final_download(self, i, main_head, hosting_peer, port_of_peer):
        try:
            connecting_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if connecting_socket.connect_ex((hosting_peer, port_of_peer)):
                raise MyException('Peer Not Available')

            final_message = 'GET FILE %s %s\n' % (i, self.Vupdate)
            final_message += 'Host: %s\n' % socket.gethostname()
            final_message += 'OS: %s\n' % platform.platform()
            connecting_socket.sendall(final_message.encode())
            print('')
            print('Request Message:')
            print(final_message)
            # FILE Downloading

            mheader = connecting_socket.recv(1024).decode()
            print('Recieve response header: \n%s' % mheader)
            mheader = mheader.splitlines()
            if mheader[0].split()[-2] == '200':
                path = '%s/file%s.txt' % (self.patta, i)
                print('FILE Downloading...')
                try:
                    with open(path, 'w') as file:
                        content = connecting_socket.recv(1024)
                        while content:
                            file.write(content.decode())
                            content = connecting_socket.recv(1024)
                except Exception:
                    raise MyException('FILE Downloading Failed')

                length_total = int(mheader[4].split()[1])


                if os.path.getsize(path) < length_total:
                    raise MyException('FILE Downloading Failed')

                print('FILE Download Completed.')
                # Share file, send ADD request
                print('ADD request is sending to share...')
                if self.common:
                    self.file_addition(i, main_head)
            elif mheader[0].split()[1] == '404':
                raise MyException('FILE File is Not Available.')
            elif mheader[0].split()[1] == '400':
                raise MyException('Input is invalid.')
            elif mheader[0].split()[1] == '500':
                raise MyException('Not Supported Version.')
        finally:
            connecting_socket.close()


    def wrong_input(self):
        raise MyException('Invalid Input.')

    def closedown(self):
        print('\nShutting Down the client...')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)


if __name__ == '__main__':
    if len(sys.argv) == 2:
        starting_client = Client(sys.argv[1])
    else:
        starting_client = Client()
    starting_client.start()
