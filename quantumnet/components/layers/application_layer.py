
import networkx as nx
from quantumnet.components import Host
from quantumnet.objects import Qubit, Logger, Epr
from random import uniform, choice
import random

class ApplicationLayer:
    def __init__(self, network, transport_layer, network_layer, link_layer, physical_layer):
        """
        Inicializa a camada de Aplicação.
        
        args:
            network : Network : Rede.
            network_layer : NetworkLayer : Camada de rede.
            link_layer : LinkLayer : Camada de enlace.
            physical_layer : PhysicalLayer : Camada física.
            transport_layer : TransportLayer : Camada de transporte.
        """
        self._network = network
        self._physical_layer = physical_layer
        self._network_layer = network_layer
        self._link_layer = link_layer
        self._transport_layer = transport_layer 
        self.logger = Logger.get_instance()
    
    def __str__(self):
        """ Retorna a representação em string da camada de aplicação. 
        
        returns:
            str : Representação em string da camada de aplicação."""
        return f'Application Layer'
    

    def prepara_qubits_e91(self, key, bases):
        """
        Prepara os qubits para o protocolo E91, aplicando operações baseadas na chave (bit) e na base de medição.

        Args:
            key : Lista de bits que representam a chave que Alice quer enviar.
            bases : Lista de bases (0 ou 1) que indica qual base (computacional ou Hadamard) deve ser usada para preparar cada qubit.
        
        Returns:
            pairs : Lista de qubits preparados, prontos para serem enviados a Bob.
        
        """
        pairs = []
        for bit, base in zip(key, bases):
            qubit = Qubit(qubit_id=random.randint(0, 1000))
            if bit == 1:
                qubit.apply_x()
            if base == 1:
                qubit.apply_hadamard()
            pairs.append(qubit)
        return pairs
    
    def apply_bases_and_measure_e91(self, qubits, bases):
        """
        Aplica bases de medição aos qubits e mede seus valores, simulando o processo de medição por Bob.

        Args:
            qubits :  Lista de qubits enviados por Alice.
            bases : Lista de bases (0 ou 1) que indica qual base Bob deve usar para medir cada qubit.

        Returns:
            results : Lista de resultados de medição para cada qubit.
        """
        results = []
        for qubit, base in zip(qubits, bases):
            if base == 1:
                qubit.apply_hadamard()
            measurement = qubit.measure()
            results.append(measurement)
        return results
    
    def qkd_e91_protocol(self, alice_id, bob_id, num_bits):
        """
        Protocolo de Distribuição de Chave Quântica (QKD) usando o protocolo E91.

        Args: 
            alice_id : Identificador do host de Alice.
            bob_id : Identificador do host de Bob.
            num_bits : Número de bits necessários na chave final.

        Returns:
            True : Se o protocolo for bem-sucedido e a chave for compartilhada corretamente.
            False : Se ocorrer algum erro durante a execução do protocolo.
        
        """
        alice = self._network.get_host(alice_id)
        bob = self._network.get_host(bob_id)
        
        num_qubits = int(num_bits * 1.5)  # 50% mais qubits do que o necessário
        
        while len(alice.memory) < num_qubits:
            print(alice.memory)
            self.logger.log(f'Qubits insuficientes. Requisitando mais {num_qubits - len(alice.memory)} qubits.')
            success = self._transport_layer.run_transport_layer(alice_id, bob_id, num_qubits - len(alice.memory))
            if not success:
                self.logger.log('Falha ao obter qubits adicionais. Tentativa novamente.')
                return False
        
        # Passo 1: Alice prepares qubits
        key = [random.choice([0, 1]) for _ in range(num_qubits)]
        bases_alice = [random.choice([0, 1]) for _ in range(num_qubits)]
        qubits = self.prepara_qubits_e91(key, bases_alice)
        
        # Passo 2: Bob chooses random bases and measures qubits
        bases_bob = [random.choice([0, 1]) for _ in range(num_qubits)]
        results_bob = self.apply_bases_and_measure_e91(qubits, bases_bob)
        
        # Passo 3: Alice and Bob share their bases
        common_indices = [i for i in range(len(bases_alice)) if bases_alice[i] == bases_bob[i]]
        
        if not common_indices:
            self.logger.log("Nenhuma base em comum, tentativa novamente.")
            return False
        
        # Passo 4: Extrai a chave das bases em comum
        shared_key_alice = [key[i] for i in common_indices]
        shared_key_bob = [results_bob[i] for i in common_indices]
        
        if shared_key_alice == shared_key_bob and len(shared_key_alice) >= num_bits:
            final_key = shared_key_alice[:num_bits]
            self.logger.log(f"Protocolo E91 bem-sucedido. Chave compartilhada: {final_key}")
            return True
        else:
            self.logger.log("As chaves não coincidem ou chave insuficiente. Tentativa novamente.")
            return False



