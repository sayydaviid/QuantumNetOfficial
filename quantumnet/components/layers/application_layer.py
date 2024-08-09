
import networkx as nx
from quantumnet.components import Host
from quantumnet.objects import Qubit, Logger, Epr
from random import uniform, choice
import random

class ApplicationLayer:
    def __init__(self, network, network_layer, link_layer, physical_layer, transport_layer):
        self._network = network
        self._network_layer = network_layer
        self._link_layer = link_layer
        self._physical_layer = physical_layer
        self._transport_layer = transport_layer
        self.logger = Logger.get_instance()
    
    def prepara_qubits_e91(self, key, bases):
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
        results = []
        for qubit, base in zip(qubits, bases):
            if base == 1:
                qubit.apply_hadamard()
            measurement = qubit.measure()
            results.append(measurement)
        return results
    
    def qkd_e91_protocol(self, alice_id, bob_id, num_bits):
        alice = self._network.get_host(alice_id)
        bob = self._network.get_host(bob_id)
        
        num_qubits = int(num_bits * 1.5)  # 50% mais qubits do que o necessário
        
        while len(alice.memory) < num_qubits:
            self.logger.log(f'Qubits insuficientes. Requisitando mais {num_qubits - len(alice.memory)} qubits.')
            success = self._transport_layer.run_transport_layer(alice_id, bob_id, num_qubits - len(alice.memory))
            if not success:
                self.logger.log('Falha ao obter qubits adicionais. Tentativa novamente.')
                return False
        
        # Step 1: Alice prepares qubits
        key = [random.choice([0, 1]) for _ in range(num_qubits)]
        bases_alice = [random.choice([0, 1]) for _ in range(num_qubits)]
        qubits = self.prepara_qubits_e91(key, bases_alice)
        
        # Step 2: Bob chooses random bases and measures qubits
        bases_bob = [random.choice([0, 1]) for _ in range(num_qubits)]
        results_bob = self.apply_bases_and_measure_e91(qubits, bases_bob)
        
        # Step 3: Alice and Bob share their bases
        common_indices = [i for i in range(len(bases_alice)) if bases_alice[i] == bases_bob[i]]
        
        if not common_indices:
            self.logger.log("Nenhuma base em comum, tentativa novamente.")
            return False
        
        # Step 4: Extract the key based on common bases
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
