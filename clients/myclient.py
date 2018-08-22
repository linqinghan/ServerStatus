# /usr/bin/env Python
# -*- coding=utf-8 -*-
# 功能：获取系统的相关信息，然后以Json数据的形式，发送给服务器
# 依赖于psutil跨平台库，仅在Python3.6 + Windows 7 64bit上验证过
# 


# 这边根据需要修改服务器的IP和端口
SERVER = "127.0.0.1"
PORT = 35601
USER = "s04"  # 这边的用户名和密码需要在服务器上config.json文件中存在
PASSWORD = "USER_DEFAULT_PASSWORD"
INTERVAL = 1 # 更新间隔


import socket
import time
import string
import math
import os
import json
import collections
import psutil
import sys


class MachineInfo():
	''' 获取设备相关的信息 '''
	def __init__(self):
		self.net_stat = collections.deque(maxlen=10)

		self.add_one_net_state()
	
	def get_uptime(self):
		''' 获取开机到现在的时间 '''
		return int(time.time() - psutil.boot_time())

	def get_memory(self):
		''' 获取总内存和已使用的内存 '''
		Mem = psutil.virtual_memory()
		try:
			MemUsed = Mem.total - (Mem.cached + Mem.free)
		except:
			MemUsed = Mem.total - Mem.free
		return int(Mem.total/1024.0), int(MemUsed/1024.0)

	def get_swap(self):
		''' 获取Swap的总内存和已使用的内存, 单位：KB '''
		Mem = psutil.swap_memory()
		return int(Mem.total/1024.0), int(Mem.used/1024.0)

	def get_hdd(self):
		''' 获取硬盘的容量和已使用的空间, 单位:MB '''
		valid_fs = [ "ext4", "ext3", "ext2", "reiserfs", "jfs", "btrfs", "fuseblk", "zfs", "simfs", "ntfs", "fat32", "exfat", "xfs" ]
		disks = dict()
		size = 0
		used = 0

		for disk in psutil.disk_partitions():	# 获取所有磁盘的信息		
			if not disk.device in disks and disk.fstype.lower() in valid_fs:
				disks[disk.device] = disk.mountpoint

		for disk in disks.values():
			usage = psutil.disk_usage(disk)
			size += usage.total
			used += usage.used
		return int(size/1024.0/1024.0), int(used/1024.0/1024.0)

	def get_cpu(self):
		''' 获取CPU占用率 '''
		return psutil.cpu_percent(interval=INTERVAL)

	def get_total_net_bytes(self):
		''' 获取网络发送和接收的总字节数 '''
		total_recv_bytes = 0
		total_send_bytes = 0

		net = psutil.net_io_counters(pernic=True)
		for interface_name, stat in net.items(): # 获取所有的网络接口的信息
			# 过滤掉不相干的网络接口
			if interface_name == 'lo' or 'tun' in interface_name \
					or 'br-' in interface_name \
					or 'docker' in interface_name or 'veth' in interface_name:
				continue
			
			total_recv_bytes += stat.bytes_recv
			total_send_bytes += stat.bytes_sent

		return total_recv_bytes, total_send_bytes

	def add_one_net_state(self):
		''' 往双向链表添加一个记录 '''
		stat = {}
		stat['time'] = time.time()
		stat['rx'], stat['tx'] = self.get_total_net_bytes()

		self.net_stat.append(stat)

	def get_avge_net_bytes(self):
		''' 获取网络平均的发送和接收的速度 '''
		self.add_one_net_state()
		
		diff_time = self.net_stat[len(self.net_stat) - 1]['time'] - self.net_stat[0]['time']
		diff_rx = self.net_stat[len(self.net_stat) - 1]['rx'] - self.net_stat[0]['rx']
		diff_tx = self.net_stat[len(self.net_stat) - 1]['tx'] - self.net_stat[0]['tx']

		if diff_time == 0 or len(self.net_stat) == 1:
			return (diff_rx, diff_tx)

		avg_rx = diff_rx / diff_time
		avg_tx = diff_tx / diff_time

		return (avg_rx, avg_tx)

	def get_avg_load(self):
		''' 获取系统的平均负载[仅在Linux系统可用] '''
		if 'linux' in sys.platform:
			return os.getloadavg()
		return (0.0, 0.0, 0.0)
		# Load_1, Load_5, Load_15 = os.getloadavg() if 'linux' in sys.platform else (0.0, 0.0, 0.0)

	def get_network(self, ip_version):
		''' 连接 IPV4或IPV6网址 '''
		if(ip_version == 4):
			HOST = "ipv4.google.com"
		elif(ip_version == 6):
			HOST = "ipv6.google.com"
		try:
			s = socket.create_connection((HOST, 80), 2)
			return True
		except:
			pass
		return False

	# todo: 不确定是否要用多线程or多进程:  效率? 资源?　
	def ip_status(self):
		''' 连接指定网络，判断是否通 '''
		object_check = ['www.10010.com', 'www.189.cn', 'www.10086.cn']
		ip_check = 0
		for i in object_check:
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.settimeout(1)
			try:
				s.connect((i, 80))
			except:
				ip_check += 1
			s.close()
			del s
		if ip_check >= 2:
			return False
		else:
			return True

	def get_sys_info(self, update_online_flag, check_ip):
		''' 获取系统信息，通过字典返回结果 '''
		NetRx, NetTx = self.get_avge_net_bytes()
		NET_IN, NET_OUT = self.get_total_net_bytes()
		
		Load_1, Load_5, Load_15 = self.get_avg_load()
		MemoryTotal, MemoryUsed = self.get_memory()
		SwapTotal, SwapUsed = self.get_swap()
		HDDTotal, HDDUsed = self.get_hdd()

		array = {}

		if update_online_flag:
			array['online' + str(check_ip)] = ma.get_network(check_ip)

		array['uptime'] = self.get_uptime()
		array['load_1'] = Load_1
		array['load_5'] = Load_5
		array['load_15'] = Load_15
		array['memory_total'] = MemoryTotal
		array['memory_used'] = MemoryUsed
		array['swap_total'] = SwapTotal
		array['swap_used'] = SwapUsed
		array['hdd_total'] = HDDTotal
		array['hdd_used'] = HDDUsed
		array['cpu'] = self.get_cpu()
		array['network_rx'] = NetRx
		array['network_tx'] = NetTx
		array['network_in'] = NET_IN
		array['network_out'] = NET_OUT
		array['ip_status'] = self.ip_status()

		return array


