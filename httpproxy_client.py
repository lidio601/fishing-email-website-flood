
import socket, select, time
from threading import Thread,Lock

__version__ = '0.1.0 Draft 1'
BUFLEN = 8192
VERSION = 'Python Proxy/'+__version__
HTTPVER = 'HTTP/1.1'

class ConnectionHandler(Thread):
	def __init__(self,connection,address=None,timeout=60):
		Thread.__init__(self)
		self.client = connection
		self.client_buffer = ''
		self.timeout = timeout
		
	def run(self):
		try:
			self.method, self.path, self.protocol = self.get_base_header()
			if self.method=='CONNECT':
				self.method_CONNECT()
			elif self.method in ('OPTIONS', 'GET', 'HEAD', 'POST', 'PUT','DELETE', 'TRACE'):
				if self.method == 'POST':
					print self.path
				self.method_others()
		except:
			self.client.close()
		else:
			self.client.close()
			self.target.close()

	def get_base_header(self):
		while 1:
			self.client_buffer += self.client.recv(BUFLEN)
			end = self.client_buffer.find('\n')
			if end!=-1:
				break
		print '%s'%self.client_buffer[:end]#debug
		data = (self.client_buffer[:end+1]).split()
		self.client_buffer = self.client_buffer[end+1:]
		return data
		
	def method_CONNECT(self):
		self._connect_target(self.path)
		self.client.send(HTTPVER+' 200 Connection established\n'+'Proxy-agent: %s\n\n'%VERSION)
		self.client_buffer = ''
		self._read_write()

	def method_others(self):
		self.path = self.path[7:]
		i = self.path.find('/')
		host = self.path[:i]        
		path = self.path[i:]
		self._connect_target(host)
		self.target.send('%s %s %s\n'%(self.method, path, self.protocol)+self.client_buffer)
		self.client_buffer = ''
		self._read_write()

	def _connect_target(self, host):
		print 'Server:request for ',host
		i = host.find(':')
		if i!=-1:
			port = int(host[i+1:])
			host = host[:i]
		else:
			port = 80
		(soc_family, _, _, _, address) = socket.getaddrinfo(host, port)[0]
		self.target = socket.socket(soc_family)
		self.target.connect(address)

	def _read_write(self):
		time_out_max = self.timeout/3
		socs = [self.client, self.target]
		count = 0
		while 1:
			count += 1
			(recv, _, error) = select.select(socs, [], socs, 3)
			if error:
				break
			if recv:
				for in_ in recv:
					data = in_.recv(BUFLEN)
					if in_ is self.client:
						out = self.target
					else:
						out = self.client
					if data:
						out.send(data)
						count = 0
					if count == time_out_max:
						break

class ServerConnectionHandler(Thread):

	def run(self, host='localhost', port=8080, IPv6=False, timeout=10):
		print 'Starting server'
		if IPv6==True:	soc_type=socket.AF_INET6
		else:	soc_type=socket.AF_INET
		server_sock = socket.socket(soc_type)
		server_sock.bind((host, port))
		server_sock.settimeout(timeout)
		print "Serving on %s:%d."%(host, port)
		server_sock.listen(0)
		run = True
		while run:
				print "server.accept"
				try:
					conn,addr = server_sock.accept()
					ConnectionHandler(conn,addr).start()
				except Exception as e:
					conn.close()
					print 'server.close()',e
					run = False
		print 'Server exiting...'
		server_sock.close()
		exit()

class ClientConnectionHandler(Thread):
	def __init__(self,req):
		Thread.__init__(self)
		self.request = req
	
	def run(self):
		print "Contacting local proxy server"
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			s.connect(('localhost', 8080))
		except Exception as e:
			print "client error ",e
		else:
			print "send request "
			s.send(self.request)
			print self.request
			ris = s.recv(BUFLEN)
			print "ricevo ",ris
			s.close()
		print "client close"

def start_server():
	ServerConnectionHandler().run()

def start_client(request):
	ClientConnectionHandler(request).start()
	
if __name__ == '__main__':
	start_server()
	#start_client("""GET / HTTP/1.0\r\nHost: www.verisign.com\r\n\r\n""")
	#start_client("""GET / HTTP/1.0\r\nHost: www.verisign.com\r\n\r\n""")
