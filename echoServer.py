#-*- coding: utf-8 -*-
from tornado.tcpserver import TCPServer
from tornado.ioloop import IOLoop
from tornado.options import options, parse_command_line, define
from tornado import process,netutil
 
import logging,struct,sys
 
 
class ECHO(object):
    _client = set()
 
    def __init__(self, stream, server):
        ECHO._client.add(self)
        self.server = server
        self._stream = stream
        self.uid = None
        self.head = 127
        self.headLen = 8
        self.read()
        stream.set_close_callback(self.close_stream)
 
    def read(self):
        #logging.info(('read %s'%self._stream))
    #   self._stream.read_until_close(self.checkdata)
    #def checkdata(self,data):
    #    print data
        self._stream.read_bytes(self.headLen,self.on_headers)
 
    def on_headers(self,data):
        logging.info(('data : %s'%(data)))
        if str(data) == '<policy-':
            rs = open('socket-policy.xml', 'rt').read()
            rs = bytes(rs)
            self._stream.write(rs,self._stream.close)
        head,tl,num = struct.unpack('!hhl',data[:self.headLen])
        logging.info((head,tl,num))
        if num == 10001:
            self._stream.read_bytes(int(tl-self.headLen), self.login)
        if num == 10003:self.getUserlist()
        if num == 10005:
            self._stream.read_bytes(int(tl-self.headLen), self.talk)
             
         
    def login(self,data):
        tl = len(data)
        print 'login ... %d'%tl
        name, = struct.unpack(str(tl)+'s',data)
        self.uid = name
         
        self.sendMsg(10002,self.uid,None)
         
        rs = [i.uid for i in ECHO._client]
        rs = bytes(rs)
         
        logging.info(('name is %s list %s'%(self.uid,rs)))
        self.sendall(10004,rs)
 
    def close_stream(self, *args, **kwargs):
        """Called on client disconnected"""
        logging.info(('Client disconnected%s',self.uid))
        ECHO._client.remove(self)
         
        rs = [i.uid for i in ECHO._client]
        rs = bytes(rs)
        self.sendall(10004,rs,False)
        self._stream.close()
         
 
         
    def sendMsg(self, code, msg, callback):
        mylen = self.headLen + len(msg)
        a = struct.pack('>hhl'+str(len(msg))+'s',self.head,mylen,code,msg)  
        self._stream.write(a,callback=callback)
     
    def sendall(self, code, msg, hascall=True):
        for i in ECHO._client:
            client = i
            client.sendMsg(code,msg,callback=None)
        if hascall : self.read()
     
    def getUserlist(self):
        rs = [i.uid for i in ECHO._client]
        #rs.remove(self.uid)
        rs = bytes(rs)
        logging.info(('getuserlist%s'%rs))
        self.sendMsg(10004,rs,self.read)
     
    def talk(self,data):
        tl = len(data)
        print 'talk ... %d'%tl
        msg, = struct.unpack(str(tl)+'s',data)
        logging.info(('talk : %s'%msg))
 
        self.sendall(10006,msg)
 
         
 
class ECHOServer(TCPServer):
 
    def handle_stream(self,stream,address):
        logging.info("echo connecting...%r",address)
        ECHO(stream,self)
 
class Policy(TCPServer):
    def handle_stream(self,stream,address):
        logging.info("policy ....")
        rs = open('socket-policy.xml', 'rt').read()
        rs = bytes(rs)
        print rs
        stream.write(rs)
 
               
if __name__ == '__main__':
    parse_command_line()
     
    socket1 = netutil.bind_sockets(8000)
    #socket2 = netutil.bind_sockets(843)
    process.fork_processes(0)
 
    server = ECHOServer()
    server.add_sockets(socket1)
    #server2 = Policy()
    #server2.add_sockets(socket2)
 
    IOLoop.instance().start()
