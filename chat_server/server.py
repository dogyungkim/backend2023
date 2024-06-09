#!/usr/bin/python3

import json
import select
import socket
import sys


from absl import app, flags
import threading


FLAGS = flags.FLAGS
IP = '127.0.0.1'

flags.DEFINE_integer(name='port', default=None, required=True, help='서버 port 번호')
flags.DEFINE_enum(name='format', default='json', enum_values=['json', 'protobuf'], help='메시지 포맷')
flags.DEFINE_integer(name='workers', default=2,  help='작업 쓰레드 숫자')

class SocketClosed(RuntimeError):
  pass

class NoCommandFieldInMessage(RuntimeError):
  pass

# Client 소켓 정보를 위한 배열
client_sockets = []
  # i/o Multiplexing을 위해 배열, sever의 이벤트를 받기위해 sever socket을 처음으로 설정
readsocks = []
writesocks = []

# 멀티쓰레딩을 위한 변수들
task_queue = []
threads = []
condition = threading.Condition() # pyhton condition은 lock 도 잡아줌
quit_sig = False # python은 기본적으로 thread safe하게 처리함 (GIL)


# 생성된 방 리스트
room_list = []
room_count = 0


class Room:
  '''
  채팅 방을 위한 클래스
  '''

  def __init__(self,client,title):
    global room_count
    self.roomId = room_count + 1
    room_count = self.roomId
    self.title = title
    self.members = [client]
    room_list.append(self)
    print(f'방[{self.roomId}]: 생성. 방제 {self.title}')

  def get_members_name(self):
    names = []
    for member in self.members:
      names.append(member.name)
    return names

  def get_rooms_to_json(self):
    members = self.get_members_name()
    msg = {
      'roomId' : self.roomId,
      'title' : self.title,
      'members' : members
    }
    return msg

  def is_client_in_room(self,client):
    if client in self.members:
      return True
    else:
      return False

  def client_leave_room(self,client):
    if client in self.members:
      self.members.remove(client)
    return self.members.count

  def client_enter_room(self,client):
    self.members.append(client)

    

class Client :
  '''
  클라이언트 관리를 위한 클래스
  '''
  def __init__(self,sock,addr):
    self.sock = sock
    self.name = addr[0] + ":" + str(addr[1])

  def change_name(self,name):
    print(f'사용자 {self.name}의 이름이 {name}으로 변경되었습니다')
    self.name = name
    
def addClient(sock,addr):
  '''
  서버에 접속한 클라이언트의 sock 정볼르 가지고 Client 클래스 생성 및 client 
  '''
  client_sockets.append(Client(sock,addr))
  print(f'클라이언트 {addr[0]} : {addr[1]} 연결 완료')


# 클라이언트에게 메시지를 보내는 함수들
def sc_send_message(client,messages):

  for msg in messages:

    msg_str = None
    serialized = bytes(json.dumps(msg), encoding='utf-8')
    msg_str = json.dumps(msg)

    to_send = len(serialized)
    to_send_big_endian = int.to_bytes(to_send, byteorder='big', length=2)

    serialized = to_send_big_endian + serialized

    offset = 0
    attempt = 0
    while offset < len(serialized):
      num_sent = client.sock.send(serialized[offset:])
      if num_sent <= 0:
        raise RuntimeError('Send failed')
      offset += num_sent

def sc_send_system_message(client,message):
  '''
  클라이언트에게 메시지를 보내는 함수
  '''
  msg_buffer = {
    'type' : 'SCSystemMessage',
    'text' : message,
  }
  messages = [msg_buffer]
  sc_send_message(client,messages)

def sc_send_room_message(client,message):
  msg_buffer = {
    'type' : "SCRoomsResult",
    'rooms' : message,
  }
  messages = [msg_buffer]
  sc_send_message(client,messages)

def sc_send_chat_to_rooms(sender,room,msg):
  msg_buffer ={
    'type' : 'SCChat',
    'member': sender.name,
    'text' : msg,
  }
  message = [msg_buffer]
  for client in room.members:
    if client != sender:
      sc_send_message(client,message)
  

'''
클라이언트 요청 사항을 처리하는 함수들
'''
def process_client_message(index):
  '''
  TCP는 stream처럼 보이게 데이터가 온다.
  중간에 데이터 손실이 있을 수 있기에 완전히 데이터를 받은 뒤 처리해야한다.
  '''
  while(quit_sig == False):
    print(f'Thread {index}')
    current_message_len = None
    socket_buffer = None

    condition.acquire()
    while len(task_queue) < 1:
      condition.wait()
    
    sock = task_queue.pop(0) 
    received_buffer = sock.recv(65535)
    condition.release()
    
    
    if not received_buffer:
      raise SocketClosed()
    if not socket_buffer:
      socket_buffer = received_buffer
    else:
      socket_buffer += received_buffer

    # 받아야할 데이터의 길이를 확인
    if current_message_len is None:
      if len(socket_buffer) < 2:
        return
      current_message_len = int.from_bytes(socket_buffer[0:2], byteorder='big')
      socket_buffer = socket_buffer[2:]

    # 현재까지 받은 데이터가 다 도착하지 않았음
    if len(socket_buffer) < current_message_len:
      return

    # 처리할 데이터의 길이를 알았으면, 그만큼 짤라낸다
    serialized = socket_buffer[:current_message_len]
    socket_buffer = socket_buffer[current_message_len:]
    current_message_len = None

    # Json 처리
    msg = json.loads(serialized)
    command = msg.get('type',None)

    if not command:
      raise NoCommandFieldInMessage()

    for client in client_sockets:
      if client.sock == sock:
        sock = client

    if command in command_handlers:
      command_handlers[command][0](sock,msg)    

    if FLAGS.verbosity >= 2:
     print(f'  - recv(): {len(received_buffer)}바이트 읽음')

