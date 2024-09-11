import networkx as nx
from quantumnet.components import Host
from quantumnet.objects import Logger, Epr
from random import uniform

class TransportLayer:
    def __init__(self, network, network_layer, link_layer, physical_layer):
        """
        Inicializa a camada de transporte.
        
        args:
            network : Network : Rede.
            network_layer : NetworkLayer : Camada de rede.
            link_layer : LinkLayer : Camada de enlace.
            physical_layer : PhysicalLayer : Camada física.
        """
        self._network = network
        self._physical_layer = physical_layer
        self._network_layer = network_layer
        self._link_layer = link_layer
        self.logger = Logger.get_instance()
        self.transmitted_qubits = []
        self.used_eprs = 0
        self.used_qubits = 0
        self.created_eprs = []  # Lista para armazenar EPRs criados

    def __str__(self):
        """ Retorna a representação em string da camada de transporte. 
        
        returns:
            str : Representação em string da camada de transporte."""
        return f'Transport Layer'
    
    def get_used_eprs(self):
        self.logger.debug(f"Eprs usados na camada {self.__class__.__name__}: {self.used_eprs}")
        return self.used_eprs
    
    def get_used_qubits(self):
        self.logger.debug(f"Qubits usados na camada {self.__class__.__name__}: {self.used_qubits}")
        return self.used_qubits
    
    def request_transmission(self, alice_id: int, bob_id: int, num_qubits: int):
        """
        Requisição de transmissão de n qubits entre Alice e Bob.
        
        args:
            alice_id : int : Id do host Alice.
            bob_id : int : Id do host Bob.
            num_qubits : int : Número de qubits a serem transmitidos.
            
        returns:
            bool : True se a transmissão foi bem-sucedida, False caso contrário.
        """
        alice = self._network.get_host(alice_id)
        available_qubits = len(alice.memory)

        if available_qubits < num_qubits:
            self.logger.log(f'Número insuficiente de qubits na memória de Alice (Host:{alice_id}). Tentando transmitir os {available_qubits} qubits disponíveis.')
            num_qubits = available_qubits

        if num_qubits == 0:
            self.logger.log(f'Nenhum qubit disponível na memória de Alice ({alice_id}) para transmissão.')
            return False

        max_attempts = 2
        attempts = 0
        success = False

        while attempts < max_attempts and not success:
            self._network.timeslot()  # Incrementa o timeslot para cada tentativa de transmissão
            self.logger.log(f'Timeslot {self._network.get_timeslot()}: Tentativa de transmissão {attempts + 1} entre {alice_id} e {bob_id}.')
            
            routes = []
            for _ in range(num_qubits):
                route = self._network_layer.short_route_valid(alice_id, bob_id)
                if route is None:
                    self.logger.log(f'Não foi possível encontrar uma rota válida na tentativa {attempts + 1}. Timeslot: {self._network.get_timeslot()}')
                    break
                routes.append(route)
            
            if len(routes) == num_qubits:
                success = True
                for route in routes:
                    for i in range(len(route) - 1):
                        node1 = route[i]
                        node2 = route[i + 1]
                        # Verifica se há pelo menos um par EPR disponível no canal
                        if len(self._network.get_eprs_from_edge(node1, node2)) < 1:
                            self.logger.log(f'Falha ao encontrar par EPR entre {node1} e {node2} na tentativa {attempts + 1}. Timeslot: {self._network.get_timeslot()}')
                            success = False
                            break
                    if not success:
                        break
            
            if not success:
                attempts += 1

        if success:
            # Registrar os qubits transmitidos
            for route in routes:
                qubit_info = {
                    'route': route,
                    'alice_id': alice_id,
                    'bob_id': bob_id,
                }
                self.transmitted_qubits.append(qubit_info)
            self.logger.log(f'Transmissão de {num_qubits} qubits entre {alice_id} e {bob_id} concluída com sucesso. Timeslot: {self._network.get_timeslot()}')
            return True
        else:
            self.logger.log(f'Falha na transmissão de {num_qubits} qubits entre {alice_id} e {bob_id} após {attempts} tentativas. Timeslot: {self._network.get_timeslot()}')
            return False

    def teleportation_protocol(self, alice_id: int, bob_id: int):
        """
        Realiza o protocolo de teletransporte de um qubit de Alice para Bob.
        
        args:
            alice_id : int : Id do host Alice.
            bob_id : int : Id do host Bob.
        
        returns:
            bool : True se o teletransporte foi bem-sucedido, False caso contrário.
        """
        self._network.timeslot()  # Incrementa o timeslot para o protocolo de teletransporte
        self.logger.log(f'Timeslot {self._network.get_timeslot()}: Iniciando teletransporte entre {alice_id} e {bob_id}.')
        
        # Estabelece uma rota válida
        route = self._network_layer.short_route_valid(alice_id, bob_id)
        if route is None:
            self.logger.log(f'Não foi possível encontrar uma rota válida para teletransporte entre {alice_id} e {bob_id}. Timeslot: {self._network.get_timeslot()}')
            return False
        
        # Pega um qubit de Alice e um qubit de Bob
        alice = self._network.get_host(alice_id)
        bob = self._network.get_host(bob_id)
        
        if len(alice.memory) < 1 or len(bob.memory) < 1:
            self.logger.log(f'Alice ou Bob não possuem qubits suficientes para teletransporte. Timeslot: {self._network.get_timeslot()}')
            return False
        
        qubit_alice = alice.memory.pop(0)  # Remove o primeiro qubit da memória de Alice
        qubit_bob = bob.memory.pop()       # Remove o último qubit da memória de Bob
        
        # Calcula a fidelidade final do teletransporte
        f_alice = qubit_alice.get_current_fidelity()
        f_bob = qubit_bob.get_current_fidelity()
        
        # Assume fidelidade do link como a média das fidelidades dos pares EPR na rota
        fidelities = []
        for i in range(len(route) - 1):
            epr_pairs = self._network.get_eprs_from_edge(route[i], route[i+1])
            fidelities.extend([epr.get_current_fidelity() for epr in epr_pairs])
        
        if not fidelities:
            self.logger.log(f'Não foi possível encontrar pares EPR na rota entre {alice_id} e {bob_id}. Timeslot: {self._network.get_timeslot()}')
            return False
        
        f_route = sum(fidelities) / len(fidelities)
        
        # Fidelidade final do qubit teletransportado
        F_final = f_alice * f_bob * f_route + (1 - f_alice) * (1 - f_bob) * (1 - f_route)
        
        qubit_info = {
            'alice_id': alice_id,
            'bob_id': bob_id,
            'route': route,
            'fidelity_alice': f_alice,
            'fidelity_bob': f_bob,
            'fidelity_route': f_route,
            'F_final': F_final,
            'qubit_alice': qubit_alice,
            'qubit_bob': qubit_bob,
            'success': True
        }
        
        # Adiciona o qubit teletransportado à memória de Bob com a fidelidade final calculada
        qubit_alice.fidelity = F_final
        bob.memory.append(qubit_alice)
        self.logger.log(f'Teletransporte de qubit de {alice_id} para {bob_id} foi bem-sucedido com fidelidade final de {F_final}. Timeslot: {self._network.get_timeslot()}')
        
        # Par virtual é deletado no final
        for i in range(len(route) - 1):
            self._network.remove_epr(route[i], route[i + 1])
        
        self.transmitted_qubits.append(qubit_info)
        return True

    def avg_fidelity_on_transportlayer(self):
        """
        Calcula a fidelidade média dos EPRs usados na camada de transporte.

        returns:
            float : Fidelidade média dos EPRs usados na camada de transporte.
        """
        total_fidelity = 0
        total_eprs = 0

        # Percorre todas as rotas dos qubits transmitidos na camada de transporte
        for qubit_info in self.transmitted_qubits:
            route = qubit_info['route']
            
            # Percorre a rota do qubit transmitido e soma a fidelidade dos EPRs
            for i in range(len(route) - 1):
                epr_pairs = self._network.get_eprs_from_edge(route[i], route[i + 1])
                
                if epr_pairs:
                    # Soma as fidelidades de todos os EPRs na rota
                    for epr in epr_pairs:
                        total_fidelity += epr.get_current_fidelity()
                        total_eprs += 1
                        self.logger.log(f'Fidelidade do EPR na rota {route[i]} -> {route[i + 1]}: {epr.get_current_fidelity()}')
                else:
                    self.logger.log(f'Nenhum EPR encontrado entre {route[i]} e {route[i + 1]}.')

        # Se não houver EPRs, retorna 0
        if total_eprs == 0:
            self.logger.log('Nenhum EPR foi utilizado na camada de transporte.')
            return 0.0

        # Calcula a fidelidade média
        avg_fidelity = total_fidelity / total_eprs
        self.logger.log(f'A fidelidade média dos EPRs na camada de transporte é {avg_fidelity}')
        
        return avg_fidelity

    
    def get_transmitted_qubits(self):
        """
        Retorna a lista de qubits transmitidos.
        
        returns:
            list : Lista de dicionários contendo informações dos qubits transmitidos.
        """
        return self.transmitted_qubits

    def get_teleported_qubits(self):
        """
        Retorna a lista de qubits teletransportados.
        
        returns:
            list : Lista de dicionários contendo informações dos qubits teletransportados.
        """
        return self.transmitted_qubits
    
    def run_transport_layer(self, alice_id: int, bob_id: int, num_qubits: int):
        """
        Executa a requisição de transmissão e o protocolo de teletransporte.

        args:
            alice_id : int : Id do host Alice.
            bob_id : int : Id do host Bob.
            num_qubits : int : Número de qubits a serem transmitidos.

        returns:
            bool : True se a operação foi bem-sucedida, False caso contrário.
        """
        alice = self._network.get_host(alice_id)
        bob = self._network.get_host(bob_id)
        available_qubits = len(alice.memory)

        # Se Alice tiver menos qubits do que o necessário, crie mais qubits
        if available_qubits < num_qubits:
            self.logger.log(f'Número insuficiente de qubits na memória de Alice (Host {alice_id}). Criando mais qubits para completar os {num_qubits} necessários.')
            
            # Cria qubits suficientes para completar a transmissão
        qubits_needed = num_qubits - available_qubits
        for _ in range(qubits_needed):
            self._network.timeslot()  # Incrementa o timeslot a cada criação de qubit
            self.logger.log(f"Timeslot antes da criação do qubit: {self._network.get_timeslot()}")
            self._physical_layer.create_qubit(alice_id)  # Cria novos qubits para Alice
            self.logger.log(f"Qubit criado para Alice (Host {alice_id}) no timeslot: {self._network.get_timeslot()}")
        available_qubits = len(alice.memory)  # Atualiza a quantidade de qubits disponíveis após a criação
            
        self.logger.log(f'{qubits_needed} qubits criados para Alice (Host {alice_id}). Alice agora possui {available_qubits} qubits na memória.')

        # Verifica se ainda há qubits suficientes
        if available_qubits < num_qubits:
            self.logger.log(f'Mesmo após a criação, não há qubits suficientes na memória de Alice ({alice_id}) para transmissão.')
            return False

        max_attempts = 2
        attempts = 0
        success = False
        routes = []

        while attempts < max_attempts and not success:
            routes.clear()
            for _ in range(num_qubits):
                route = self._network_layer.short_route_valid(alice_id, bob_id)
                if route is None:
                    self.logger.log(f'Não foi possível encontrar uma rota válida na tentativa {attempts + 1}. Timeslot: {self._network.get_timeslot()}')
                    break
                routes.append(route)
            
            if len(routes) == num_qubits:
                success = True
                for route in routes:
                    for i in range(len(route) - 1):
                        node1 = route[i]
                        node2 = route[i + 1]
                        if len(self._network.get_eprs_from_edge(node1, node2)) < 1:
                            self.logger.log(f'Falha ao encontrar par EPR entre {node1} e {node2} na tentativa {attempts + 1}. Timeslot: {self._network.get_timeslot()}')
                            success = False
                            break
                    if not success:
                        break
            
            if not success:
                attempts += 1

        if success:
            success_count = 0
            for route in routes:
                if len(alice.memory) < 1:
                    self.logger.log(f'Alice não possui qubits suficientes para teletransporte.')
                    continue

                qubit_alice = alice.memory.pop(0)
                f_alice = qubit_alice.get_current_fidelity()

                fidelities = []
                for i in range(len(route) - 1):
                    epr_pairs = self._network.get_eprs_from_edge(route[i], route[i + 1])
                    fidelities.extend([epr.get_current_fidelity() for epr in epr_pairs])

                if not fidelities:
                    self.logger.log(f'Não foi possível encontrar pares EPR na rota {route}. Timeslot: {self._network.get_timeslot()}')
                    continue

                f_route = sum(fidelities) / len(fidelities)
                F_final = f_alice * f_route

                bob.memory.append(qubit_alice)
                success_count += 1
                self._network.timeslot()  # Incrementa o timeslot para cada teletransporte bem-sucedido
                self.used_qubits += 1
                self.logger.log(f'Teletransporte de qubit de {alice_id} para {bob_id} na rota {route} foi bem-sucedido com fidelidade final de {F_final}. Timeslot: {self._network.get_timeslot()}')

            if success_count == num_qubits:
                self.logger.log(f'Transmissão e teletransporte de {num_qubits} qubits entre {alice_id} e {bob_id} concluídos com sucesso. Timeslot: {self._network.get_timeslot()}')
                return True
            else:
                self.logger.log(f'Falha na transmissão e teletransporte de {num_qubits} qubits entre {alice_id} e {bob_id}. Apenas {success_count} qubits foram teletransportados com sucesso. Timeslot: {self._network.get_timeslot()}')
                return False
        else:
            self.logger.log(f'Falha na transmissão de {num_qubits} qubits entre {alice_id} e {bob_id} após {attempts} tentativas. Timeslot: {self._network.get_timeslot()}')
            return False


