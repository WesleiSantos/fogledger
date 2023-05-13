from iota.iota import (IotaBasic)
from typing import List
from fogbed import (
    FogbedExperiment, Container, Resources, Services,
    CloudResourceModel, EdgeResourceModel, FogResourceModel, VirtualInstance,
    setLogLevel,
)
import os
import json
import time

setLogLevel('info')


def create_links(cloud: VirtualInstance, devices: List[VirtualInstance]):
    for device in devices:
        exp.add_link(device, cloud)


def create_peer_conf_file(peer_conf_file, peerIp, peerName, peerID):
    with open(peer_conf_file, "r") as f:
        data = json.load(f)
    data["peers"].append({"alias": peerName, "multiAddress": f"/dns/{peerIp}/tcp/15600/p2p/{peerID}"})
    with open(peer_conf_file, "w") as f:
        json.dump(data, f, indent=4)


def setCooPublicKey(public_key, file_path):
    with open(file_path, 'r') as f:
        file_contents = f.read()
        file_contents = file_contents.replace('"key": "{}"'.format(file_contents.split(
            '"key": "')[1].split('"')[0]), '"key": "{}"'.format(public_key))
    with open(file_path, 'w') as f:
        f.write(file_contents)


def setEntryNode(node, file_path):
    with open(file_path, "r") as f:
        data = json.load(f)
    data["p2p"]["autopeering"]["entryNodes"] = [node]
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

def write_file(file_path, file_name, text):
    with open(file_path + '/' + file_name, 'w') as file:
        file.write(text)

