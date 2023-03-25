from fogbed import (
    Container, VirtualInstance, FogbedExperiment
)
from typing import List
import subprocess


class IotaBasic:
    def __init__(
        self,
        exp: FogbedExperiment,
        prefix: str = 'node'
    ) -> None:
        self.ledgers: List[VirtualInstance] = []
        self.nodes: List[Container] = []
        self.exp = exp
        self.prefix = prefix

    # def create_ledgers(self, number_nodes: int):
    #     self.ledgers = self._create_ledgers(number_nodes, self.prefix)
    #     self.nodes = self._create_nodes(self.prefix)
    #     return self.ledgers, self.nodes
    
    def create_ledger(self, prefix_node: str = 'node'):
        ledger = self._create_ledger(1, self.prefix)
        self.ledgers.append(ledger)
        node = self._create_node(prefix_node)
        self.nodes.append(node)
        return ledger, node

    def create_links(self, target: VirtualInstance, devices: List[VirtualInstance]):
        for device in devices:
            self.exp.add_link(device, target)

    # def _create_ledgers(self, number: int, prefix: str) -> List[VirtualInstance]:
    #     return [self.exp.add_virtual_instance(f'{prefix}{i+1}') for i in range(number)]

    def _create_ledger(self, prefix: str) -> List[VirtualInstance]:
        return self.exp.add_virtual_instance(f'{prefix}')

    def _create_node(self, prefix:str, ledger: VirtualInstance):
        self.cli_instance = self.exp.add_virtual_instance(f'{prefix}_cli')
        name = f'{prefix}-node'
        node = Container(
            name=name,
            dimage='gohornet/hornet:1.2.1'
        )
        self.exp.add_docker(
            container=node,
            datacenter=ledger)
        return node
    
    def _create_nodes(self, prefix:str):
        self.cli_instance = self.exp.add_virtual_instance(f'{prefix}')
        nodes = []
        for i, ledger in enumerate(self.ledgers):
            name = f'node{i+1}'
            node = Container(
                name=name,
                dimage='gohornet/hornet:1.2.1'
            )
            nodes.append(node)
            self.exp.add_docker(
                container=node,
                datacenter=ledger)
        return nodes
    
    def _create_node(self, prefix:str):
        self.cli_instance = self.exp.add_virtual_instance(f'{prefix}_cli')
        name = f'node{i+1}'
        node = Container(
            name=name,
            dimage='gohornet/hornet:1.2.1'
        )
        self.nodes.append(node)
        self.exp.add_docker(
            container=node,
            datacenter=ledger)
        return node

    def start_network(self):
        for node in self.nodes:
            node.start()
            node.cmd('tool ed25519-key > key-pair.txt')
        # node.cmd('tool ed25519-key > key-pair.txt')

        # ips = list(map(lambda node: node.ip, self.nodes))
        # count_nodes = len(self.nodes)
        # ips = ",".join(ips)
        # print(ips)