def client_change_name(client,msg):
  name = msg.get('name',None)
  client.change_name(name)
  
  message = f'이름이 {name} 으로 변경되었습니다.'
 
  message_hander["SCSystemMessage"][0](client,message)

def client_check_rooms(client,msg):
  message = []
  for room in room_list:
    if room.is_client_in_room(client):
     buf = room.get_rooms_to_json()
     message.append(buf)
     break
    else:
      buf = room.get_rooms_to_json()
      message.append(buf)
  
  message_hander["SCRoomsResult"][0](client,message)

def client_create_room(client, msg):

  title = msg.get('title',None)
  is_client = False
  for room in room_list:
    if room.is_client_in_room(client):
      is_client = True
      break
  
  if is_client:
    message = f'대화 방에 있을 때는 방을 개설 할 수 없습니다.'
    sc_send_system_message(client,message)
  else:
    new_rooms = Room(client,title)
    message = f'방제 {title} 방에 입장하셧습니다.'
    message_hander['SCSystemMessage'][0](client,message)

def client_join_room(client,msg):
  room_num = msg.get('roomId',None)
  for room in room_list:
    if room.is_client_in_room(client) :
      msg = f'대화 방에 있을 때는 다른 방에 들어갈 수 없습니다.'
      sc_send_system_message(client,msg)
    if room_num == room.roomId:
      room.client_enter_room(client)
      break

def client_leave_room(client,msg):
  for room in room_list:
    if room.is_client_in_room(client):
     if room.client_leave_room(client) == 0 :
      room_list.remove(room)
      print(f'사용자 종료로 인한 방폭')
      break
     msg = f'방제 {room.title} 대화 방에서 퇴장했습니다.'
     sc_send_system_message(client,msg)
     break

def client_chat_message(client,msg):
  text = msg.get('text',None)
  for room in room_list:
    if room.is_client_in_room(client) :
      sc_send_chat_to_rooms(client,room,text)
      break

def client_shutdown(client,msg):
  print(f'서버 중지가 요청됨')
  for client_socket in client_sockets:
    if client == client_socket:
      client_sockets.remove(client)
  if client.sock in readsocks:
    readsocks.remove(client.sock)
 
  client.sock.close()
  quit_sig = True

def join_threads():
  for i in threads.count:
    print(f'메시지 작업 쓰레드 #{i} 종료')
    threads[i].join()
    
  
message_hander = {
  'SCSystemMessage':(sc_send_system_message, '시스템 메시지 전달'),
  'SCRoomsResult' : (sc_send_room_message, '방 정보 전달'),
}

command_handlers = {
  'CSName' : (client_change_name,'클라이언트 이름을 변경'),
  'CSRooms' : (client_check_rooms,'생성된 방 확인'),
  'CSCreateRoom': (client_create_room,'클라이언트가 방을 생성'),
  'CSJoinRoom' : (client_join_room, '클라이언트가 방에 들어감'),
  'CSLeaveRoom' : (client_leave_room,'클라이언트가 방을 나감'),
  'CSChat': (client_chat_message,'클라이언트가 메시지를 보냄'),
  'CSShutdown' : (client_shutdown,'클라이언트 접속 해제')
}


def prepare_socket(port):
  """
  서버의 준비를 한다.
    - socket 생성
    - IP, Port bind
    - listen
  """

  print(f'Server starting')
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
  sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  sock.bind((IP,port))
  print(f'Port 번호 {port}에서 서버 동작 중')

  sock.listen()
  return sock


def main(argv):

  if not FLAGS.port:
    print('서버의 Port 번호를 지정해야 됩니다.')
    sys.exit(1)

  for i in range(FLAGS.workers):
    print(f'메시지 작업 쓰레드 #{i} 생성')
    thread = threading.Thread(target=process_client_message,args=(i,))
    threads.append(thread)
    thread.start()

  server_sock = prepare_socket(FLAGS.port)
  readsocks.append(server_sock)


  while (quit_sig == False) :
    try:
      readables, writeables, excpetions = select.select(readsocks, writesocks, readsocks, None)
      for sock in readables:
        # 서버 소켓의 event인 경우, 클라이언트 추가
        if sock == server_sock:
          client_socket, addr = sock.accept()
          addClient(client_socket, addr)
          readsocks.append(client_socket)

        # 클라이언트 소켓의 event인 경우, 클라이언트 명령처리
        else:
          condition.acquire()    
          task_queue.append(sock) 
          condition.notify(1)
          condition.release() 
        

    except NoCommandFieldInMessage:
      print('클라이언트가 보낸 메시지에 command 필드가 없음')
      # while 문을 종료한다.
      break

    except socket.error as err:
      print(f'소켓 에러: {err}')
      # while 문을 종료한다.
      break

    # 클라이언트와 연결 해제
    if client_socket in client_sockets:
        client_shutdown(client_socket.sock)
        print('remove client list : ', len(client_sockets))
  

  for thread in threads:
    thread.join()

  if sock:
    sock.close()

  
  

if __name__ == '__main__':

  app.run(main)
