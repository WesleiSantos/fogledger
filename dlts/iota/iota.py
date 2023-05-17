from fogbed import (
    Container, VirtualInstance, FogbedExperiment
)
from typing import List
from typing import Dict
import os
import json
import time

class IotaBasic:
    def __init__(
        self,
        exp: FogbedExperiment,
        prefix: str = 'cloud'
    ) -> None:
        self.ledgers: List[VirtualInstance] = []
        self.nodes: Dict[str, Container] = {}
        self.exp = exp
        self.prefix = prefix

    def add_ledger(self, prefix: str, nodes: List[Container]):
        ledger = self.exp.add_virtual_instance(f'{prefix}')
        self._create_nodes(ledger, nodes)
        self.ledgers.append(ledger)
        return self.ledgers
    
    def _create_nodes(self, ledger: VirtualInstance, nodes: List[Container]):
        for node in nodes:
            self.exp.add_docker(
                container=node,
                datacenter=ledger)
            self.nodes[f'{self.prefix}_{ledger.label}_{node.name}'] = node
        return nodes
    
    @staticmethod
    def write_file(file_path, file_name, text):
        with open(file_path + '/' + file_name, 'w') as file:
            file.write(text)

    @staticmethod
    def create_peer_conf_file(peer_conf_file, peerIp, peerName, peerID):
        with open(peer_conf_file, "r") as f:
            data = json.load(f)
        data["peers"].append({"alias": peerName, "multiAddress": f"/dns/{peerIp}/tcp/15600/p2p/{peerID}"})
        with open(peer_conf_file, "w") as f:
            json.dump(data, f, indent=4)

    @staticmethod
    def setCooPublicKey(public_key, file_path):
        with open(file_path, 'r') as f:
            file_contents = f.read()
            file_contents = file_contents.replace('"key": "{}"'.format(file_contents.split(
                '"key": "')[1].split('"')[0]), '"key": "{}"'.format(public_key))
        with open(file_path, 'w') as f:
            f.write(file_contents)

    def searchNode(self, node_name:str):
        for node in self.nodes.values():
            if node.name == node_name:
                return node

    # P2P identities are generated for each node
    def setupIdentities(self):
        print("\nGenerating P2P identities for each node")
        for node in self.nodes.values():
            nodeIdentity = node.cmd(f'./hornet tool p2pidentity-gen > {node.name}.identity.txt && cat {node.name}.identity.txt')
            arq_name = f'{node.name}.identity.txt'
            path = os.path.abspath('iota')
            IotaBasic.write_file(path, arq_name, nodeIdentity)
        print("P2P identities generated! ✅")
    
    # Extracts the peerID from the identity file
    def extractPeerID(self):
        print("\nExtracting peerID from the identity file")
        for node_ext in self.nodes.values():
            peerID = node_ext.cmd(
            f'cat {node_ext.name}.identity.txt | awk -F : \'{{if ($1 ~ /PeerID/) print $2}}\' | sed "s/ \+//g" | tr -d "\n" | tr -d "\r"').strip("> >")
            for node_int in self.nodes.values():
                if node_int.name != node_ext.name:
                    IotaBasic.create_peer_conf_file(os.path.abspath(f'iota/config/peering-{node_int.name}.json'),node_ext.ip, node_ext.name, peerID)        
        print("peerID extracted! ✅")

    # We need this so that the peering can be properly updated
    def setPermissions(self):
        if not os.uname()[0] == 'Darwin':
            print("\nSetting permissions for the peering files")
            for node in self.nodes.values():
                path =  os.path.abspath(f"iota/config/peering-{node.name}.json")
                if os.path.exists(path):
                    os.system(f'sudo chown 65532:65532 {os.path.abspath(f"iota/config/peering-{node.name}.json")}')
            print("Permissions set! ✅")
    
    #Sets the Coordinator up by creating a key pair
    def setupCoordinator(self):
        print("\nSetting up the Coordinator")
        coo_key_pair_file="coo-milestones-key-pair.txt"
        coo = self.searchNode("coo")
        if coo is not None:
            coo.cmd(f'./hornet tool ed25519-key > {coo_key_pair_file}')
            COO_PRV_KEYS = coo.cmd(f'cat {coo_key_pair_file} | awk -F : \'{{if ($1 ~ /private key/) print $2}}\' | sed "s/ \+//g" | tr -d "\n" | tr -d "\r"').strip("> >")
            coo.cmd(f'export COO_PRV_KEYS={COO_PRV_KEYS}')
            coo_public_key= coo.cmd(f'cat {coo_key_pair_file} | awk -F : \'{{if ($1 ~ /public key/) print $2}}\' | sed "s/ \+//g" | tr -d "\n" | tr -d "\r"').strip("> >")
            os.system(f'echo {coo_public_key} > {os.path.abspath("iota/coo-milestones-public-key.txt")}'.format(coo_public_key))
            for node in self.nodes.values():
               IotaBasic.setCooPublicKey(coo_public_key, os.path.abspath(f"iota/config/config-{node.name}.json"))
            print("Coordinator set up! ✅")
        else:
            print("Coordinator not found! ❌")

    # Bootstraps the coordinator
    def bootstrapCoordinator(self):
        print("Bootstrapping the Coordinator...")
        # Need to do it again otherwise the coo will not bootstrap
        if not os.uname()[0] == 'Darwin':
            os.system(f'sudo chown 65532:65532 {os.path.abspath("iota/p2pstore")}')
        coo = self.searchNode("coo")
        if coo is not None:
            coo.cmd(f'./hornet --cooBootstrap --cooStartIndex 0 > coo.bootstrap.log &')
            print("Waiting for $bootstrap_tick seconds ... ⏳")
            time.sleep(30)
            bootstrapped = coo.cmd('grep "milestone issued (1)" coo.bootstrap.log | cat')
            if(bootstrapped):
                print("Coordinator bootstrapped successfully! ✅")
                coo.cmd(f'pkill -f "hornet --cooBootstrap --cooStartIndex 0"')
                coo.cmd('rm ./coo.bootstrap.container')
                time.sleep(10)
            else:
                print("Error. Coordinator has not been boostrapped.")
        else:
            print("Coordinator not found! ❌")

    def startContainers(self):
        print("Starting the containers...")
        for node in self.nodes.values():
            node.cmd(f'./hornet > {node.name}.log &')
            print(f"Starting {node.name}... ⏳")
            time.sleep(10)
            print(f"{node.name} is up and running! ✅")

    def start_network(self):
        print("Starting the network...")
        self.setupIdentities()
        self.extractPeerID()
        self.setPermissions()
        self.setupCoordinator()
        self.bootstrapCoordinator()
        self.startContainers()
        print("Network is up and running! ✅")
       
