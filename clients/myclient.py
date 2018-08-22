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
		pass
	
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
		''' 获取Swap的总内存和已使用的内存 '''
		Mem = psutil.swap_memory()
		return int(Mem.total/1024.0), int(Mem.used/1024.0)

	def get_hdd(self):
		''' 获取硬盘的容量和已使用的空间 '''
		valid_fs = [ "ext4", "ext3", "ext2", "reiserfs", "jfs", "btrfs", "fuseblk", "zfs", "simfs", "ntfs", "fat32", "exfat", "xfs" ]
		disks = dict()
		size = 0
		used = 0
		for disk in psutil.disk_partitions():
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

	def get_net_flow(self):
		''' 获取网络流量 '''
		NET_IN = 0
		NET_OUT = 0
		net = psutil.net_io_counters(pernic=True)
		for k, v in net.items():
			if k == 'lo' or 'tun' in k \
					or 'br-' in k \
					or 'docker' in k or 'veth' in k:
				continue
			else:
				NET_IN += v[1]
				NET_OUT += v[0]
		return NET_IN, NET_OUT

	def get_network(self, ip_version):
		''' '''
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

class Traffic:
	def __init__(self):
		self.rx = collections.deque(maxlen=10)
		self.tx = collections.deque(maxlen=10)

	def get(self):
		avgrx = 0; avgtx = 0
		for name, stats in psutil.net_io_counters(pernic=True).items():
			if name == "lo" or name.find("tun") > -1 \
					or name.find("docker") > -1 or name.find("veth") > -1 \
					or name.find("br-") > -1:
				continue
			avgrx += stats.bytes_recv
			avgtx += stats.bytes_sent

		self.rx.append(avgrx)
		self.tx.append(avgtx)
		avgrx = 0; avgtx = 0

		l = len(self.rx)
		for x in range(l - 1):
			avgrx += self.rx[x+1] - self.rx[x]
			avgtx += self.tx[x+1] - self.tx[x]

		avgrx = int(avgrx / l / INTERVAL)
		avgtx = int(avgtx / l / INTERVAL)

		return avgrx, avgtx

	def get_sys_info(self):
		pass

def SendDataToServer(SERVER, PORT, USER, PWD, INTERVAL):
    ''' 给指定服务器发送设备的信息 '''
	
    pass

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

	ma = MachineInfo();
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

			traffic = Traffic()
			# traffic.get()
			while True:
				CPU = ma.get_cpu()
				NetRx, NetTx = traffic.get()
				NET_IN, NET_OUT = ma.get_net_flow()
				Uptime = ma.get_uptime()
				Load_1, Load_5, Load_15 = os.getloadavg() if 'linux' in sys.platform else (0.0, 0.0, 0.0)
				MemoryTotal, MemoryUsed = ma.get_memory()
				SwapTotal, SwapUsed = ma.get_swap()
				HDDTotal, HDDUsed = ma.get_hdd()
				IP_STATUS = ma.ip_status()

				array = {}
				# print("timer = ", timer)
				if not timer:
					array['online' + str(check_ip)] = ma.get_network(check_ip)
					timer = 10
				else:
					timer -= 1*INTERVAL

				# print("timer =", timer, ", online = ", array['online' + str(check_ip)])	

				array['uptime'] = Uptime
				array['load_1'] = Load_1
				array['load_5'] = Load_5
				array['load_15'] = Load_15
				array['memory_total'] = MemoryTotal
				array['memory_used'] = MemoryUsed
				array['swap_total'] = SwapTotal
				array['swap_used'] = SwapUsed
				array['hdd_total'] = HDDTotal
				array['hdd_used'] = HDDUsed
				array['cpu'] = CPU
				array['network_rx'] = NetRx
				array['network_tx'] = NetTx
				array['network_in'] = NET_IN
				array['network_out'] = NET_OUT
				array['ip_status'] = IP_STATUS
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
