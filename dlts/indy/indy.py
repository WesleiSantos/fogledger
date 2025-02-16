from fogbed import (
    Container, VirtualInstance, FogbedExperiment
)
from typing import List
import csv
import os
import uuid
import re
import numpy

class IndyBasic:
    def __init__(
        self,
        exp: FogbedExperiment,
        number_nodes: int = 4
    ) -> None:
        self.ledgers: List[VirtualInstance] = []
        self.nodes: List[Container]  = []
        self.number_nodes: int = number_nodes
        self.exp = exp
        self.genesis_file_path = ''
        

    def create_ledgers(self, prefix: str = 'node'):
        self.ledgers = self._create_ledgers(self.number_nodes, prefix)
        self.nodes = self._create_nodes(prefix)
        return self.ledgers, self.nodes

    def create_links(self,target: VirtualInstance, devices: List[VirtualInstance]) -> None:
        for device in devices:
            self.exp.add_link(device, target)

    def _create_ledgers(self, number: int, prefix: str) -> List[VirtualInstance]:
        return [self.exp.add_virtual_instance(f'{prefix}{i+1}') for i in range(number)]


    def _create_nodes(self, prefix: str):
        nodes = []

        # Cli to create seeds to nodes
        self.cli_instance = self.exp.add_virtual_instance(f'{prefix}_cli')
        self.indy_cli = Container(
            name=f'{prefix}_cli', 
            dimage='mnplima/fogbed-indy-cli',
            volumes=[f'{os.path.abspath("indy/scripts/")}:/opt/indy/scripts/']
            )
        self.exp.add_docker(
                container=self.indy_cli,
                datacenter=self.cli_instance)
        for i, ledger in enumerate(self.ledgers):
            name = f'{prefix}{i+1}'
            node = Container(
                    name=name, 
                    dimage='mnplima/fogbed-indy-node',
                    volumes=[f'{os.path.abspath("indy/scripts/")}:/opt/indy/scripts/', f'{os.path.abspath("indy/tmp/trustees.csv")}:/tmp/indy/trustees.csv']
                )
            nodes.append(node)
            self.exp.add_docker(
                container=node,
                datacenter=ledger)
        return nodes

        

    def start_network(self) -> None:
        self.indy_cli.cmd(f"printf 'wallet create fogbed key=key \nexit\n' | indy-cli")
        genesis_file_name = uuid.uuid4()
        array_genesis = numpy.array([['Steward name','Validator alias','Node IP address','Node port','Client IP address','Client port','Validator verkey','Validator BLS key','Validator BLS POP','Steward DID','Steward verkey']])
        for i, node in enumerate(self.nodes):
            seed = self.indy_cli.cmd("pwgen -s 32 1")
            info_cli = self.indy_cli.cmd(f"printf 'wallet open fogbed key=key\n did new seed={seed}\nexit\n' | indy-cli")
            matches = re.findall(r'Did "(\S+)" has been created with "(\S+)" verkey', info_cli)
            did = ''
            verkey = ''
            if matches:
                did = matches[0][0]
                verkey = matches[0][1]
            aux = node.cmd(f'init_indy_node {node.name} {node.ip} 9701 {node.ip} 9702')
            lines = aux.splitlines()
            array_genesis = numpy.append(array_genesis,[[node.name,node.name,node.ip,9701,node.ip,9702,lines[5].split(' ')[3], lines[9].split(' ')[4], lines[10].split(' ')[7], did, verkey]], axis=0)
        rows = ["{},{},{},{},{},{},{},{},{},{},{}".format(a,b,c,d,e,f,g,h,i,j,k) for a,b,c,d,e,f,g,h,i,j,k in array_genesis]
        text= "\n".join(rows)
        self.genesis_file_path = f'indy/tmp/{genesis_file_name}.csv'
        numpy.savetxt(self.genesis_file_path, array_genesis, delimiter=',', fmt='%s')
        for i, node in enumerate(self.nodes):
            print(node.cmd(f'echo "{text}" >> /tmp/indy/{genesis_file_name}.csv'))
            print(node.cmd(f'/opt/indy/scripts/genesis_from_files.py --stewards /tmp/indy/{genesis_file_name}.csv --trustees /tmp/indy/trustees.csv'))
            node.cmd(f'cp domain_transactions_genesis /var/lib/indy/$NETWORK_NAME/ && cp pool_transactions_genesis /var/lib/indy/$NETWORK_NAME/')
            node.cmd(f'start_indy_node {node.name} {node.ip} 9701 {node.ip} 9702 > output.log 2>&1 &')
    
    def request_genesis_file(self) -> str:
        genesis_file = open(self.genesis_file_path, 'r')
        data = genesis_file.read()
        genesis_file.close()
        return data