def SendDataToServer(SERVER, PORT, USER, PWD, INTERVAL):
    ''' 给指定服务器发送设备的信息 '''
	
    pass

if __name__ == "__main2__":
	ma = MachineInfo()
	print(ma.get_sys_info(True, 4))
	
	first_time = time.time()
	while True:				
		curr_time = time.time()
		if curr_time - first_time > 30:
			print("Break")
			break
		print("hello....")
		time.sleep(1)
	# count = 0
	# while True:
	# 	if count >= 10:
	# 		break
	# 	count += 1
	# 	print(ma.get_avge_net_bytes())
	# 	time.sleep(3)


if __name__ == '__main__':
	for argc in sys.argv:
		if 'SERVER' in argc:
			SERVER = argc.split('SERVER=')[-1]
		elif 'PORT' in argc:
			PORT = int(argc.split('PORT=')[-1])
		elif 'USER' in argc:
			USER = argc.split('USER=')[-1]
		elif 'PASSWORD' in argc:
			PASSWORD = argc.split('PASSWORD=')[-1]
		elif 'INTERVAL' in argc:
			INTERVAL = int(argc.split('INTERVAL=')[-1])

	ma = MachineInfo()
	socket.setdefaulttimeout(30)
	while True:
		try:
			print("Connecting...")
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.connect((SERVER, PORT))
			data = s.recv(1024)
			strdata = bytes.decode(data)
			if strdata.find("Authentication required") > -1:
				strdata = USER + ':' + PASSWORD + '\n'
				s.send(str.encode(strdata))
				data = s.recv(1024)
				strdata = bytes.decode(data)
				if strdata.find("Authentication successful") < 0:
					print(data)
					raise socket.error
			else:
				print(data)
				raise socket.error
			print("1".center(50, "-"))
			print(data)
			data = s.recv(1024)
			print(data)

			timer = 0
			check_ip = 0
			strdata = bytes.decode(data)
			if strdata.find("IPv4") > -1:
				check_ip = 6
			elif strdata.find("IPv6") > -1:
				check_ip = 4
			else:
				print(data)
				raise socket.error

			update_online_flag = True
			first_time = time.time()
			while True:				
				curr_time = time.time()
				if curr_time - first_time > 10:
					first_time = curr_time
					update_online_flag = True

				array = ma.get_sys_info(update_online_flag, check_ip)

				update_online_flag = False
				strdata = "update " + json.dumps(array) + "\n"
				# print("Send".center(80, "-"))
				# print(strdata)
				s.send(str.encode(strdata))
				# print("Send Ok".center(80, "-"))
		except KeyboardInterrupt:
			raise
		except socket.error:
			print("Disconnected...")
			# keep on trying after a disconnect
			s.close()
			time.sleep(3)
		except Exception as e:
			print("Caught Exception:", e)
			s.close()
			time.sleep(3)
