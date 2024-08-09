import networkx as nx
from quantumnet.components import Host
from quantumnet.objects import Logger, Epr
from random import uniform

class LinkLayer:
    def __init__(self, network, physical_layer):
        """
        Inicializa a camada de enlace.
        
        args:
            network : Network : Rede.
            physical_layer : PhysicalLayer : Camada física.
        """
        self._network = network
        self._physical_layer = physical_layer
        self._requests = []
        self._failed_requests = []
        self.logger = Logger.get_instance()

    @property
    def requests(self):
        return self._requests

    @property
    def failed_requests(self):
        return self._failed_requests

    def __str__(self):
        """ Retorna a representação em string da camada de enlace. 
        
        returns:
            str : Representação em string da camada de enlace."""
        return f'Link Layer'
    
    def request(self, alice_id: int, bob_id: int):
        """
        request: Solicitação de criação de emaranhamento entre Alice e Bob.
        
        args:
            alice_id : int : Id do host Alice.
            bob_id : int : Id do host Bob.
        """
        alice = self._network.get_host(alice_id)
        bob = self._network.get_host(bob_id)
        
        # Tentar criar emaranhamento até duas vezes
        for attempt in range(1, 3):
            entangle = self._physical_layer.entanglement_creation_heralding_protocol(alice, bob)
            if entangle:
                self._requests.append((alice_id, bob_id))
                self.logger.log(f'Entrelaçamento criado entre {alice} e {bob} na tentativa {attempt}.')
                #print(f'Entrelaçamento criado entre {alice} e {bob} na tentativa {attempt}.')
                return True
            else:
                self.logger.log(f'Entrelaçamento falhou entre {alice} e {bob} na tentativa {attempt}.')
                self._failed_requests.append((alice_id, bob_id))
                self.purification(alice_id, bob_id)
                #print(f'Entrelaçamento falhou entre {alice} e {bob} na tentativa {attempt}.')
                
    def purification_calculator(self, f1: int, f2: int, purification_type: int) -> float:
        """
        Cálculo das fórmulas de purificação
        1 - Deafult
        2 - BBPSSW Protocol
        3 - DEJMPS Protocol
        
        args:
            f1: int
            f2: int
            purification_type: int : Fórmula escolhida
        """
        
        f1f2 = f1*f2

        type_1 = (f1f2) / ((f1f2) + ((1 - f1) * (1 - f2)))
        if purification_type == 1:
            self.logger.log(f'A purificação ultilizada foi tipo 1')
            return type_1 
        
        elif purification_type == 2:
            type_2 = (f1f2 + ((1-f1) / 3) * ((1-f2) / 3)) / ((f1f2 + f1*((1-f2)/3) + f2*((1-f1)/3) + 5*((1-f1)/3)*((1-f2)/3)))
            self.logger.log(f'A purificação ultilizada foi tipo 2')
            return type_2
        
        elif purification_type == 3:
            type_3 = ((2*f1f2 + 1 - f1 - f2) / ((1/4)*(f1 + f2 - f1f2) + 3/4))
            self.logger.log(f'A purificação ultilizada foi tipo 3')
            return type_3
        
        print("Purificação só pode aceitar os valores (1, 2 ou 3), a fórmula 1 foi escolhida por padrão")
        return type_1 


    def purification(self, alice_id: int, bob_id: int, purification_type: int = 1):
        """
        Purificação de EPRs
        
        args:
            alice_id : int : Id do host Alice.
            bob_id : int : Id do host Bob.
            purification_type : int : Tipo de protocolo de purificaçã́o
        """
        eprs_fail = self._physical_layer.failed_eprs
        # print(eprs_fail)
        
        if len(eprs_fail) < 2:
            self.logger.log(f'Não há EPRs suficientes para purificação no canal ({alice_id}, {bob_id}).')
            return False

        eprs_fail1 = eprs_fail[-1]
        eprs_fail2 = eprs_fail[-2]
        f1 = eprs_fail1.get_current_fidelity()
        f2 = eprs_fail2.get_current_fidelity()
        epr_two = (alice_id,bob_id)

        purification_prob = (f1 * f2) + ((1 - f1) * (1 - f2))

        if purification_prob > 0.5:
            new_fidelity = self.purification_calculator(f1, f2, purification_type)

            # print(new_fidelity)
            if new_fidelity > 0.8:  # Verifica se a nova fidelidade é maior que 0.8
                epr_purified = Epr(epr_two, new_fidelity)
                self._network.physical.add_epr_to_channel(epr_purified, (alice_id, bob_id))
                self._physical_layer.failed_eprs.remove(eprs_fail1)
                self._physical_layer.failed_eprs.remove(eprs_fail2)
                self.logger.log(f'Purificação bem sucedida no canal ({alice_id}, {bob_id}) com nova fidelidade {new_fidelity}.')
                return True
            else:
                self._physical_layer.failed_eprs.remove(eprs_fail1)
                self._physical_layer.failed_eprs.remove(eprs_fail2)
                self.logger.log(f'Purificação falhou no canal ({alice_id}, {bob_id}) devido a baixa fidelidade após purificação.')
                return False
        else:
            self._physical_layer.failed_eprs.remove(eprs_fail1)
            self._physical_layer.failed_eprs.remove(eprs_fail2)
            self.logger.log(f'Purificação falhou no canal ({alice_id}, {bob_id}) devido a baixa fidelidade após purificação {purification_prob}.1')

 
    

