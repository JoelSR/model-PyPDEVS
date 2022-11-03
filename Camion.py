from pypdevs.DEVS import *
from scipy.stats import lognorm,weibull_min
import random

class CamionState:
	def __init__(self, current="listoPala"):
		self.set(current)

	def set(self, value="listoPala"):
		self.__state=value

	def get(self):
		return self.__state

	def __str__(self):
		return self.get()

class Camion(AtomicDEVS):
	def __init__(self,sQ,pQ,name=None,dispatcher=None):
		AtomicDEVS.__init__(self, name)
		self.state = CamionState("listoPala")
		
		self.adv_time = 0.0
		self.elapsed = 0.0

		# Variables para el proceso
		self.carga  = 0
		self.cargaT = 0
		self.stock  = 1

		self.out_load = {}
		self.notify   = {}

		# Despachador
		self.dispatcher = dispatcher

		# PORTS:
		#  Declare as many input and output ports as desired
		#  (usually store returned references in local variables):
		self.READY  = self.addInPort(name="READY")
		self.INLOAD = self.addInPort(name="INLOAD")
		for i in range(pQ):
			self.notify["pala_"+str(i)] = self.addOutPort(name="NOTIFY_PALA_"+str(i))
		for i in range(sQ):
			self.out_load["stock_"+str(i+1)] = self.addOutPort(name="OUTLOAD_STOCK_"+str(i+1))
		
		self.DATA = self.addOutPort(name="DATA")

	def intTransition(self):
		state = self.state.get()

		if state == "viajandoVacio":
			return CamionState("listoPala")
		elif state == "transportando":
			return CamionState("descargando")
		elif state == "descargando":
			self.carga = 0
			return CamionState("viajandoVacio")
		elif state == "listoPala":
			return CamionState("esperando")
		elif state == "ocupado":
			return CamionState("transportando")
		else:
			raise DEVSException(\
				"unknown state <%s> in CAMION internal transition function"\
				% state)
	
	def extTransition(self, inputs):
		"""
		External Transition Function
		"""
		inputLoad = inputs.get(self.INLOAD)

		if inputLoad[2] != 0:
			self.stock  = random.choice(list(inputLoad[2]))

		self.carga  = inputLoad[0]
		self.cargaT = inputLoad[1]
		
		return CamionState("ocupado")

	def timeAdvance(self):
		state = self.state.get()

		if state == "ocupado":
			return self.cargaT
		elif state == "listoPala":
			self.adv_time = 0.0
			return 0.0
		elif state == "esperando":
			self.adv_time = self.elapsed
			return float("inf")
		elif state == "transportando":
			self.adv_time = lognorm.rvs(2.19,loc=3.310,scale=0.7057,size=1)[0]
			return self.adv_time
		elif state == "descargando":
			self.adv_time = lognorm.rvs(1.38,loc=0.3742,scale=0.7050,size=1)[0]
			return self.adv_time
		elif state == "viajandoVacio":
			self.adv_time = lognorm.rvs(1.90,loc=3.050,scale=0.7120,size=1)[0]
			return self.adv_time

	def outputFnc(self):

		state = self.state.get()

		####nt(state)

		if(state == "listoPala"):
			pala = self.dispatcher.asignarPalaRR()
			return {self.notify[pala]: [self.name],
					self.DATA: [self.name,self.adv_time,self.state.get(),self.carga]}
		elif(state == "descargando"):
			stock = "stock_"+str(self.stock)
			return {self.out_load[stock]: [self.carga],
					self.DATA: [self.name,self.adv_time,self.state.get(),self.carga]}
		elif(state == "esperando"):
			return {self.DATA: [self.name,self.adv_time,self.state.get(),self.carga]}
		elif(state == "ocupado"):
			return {self.DATA: [self.name,self.adv_time,self.state.get(),self.carga]}
		elif(state == "transportando"):
			return {self.DATA: [self.name,self.adv_time,self.state.get(),self.carga]}
		elif(state == "viajandoVacio"):
			return {self.DATA: [self.name,self.adv_time,self.state.get(),self.carga]}
		else:
			raise DEVSException(\
				"unknown state <%s> in CAMION outputFnc"\
				% state)