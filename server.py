import threading
import socket
import sys
import os
from collections import defaultdict


class Server(object):
    def __init__(self, name_of_host='', server_port=7734, Ver='P2P-CI/1.0'):
        self.Hosting_port = name_of_host
        self.Hosting_port_no = server_port
        self.Ver = Ver
        # list of peers contain in the form of element: {(host,port), set[file #]}
        self.info_about_peers = defaultdict(set)
        # list of files containing in the form of element: {FILE #, (title, set[(host, port)])}
        self.list_of_files = {}
        self.thread_lock = threading.Lock()

    # server start listenning on the port
    # start function is responsible initiating the socket for server and operations using thread
    def start(self):
        try:
            self.t = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.t.bind((self.Hosting_port, self.Hosting_port_no))
            self.t.listen(5)
            print('Server %s is listening on port %s' %
                  (self.Ver, self.Hosting_port_no))

            while True:
                cos, address = self.t.accept()
                print('%s:%s connected' % (address[0], address[1]))
                Instance_ofthread = threading.Thread(
                    target=self.connect_with_client_handler, args=(cos, address))
                Instance_ofthread.start()
        except KeyboardInterrupt:
            print('\nShutting down the server..\nGood Bye!')
            try:
                sys.exit(0)
            except SystemExit:
                os._exit(0)

    # Making a connection with a client
    def connect_with_client_handler(self, rec_soc, soc_addr):
        # keep recieve request from client
        rec_host = None
        rec_port = None
        while True:
            try:
                rec_req = rec_soc.recv(1024).decode()
                print('Recieve request:\n%s' % rec_req)
                splitted_lines = rec_req.splitlines()
                ser_version = splitted_lines[0].split()[-1]
                if ser_version != self.Ver:
                    rec_soc.sendall(str.encode(
                        self.Ver + ' 505 P2P-CI Version Not Supported\n'))
                else:
                    implement_method = splitted_lines[0].split()[0]
                    if implement_method == 'ADD':
                        rec_host = splitted_lines[1].split(None, 1)[1]
                        rec_port = int(splitted_lines[2].split(None, 1)[1])
                        no = int(splitted_lines[0].split()[-2])
                        mtitle = splitted_lines[3].split(None, 1)[1]
                        self.Record_addition(rec_soc, (rec_host, rec_port), no, mtitle)
                    elif implement_method == 'LOOKUP':
                        no = int(splitted_lines[0].split()[-2])
                        self.retrieving_PeersOfFile(rec_soc, no)
                    elif implement_method == 'LIST':
                        self.retrieveAllRecords(rec_soc)
                    else:
                        raise AttributeError('Method Not Match')
            except ConnectionError:
                print('%s:%s left' % (soc_addr[0], soc_addr[1]))
                # data is cleaned based on the situation
                if rec_host and rec_port:
                    self.rec_clear(rec_host, rec_port)
                rec_soc.close()
                break
            except BaseException:
                try:
                    rec_soc.sendall(str.encode(self.Ver + '  400 Bad Request\n'))
                except ConnectionError:
                    print('%s:%s left' % (soc_addr[0], soc_addr[1]))
                    # Cleaning  data if necessary
                    if rec_host and rec_port:
                        self.rec_clear(rec_host, rec_port)
                    rec_soc.close()
                    break

    def rec_clear(self, clear_host, clear_port):
        self.thread_lock.acquire()
        info_peers = self.info_about_peers[(clear_host, clear_port)]
        for num in info_peers:
            self.list_of_files[num][1].discard((clear_host, clear_port))
        if not self.list_of_files[num][1]:
            self.list_of_files.pop(num, None)
        self.info_about_peers.pop((clear_host, clear_port), None)
        self.thread_lock.release()

    def Record_addition(self, record_soc, record_peer, record_num, m_title):
        self.thread_lock.acquire()
        try:
            self.info_about_peers[record_peer].add(record_num)
            self.list_of_files.setdefault(record_num, (m_title, set()))[1].add(record_peer)
        finally:
            self.thread_lock.release()
        # print(self.files)
        # print(self.peers)
        printing_header = self.Ver + ' 200 OK\n'
        printing_header += 'FILE %s %s %s %s\n' % (record_num,
                                                  self.list_of_files[record_num][0], record_peer[0], record_peer[1])
        record_soc.sendall(str.encode(printing_header))

    def retrieving_PeersOfFile(self, peer_of_soc, peer_of_num):

        self.thread_lock.acquire()
        try:
            if peer_of_num not in self.list_of_files:
                mount_header = self.Ver + ' 404 Not Found\n'
            else:
                mount_header = self.Ver + ' 200 OK\n'
                main_title = self.list_of_files[peer_of_num][0]
                for peer in self.list_of_files[peer_of_num][1]:
                    mount_header += 'FILE %s %s %s %s\n' % (peer_of_num,
                                                           main_title, peer[0], peer[1])
        finally:
            self.thread_lock.release()
        peer_of_soc.sendall(str.encode(mount_header))

    def retrieveAllRecords(self, record_soc):
        self.thread_lock.acquire()
        try:
            if not self.list_of_files:
                ver_header = self.Ver + ' 404 Not Found\n'
            else:
                ver_header = self.Ver + ' 200 OK\n'
                for file_num in self.list_of_files:
                    main_title = self.list_of_files[file_num][0]
                    for peer in self.list_of_files[file_num][1]:
                        ver_header += 'FILE %s %s %s %s\n' % (file_num,
                                                             main_title, peer[0], peer[1])
        finally:
            self.thread_lock.release()
        record_soc.sendall(str.encode(ver_header))


if __name__ == '__main__':
    server = Server()

    server.start()
