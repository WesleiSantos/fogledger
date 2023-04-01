from iota.iota import (IotaBasic)
from typing import List
from fogbed import (
    FogbedExperiment, Container, Resources, Services,
    CloudResourceModel, EdgeResourceModel, FogResourceModel, VirtualInstance,
    setLogLevel,
)
import os

setLogLevel('info')


def create_links(cloud: VirtualInstance, devices: List[VirtualInstance]):
    for device in devices:
        exp.add_link(device, cloud)


def create_peer_conf_file(peer_conf_file, peerName1, peerID1, peerName2, peerID2):
    with open(peer_conf_file, "w") as f:
        f.write(f"""\
{{
  "peers": [
    {{
      "alias": "{peerName1}",
      "multiAddress": "/dns/{peerName1}/tcp/15600/p2p/{peerID1}"
    }},
    {{
      "alias": "{peerName2}",
      "multiAddress": "/dns/{peerName2}/tcp/15600/p2p/{peerID2}"
    }}
  ]
}}\
""")


if (__name__ == '__main__'):
    exp = FogbedExperiment()
    iota = IotaBasic(exp=exp)
    cloud = exp.add_virtual_instance('cloud')

    ### NODE1 ###
    ledger1 = exp.add_virtual_instance('ledger1')
    node1 = Container(
        name='node1',
        dimage='hornet',
        volumes=[f"{os.path.abspath('iota/config/config-node.json')}:/app/config.json:ro",
                 f"{os.path.abspath('iota/config/profiles.json')}:/app/profiles.json",
                 f"{os.path.abspath('iota/config/peering-node.json')}:/app/peering.json",
                 f"{os.path.abspath('iota/db/private-tangle/node1.db')}:/app/db",
                 f"{os.path.abspath('iota/p2pstore/node1')}:/app/p2pstore",
                 f"{os.path.abspath('iota/snapshots')}:/app/snapshots"],
        port_bindings={'14265': '14265',
                       '8081': '8081', '15600': '15600'}
    )
    exp.add_docker(
        container=node1,
        datacenter=ledger1)
    exp.add_link(ledger1, cloud)

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
                 f"{os.path.abspath('iota/snapshots')}:/app/snapshots"]
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
                 f"{os.path.abspath('iota/snapshots')}:/app/snapshots"]
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
        port_bindings={'14626': '14626/udp'}
    )
    exp.add_docker(
        container=node_autopeering,
        datacenter=ledger4)
    exp.add_link(ledger4, cloud)

    # ledgers, nodes = iota.create_ledger('coo')
    # create_links(cloud, ledgers)

    try:
        exp.start()

        # P2P identities are generated
        node1.cmd(f'./hornet tool p2pidentity-gen > node1.identity.txt')
        coo.cmd(f'./hornet tool p2pidentity-gen > coo.identity.txt')
        spammer.cmd(f'./hornet tool p2pidentity-gen > spammer.identity.txt')
        node_autopeering.cmd(
            f'./hornet tool p2pidentity-gen > node-autopeering.identity.txt')

        # Extracts the peerID from the identity file
        node1Identity = node1.cmd(
            f'cat node1.identity.txt | awk -F : \'{{if ($1 ~ /PeerID/) print $2}}\' | sed "s/ \+//g" | tr -d "\n" | tr -d "\r"').strip("> >")
        cooIdentity = coo.cmd(
            f'cat coo.identity.txt | awk -F : \'{{if ($1 ~ /PeerID/) print $2}}\' | sed "s/ \+//g" | tr -d "\n" | tr -d "\r"').strip("> >")
        spammerIdentity = spammer.cmd(
            f'cat spammer.identity.txt | awk -F : \'{{if ($1 ~ /PeerID/) print $2}}\' | sed "s/ \+//g" | tr -d "\n" | tr -d "\r"').strip("> >")

        # Sets the peering configuration
        create_peer_conf_file(os.path.abspath('iota/config/peering-coo.json'),"node1", node1Identity, "spammer", spammerIdentity)
        create_peer_conf_file(os.path.abspath('iota/config/peering-node.json'),"coo", cooIdentity, "spammer", spammerIdentity)
        create_peer_conf_file(os.path.abspath('iota/config/peering-spammer.json'),"node1", node1Identity, "coo", cooIdentity)

        # We need this so that the peering can be properly updated
        if not os.uname()[0] == 'Darwin':
            os.system(f'sudo chown 65532:65532 {os.path.abspath("iota/config/peering-node.json")}')
            os.system(f'sudo chown 65532:65532 {os.path.abspath("iota/config/peering-spammer.json")}')
        
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
