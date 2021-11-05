#!/usr/bin/env python3
#MIT License
#
#Copyright (c) 2021 TheHWcave
#
#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.
#

#
#	Implements a class that can read Brymen BM869S (and similar) meters
#   using the Brymen USB interface cable
#
import argparse
import hid,sys
from time import sleep,time,localtime,strftime,perf_counter


VID 	= 0x0820
PID 	= 0x0001

#
#  Note: 
#		The remote interface of the BM meters is actually a copy 
#		of the segments activated on the LCD display. This means for
#		the values we have to convert 7-segment back into numbers. 
#		and interpret the various annouciators on the LCD. This makes 
#		unfortunately for a very dense piece of software. You need to
#		consult the Brymen documentation of the LCD to understand what
#		is going on...
#
#          aaaaa
#         f     b
#         f     b
#          ggggg
#         e     c
#         e     c
#       xx ddddd 
#
#          bgcdafex
SEVSEG = {'00000000':'  ',
		  '00000001':'. ',
		  '10111110':' 0',
		  '10111111':'.0',
		  '10100000':' 1',
		  '10100001':'.1',
		  '11011010':' 2',
		  '11011011':'.2',
		  '11111000':' 3',
		  '11111001':'.3',
		  '11100100':' 4',
		  '11100101':'.4',
		  '01111100':' 5',
		  '01111101':'.5',
		  '01111110':' 6',
		  '01111111':'.6',
		  '10101000':' 7',
		  '10101001':'.7',
		  '11111110':' 8',
		  '11111111':'.8',
		  '11111100':' 9',
		  '11111101':'.9',
		  '00010110':' L',
		  '00010111':'.L',
		  '11110010':' d',
		  '00100000':' i',
		  '01110010':' o',
		  '11110010':' d',
		  '01100010':' n',
		  '01011110':' E',
		  '01000010':' r',
		  '00011110':' C',
		  '01001110':' F'}



