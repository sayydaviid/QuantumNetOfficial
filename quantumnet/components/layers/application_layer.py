import networkx as nx
from quantumnet.components import Host
from quantumnet.objects import Logger, Epr
from random import uniform

class ApplicationLayer():
    def __init__(self, network, network_layer, link_layer, physical_layer,transport_layer):
        """
        Inicializa a camada de aplicação.
        
        args:
            network : Network : Rede.
            network_layer : NetworkLayer : Camada de rede.
            link_layer : LinkLayer : Camada de enlace.
            physical_layer : PhysicalLayer : Camada física.
            trasnsport_layer: TransportLayer : Camada de Transporte
        """
        self._network = network
        self._network_layer = network_layer
        self._link_layer = link_layer
        self._physical_layer = physical_layer
        self._transport_layer = transport_layer
        self.logger = Logger.get_instance()       
    
    def __str__(self):
        """ Retorna a representação em string da camada de aplicação.
        
        returns:
            str : Representação em string da camada de aplicação."""
        return f'Aplication Layer'


pass