if (__name__ == '__main__'):
    exp = FogbedExperiment()
    iota = IotaBasic(exp=exp)
    cloud = exp.add_virtual_instance('cloud')

    ### NODE1 ###
    ledger1 = exp.add_virtual_instance('ledger1')
    node1 = Container(
        name='node1',
        dimage='hornet',
        volumes=[f"{os.path.abspath('iota/config/config-node1.json')}:/app/config.json:ro",
                 f"{os.path.abspath('iota/config/profiles.json')}:/app/profiles.json",
                 f"{os.path.abspath('iota/config/peering-node1.json')}:/app/peering.json",
                 f"{os.path.abspath('iota/db/private-tangle/node1.db')}:/app/db",
                 f"{os.path.abspath('iota/p2pstore/node1')}:/app/p2pstore",
                 f"{os.path.abspath('iota/snapshots')}:/app/snapshots"],
        port_bindings={'14265': '14265',
                       '8081': '8081', '15600': '15600'},
        ports=['14265', '8081', '1883', '15600', '14626/udp']
    )
    exp.add_docker(
        container=node1,
        datacenter=ledger1)
    exp.add_link(ledger1, cloud)

    ledger5 = exp.add_virtual_instance('ledger5')
    node2 = Container(
        name='node2',
        dimage='hornet',
        volumes=[f"{os.path.abspath('iota/config/config-node2.json')}:/app/config.json:ro",
                 f"{os.path.abspath('iota/config/profiles.json')}:/app/profiles.json",
                 f"{os.path.abspath('iota/config/peering-node2.json')}:/app/peering.json",
                 f"{os.path.abspath('iota/db/private-tangle/node2.db')}:/app/db",
                 f"{os.path.abspath('iota/p2pstore/node2')}:/app/p2pstore",
                 f"{os.path.abspath('iota/snapshots')}:/app/snapshots"],
        port_bindings={'8081': '8082'},
        ports=['14265', '8081', '15600', '14626/udp']

    )
    exp.add_docker(
        container=node2,
        datacenter=ledger5)
    exp.add_link(ledger5, cloud)

    ### COO ###
    ledger2 = exp.add_virtual_instance('ledger2')
    coo = Container(
        name='coo',
        dimage='hornet',
        volumes=[f"{os.path.abspath('iota/config/config-coo.json')}:/app/config.json:ro",
                 f"{os.path.abspath('iota/config/profiles.json')}:/app/profiles.json:ro",
                 f"{os.path.abspath('iota/config/peering-coo.json')}:/app/peering.json:ro",
                 f"{os.path.abspath('iota/db/private-tangle/coo.db')}:/app/db",
                 f"{os.path.abspath('iota/db/private-tangle')}:/app/coo-state",
                 f"{os.path.abspath('iota/p2pstore/coo')}:/app/p2pstore",
                 f"{os.path.abspath('iota/snapshots')}:/app/snapshots"],
        environment={'COO_PRV_KEYS': ''},
        ports=['15600']
    )
    exp.add_docker(
        container=coo,
        datacenter=ledger2)
    exp.add_link(ledger2, cloud)

    ### spammer ###
    ledger3 = exp.add_virtual_instance('ledger3')
    spammer = Container(
        name='spammer',
        dimage='hornet',
        volumes=[f"{os.path.abspath('iota/config/config-spammer.json')}:/app/config.json:ro",
                 f"{os.path.abspath('iota/config/profiles.json')}:/app/profiles.json",
                 f"{os.path.abspath('iota/config/peering-spammer.json')}:/app/peering.json",
                 f"{os.path.abspath('iota/db/private-tangle/spammer.db')}:/app/db",
                 f"{os.path.abspath('iota/p2pstore/spammer')}:/app/p2pstore",
                 f"{os.path.abspath('iota/snapshots')}:/app/snapshots"],
        ports=['15600', '14626/udp']
    )

    exp.add_docker(
        container=spammer,
        datacenter=ledger3)
    exp.add_link(ledger3, cloud)

    ### node-autopeering ###
    ledger4 = exp.add_virtual_instance('ledger4')
    node_autopeering = Container(
        name='auto',
        dimage='hornet',
        volumes=[f"{os.path.abspath('iota/config/config-autopeering.json')}:/app/config.json:ro",
                 f"{os.path.abspath('iota/config/profiles.json')}:/app/profiles.json",
                 f"{os.path.abspath('iota/db/private-tangle/node-autopeering.db')}:/app/db",
                 f"{os.path.abspath('iota/p2pstore/node-autopeering')}:/app/p2pstore"],
        port_bindings={'14626': '14626/udp'},
        ports=['14626/udp']
    )

    exp.add_docker(
        container=node_autopeering,
        datacenter=ledger4)
    exp.add_link(ledger4, cloud)

    try:
        exp.start()

        # P2P identities are generated
        node1Identity = node1.cmd(
            f'./hornet tool p2pidentity-gen > node1.identity.txt && cat node1.identity.txt')
        node2Identity = node2.cmd(
            f'./hornet tool p2pidentity-gen > node2.identity.txt && cat node2.identity.txt')
        cooIdentity = coo.cmd(
            f'./hornet tool p2pidentity-gen > coo.identity.txt && cat coo.identity.txt')
        spammerIdentity = spammer.cmd(
            f'./hornet tool p2pidentity-gen > spammer.identity.txt && cat spammer.identity.txt')
        nodeAutopeeringIdentity = node_autopeering.cmd(
            f'./hornet tool p2pidentity-gen > node-autopeering.identity.txt && cat node-autopeering.identity.txt')

        write_file(os.path.abspath('iota'), 'node1.identity.txt', node1Identity)
        write_file(os.path.abspath('iota'), 'node2.identity.txt', node2Identity)
        write_file(os.path.abspath('iota'), 'coo.identity.txt', cooIdentity)
        write_file(os.path.abspath('iota'), 'spammer.identity.txt', spammerIdentity)
        write_file(os.path.abspath('iota'), 'node-autopeering.identity.txt', nodeAutopeeringIdentity)

        # Extracts the peerID from the identity file
        node1Identity = node1.cmd(
            f'cat node1.identity.txt | awk -F : \'{{if ($1 ~ /PeerID/) print $2}}\' | sed "s/ \+//g" | tr -d "\n" | tr -d "\r"').strip("> >")
        node2Identity = node2.cmd(
            f'cat node2.identity.txt | awk -F : \'{{if ($1 ~ /PeerID/) print $2}}\' | sed "s/ \+//g" | tr -d "\n" | tr -d "\r"').strip("> >")
        cooIdentity = coo.cmd(
            f'cat coo.identity.txt | awk -F : \'{{if ($1 ~ /PeerID/) print $2}}\' | sed "s/ \+//g" | tr -d "\n" | tr -d "\r"').strip("> >")
        spammerIdentity = spammer.cmd(
             f'cat spammer.identity.txt | awk -F : \'{{if ($1 ~ /PeerID/) print $2}}\' | sed "s/ \+//g" | tr -d "\n" | tr -d "\r"').strip("> >")

        # Sets the peering configuration
        create_peer_conf_file(os.path.abspath('iota/config/peering-coo.json'),node1.ip,"node1", node1Identity)
        create_peer_conf_file(os.path.abspath('iota/config/peering-coo.json'),spammer.ip,"spammer", spammerIdentity)
        create_peer_conf_file(os.path.abspath('iota/config/peering-coo.json'),node2.ip,"node2", node2Identity)
        create_peer_conf_file(os.path.abspath('iota/config/peering-node1.json'),coo.ip,"coo", cooIdentity)
        create_peer_conf_file(os.path.abspath('iota/config/peering-node1.json'),spammer.ip, "spammer", spammerIdentity)
        create_peer_conf_file(os.path.abspath('iota/config/peering-node1.json'),node2.ip,"node2", node2Identity)
        create_peer_conf_file(os.path.abspath('iota/config/peering-node2.json'),coo.ip,"coo", cooIdentity)
        create_peer_conf_file(os.path.abspath('iota/config/peering-node2.json'),spammer.ip, "spammer", spammerIdentity)
        create_peer_conf_file(os.path.abspath('iota/config/peering-node2.json'),node1.ip,"node1", node1Identity)
        create_peer_conf_file(os.path.abspath('iota/config/peering-spammer.json'),node1.ip,"node1", node1Identity)
        create_peer_conf_file(os.path.abspath('iota/config/peering-spammer.json'),coo.ip, "coo", cooIdentity)
        create_peer_conf_file(os.path.abspath('iota/config/peering-spammer.json'),node2.ip,"node2", node2Identity)

        # We need this so that the peering can be properly updated
        if not os.uname()[0] == 'Darwin':
            os.system(f'sudo chown 65532:65532 {os.path.abspath("iota/config/peering-node1.json")}')
            os.system(f'sudo chown 65532:65532 {os.path.abspath("iota/config/peering-node2.json")}')
            os.system(f'sudo chown 65532:65532 {os.path.abspath("iota/config/peering-spammer.json")}')

        #Sets the autopeering configuration
        print("Setting autopeering configuration")
        entry_peerID = node_autopeering.cmd(
            f'cat node-autopeering.identity.txt | awk -F : \'{{if ($1 ~ /public key \(base58\)/) print $2}}\' | sed "s/ \+//g" | tr -d "\n" | tr -d "\r"').strip("> >")
        multiaddr = f"/dns/{node_autopeering.ip}/udp/14626/autopeering/{entry_peerID}"
        setEntryNode(multiaddr, os.path.abspath("iota/config/config-node1.json"))
        setEntryNode(multiaddr, os.path.abspath("iota/config/config-node2.json"))
        setEntryNode(multiaddr, os.path.abspath("iota/config/config-spammer.json"))

        #start autopeering
        node_autopeering.cmd(f'./hornet > node_autopeering.log &')

        #Sets the Coordinator up by creating a key pair
        coo_key_pair_file="coo-milestones-key-pair.txt"
        coo.cmd(f'./hornet tool ed25519-key > {coo_key_pair_file}')
        COO_PRV_KEYS = coo.cmd(f'cat {coo_key_pair_file} | awk -F : \'{{if ($1 ~ /private key/) print $2}}\' | sed "s/ \+//g" | tr -d "\n" | tr -d "\r"').strip("> >")
        coo.cmd(f'export COO_PRV_KEYS={COO_PRV_KEYS}')
        coo_public_key= coo.cmd(f'cat {coo_key_pair_file} | awk -F : \'{{if ($1 ~ /public key/) print $2}}\' | sed "s/ \+//g" | tr -d "\n" | tr -d "\r"').strip("> >")
        os.system(f'echo {coo_public_key} > {os.path.abspath("iota/coo-milestones-public-key.txt")}'.format(coo_public_key))
        setCooPublicKey(coo_public_key, os.path.abspath("iota/config/config-node1.json"))
        setCooPublicKey(coo_public_key, os.path.abspath("iota/config/config-node2.json"))
        setCooPublicKey(coo_public_key, os.path.abspath("iota/config/config-spammer.json"))
        setCooPublicKey(coo_public_key, os.path.abspath("iota/config/config-coo.json"))

        # Bootstraps the coordinator
        print("Bootstrapping the Coordinator...")

        # Need to do it again otherwise the coo will not bootstrap
        if not os.uname()[0] == 'Darwin':
            os.system(f'sudo chown 65532:65532 {os.path.abspath("iota/p2pstore")}')

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

        coo.cmd(f'./hornet > coo.log &')
        spammer.cmd(f'./hornet > spammer.log &')
        node1.cmd(f'./hornet > node1.log &')
        node2.cmd(f'./hornet > node2.log &')

        input('Press any key...')
        # print(node1.cmd(f'ping -c 4 {node2.ip}'))
        # exp.start_cli()
        # iota.start_network()
        # print(nodes[0].cmd(f'ping -c 4 {nodes[1].ip}'))
        # exp.start_cli()
        # input('Press any key...')

    except Exception as ex:
        print(ex)
    finally:
        exp.stop()