class BM869S:
	
	_h : None
	_DBYTES = bytearray(24)
	_DBITS  = ['00000000'] * 24
	_mdsp	= ''
	_mmode	= ''
	_sdsp	= ''
	_smode	= ''
	_msg	= '\x00\x00\x86\x66'
	def __init__(self):
		
		self._h = hid.Device(VID,PID)
		
		

	def Store(self,chunk, data):
		# print(str(chunk)+' '+str(len(data))+':',end='')
		# for b in data:
			# print(hex(b)+' ',end='')
		# print()
		self._DBYTES[8*chunk:8*chunk+7] = data
		n = 0
		for b in data:
			self._DBITS[8*chunk+n] = format(b,'08b')
			n = n + 1			
			
	def Decode(self):
		#print(self._DBITS)
			
		#------------------------------------------------------------------
		# main display mode and range 
		self._mmode = ''
		if   self._DBITS[1][3] == '1' and self._DBITS[2][7] == '1': self._mmode = 'AC+DC '
		elif self._DBITS[1][3] == '1': self._mmode = 'DC '
		elif self._DBITS[2][7] == '1': self._mmode = 'AC '
		if self._mmode != '':
			if self._DBITS[15][4] == '1': self._mmode = self._mmode + 'u'
			if self._DBITS[15][5] == '1': self._mmode = self._mmode + 'm'
			if self._DBITS[14][0] == '1': self._mmode = self._mmode + 'A'
			if self._DBITS[8][7]  == '1': self._mmode = self._mmode + 'V'
		else:
			if self._DBITS[15][7] == '1': 
				self._mmode = self._mmode + 'HZ'
				if self._DBITS[15][1] == '1': self._mmode = 'k'+self._mmode
				if self._DBITS[15][2] == '1': self._mmode = 'M'+self._mmode
			elif self._DBITS[15][6] == '1': self._mmode = self._mmode + 'dB'
			elif self._DBITS[15][0] == '1': self._mmode = self._mmode + 'D%'
			if self._mmode == '':
				if self._DBITS[2][5] == '1': self._mmode = 'T1-T2'
				elif self._DBITS[2][4] == '1': self._mmode = 'T2'
				elif self._DBITS[2][6] == '1': self._mmode = 'T1'
				if self._mmode == '':
					if self._DBITS[15][3] == '1': 
						self._mmode = 'OHM'
						if self._DBITS[15][1] == '1': self._mmode = 'k'+self._mmode
						if self._DBITS[15][2] == '1': self._mmode = 'M'+self._mmode
				
					elif self._DBITS[14][2] == '1': 
						self._mmode = 'F'
						if self._DBITS[14][1] == '1': self._mmode = 'n'+self._mmode
						if self._DBITS[15][4] == '1': self._mmode = 'u'+self._mmode
						if self._DBITS[15][5] == '1': self._mmode = 'm'+self._mmode
					elif self._DBITS[14][3] == '1': 
						self._mmode = 'S'
						if self._DBITS[14][1] == '1': self._mmode = 'n'+self._mmode
		#------------------------------------------------------------------
		# secondary display mode and range 
		
		
		self._smode = ''
		if self._DBITS[9][2] == '1': 
			self._smode = 'AC '
		elif self._DBITS[14][4] == '1' or self._DBITS[9][5] == '1' or self._DBITS[9][4] == '1':
			self._smode = 'DC '
		if self._smode != '':
			if self._DBITS[9][7] == '1': self._smode = self._smode + 'u'
			if self._DBITS[9][6] == '1': self._smode = self._smode + 'm'
			if self._DBITS[9][5] == '1': self._smode = self._smode + 'A'
			if self._DBITS[9][4] == '1': self._smode = self._smode + '%4-20mA'
			if self._DBITS[14][4]  == '1': self._smode = self._smode + 'V'
		else:
			if self._DBITS[14][5] == '1': 
				self._smode = self._smode + 'HZ'
				if self._DBITS[14][6] == '1': self._smode = 'k'+self._smode
				if self._DBITS[14][7] == '1': self._smode = 'M'+self._smode
			if self._smode == '':
				if self._DBITS[9][1] == '1': self._smode = 'T2'
		
		
		#------------------------------------------------------------------
		#signs for main and secondary displays
		if self._DBITS[2][0] == '1': 
			self._mdsp = '-'
		else:
			self._mdsp = ''
			
		if self._DBITS[9][3] == '1': 
			self._sdsp = '-'
		else:
			self._sdsp = ''
		#------------------------------------------------------------------
		# main display digits
		for n in range(3,9): 
			v = self._DBITS[n]
			#print(str(n)+' '+v+' = ',end='')
			if v in SEVSEG:
				digit = SEVSEG[v]
			else:
				digit = ' ?'
			if digit[0] ==' ' or (n == 3) or (n == 8):
				self._mdsp = self._mdsp + digit[1]
			else:
				self._mdsp = self._mdsp + digit
		if self._mmode.startswith('T'):
			self._mmode = self._mmode + ' '+self._mdsp[-1:]
			self._mdsp = self._mdsp[:-1]
		#print(self._mdsp+' '+self._mmode)
		#------------------------------------------------------------------
		# secondary display digits
		for n in range(10,14): 
			v = self._DBITS[n]
			#print(str(n)+' '+v+' = ',end='')
			if v in SEVSEG:
				digit = SEVSEG[v]
			else:
				digit = ' ?'
			if digit[0] ==' ' or n == 10:
				self._sdsp = self._sdsp + digit[1]
			else:
				self._sdsp = self._sdsp + digit
		#print(self._sdsp+' '+self._smode)
		return (self._mdsp,self._mmode,self._sdsp,self._smode)


	def readdata(self):
		"""
			returns the data from the BM869S in form of a list with 4 entries 
			entry
			0: the number as shown on the main display of the BM869S
			1: the unit&mode belonging to the main display, e.g. "mVDC" or "OHM"
			2: the number as shown on the secondary display (or blank if no secondary display is active)
			3: the unit&mode belonging to the secondary display, e.g. "HZ" (or blank)
		"""
		self._h.write(self._msg.encode('latin1'))
		chunk = 0
		res = ''
		Done = False
		while not Done:
			x = self._h.read(24,4000)
			if len(x) > 0:
				self.Store(chunk,x)
				chunk = chunk + 1
				if chunk > 2:
					Done = True
					res = self.Decode()
		return res

	
	
if __name__ == "__main__":
	#
	#	This implements a sample implementation in form of a logger 
	# 	it reads the BM869s periodically, determined by the --time setting
	#   and writes the data from primary and secondary displays into a 
	#	a CSV file (and shows them on the screen)
	#
	
	parser = argparse.ArgumentParser()
	
	parser.add_argument('--out','-o',help='output filename (default=BM869s_<timestamp>.csv)',
					dest='out_name',action='store',type=str,default='!')
	parser.add_argument('--time','-t',help='interval time in seconds between measurements (def=1.0)',
					dest='int_time',action='store',type=float,default=1.0)
					
	arg = parser.parse_args()
	
	BM = BM869S()
	PRI_READING	= 0
	PRI_UNIT	= 1
	SEC_READING	= 2
	SEC_UNIT	= 3
		
	if arg.out_name=='!':
		out_name = 'BM869s_'+strftime('%Y%m%d%H%M%S',localtime())+'.csv'
	else:
		out_name = arg.out_name
		
	
		
	f = open(out_name,'w')
	f.write('Time[S],Main,Main unit,Secondary,Secondary Unit\n')
	start = perf_counter()
	now = perf_counter()-start
	try:			
		while True:
			now = perf_counter()-start
			meas = BM.readdata()
			s = '{:5.1f},{:s},{:s},{:s},{:s}'.format(
				now,
				meas[PRI_READING], meas[PRI_UNIT],
				meas[SEC_READING], meas[SEC_UNIT])
				
			f.write(s+'\n')
			print(s)
			elapsed = (perf_counter()-start) - now
			if elapsed < arg.int_time:
				sleep(arg.int_time - elapsed)
	except KeyboardInterrupt:
		f.close()			