# class ApplicationLayer:
#     def __init__(self, network, network_layer, link_layer, physical_layer, transport_layer):
#         self._network = network
#         self._network_layer = network_layer
#         self._link_layer = link_layer
#         self._physical_layer = physical_layer
#         self._transport_layer = transport_layer
#         self.logger = Logger.get_instance()
    
#     def prepara_qubits_e91(self, key, bases):
#         pairs = []
#         for bit, base in zip(key, bases):
#             qubit = Qubit(qubit_id=random.randint(0, 1000))
#             if bit == 1:
#                 qubit.apply_x()
#             if base == 1:
#                 qubit.apply_hadamard()
#             pairs.append(qubit)
#         return pairs
    
#     def apply_bases_and_measure_e91(self, qubits, bases):
#         results = []
#         for qubit, base in zip(qubits, bases):
#             if base == 1:
#                 qubit.apply_hadamard()
#             measurement = qubit.measure()
#             results.append(measurement)
#         return results
    
#     def qkd_e91_protocol(self, alice_id, bob_id, num_bits):
#         alice = self._network.hosts[alice_id]
#         bob = self._network.hosts[bob_id]
        
#         num_qubits = int(num_bits * 1.5)  # 50% mais qubits do que o necessário
        
#         while len(alice.memory) < num_qubits:
#             self.logger.log(f'Qubits insuficientes. Requisitando mais {num_qubits - len(alice.memory)} qubits.')
#             success = self._transport_layer.request_transmission(alice_id, bob_id, num_qubits - len(alice.memory))
#             if not success:
#                 self.logger.log('Falha ao obter qubits adicionais. Tentativa novamente.')
#                 return False
        
#         # Step 1: Alice prepares qubits
#         key = [random.choice([0, 1]) for _ in range(num_qubits)]
#         bases_alice = [random.choice([0, 1]) for _ in range(num_qubits)]
#         qubits = self.prepara_qubits_e91(key, bases_alice)
        
#         # Step 2: Bob chooses random bases and measures qubits
#         bases_bob = [random.choice([0, 1]) for _ in range(num_qubits)]
#         results_bob = self.apply_bases_and_measure_e91(qubits, bases_bob)
        
#         # Step 3: Alice and Bob share their bases
#         common_indices = [i for i in range(len(bases_alice)) if bases_alice[i] == bases_bob[i]]
        
#         if not common_indices:
#             self.logger.log("Nenhuma base em comum, tentativa novamente.")
#             return False
        
#         # Step 4: Extract the key based on common bases
#         shared_key_alice = [key[i] for i in common_indices]
#         shared_key_bob = [results_bob[i] for i in common_indices]
        
#         if shared_key_alice == shared_key_bob and len(shared_key_alice) >= num_bits:
#             final_key = shared_key_alice[:num_bits]
#             self.logger.log(f"Protocolo E91 bem-sucedido. Chave compartilhada: {final_key}")
#             return True
#         else:
#             self.logger.log("As chaves não coincidem ou chave insuficiente. Tentativa novamente.")
#             return False
