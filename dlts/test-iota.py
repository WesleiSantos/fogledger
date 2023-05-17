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

if (__name__ == '__main__'):
    exp = FogbedExperiment()
    iota = IotaBasic(exp=exp, prefix='cloud')

    ### NODES ###
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
    iota.add_ledger('ledger1', [node1])

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
    iota.add_ledger('ledger2', [node2])

    ### COO ###
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
    iota.add_ledger('ledger3', [coo])

    ### spammer ###
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
    iota.add_ledger('ledger4', [spammer])

    cloud = exp.add_virtual_instance('cloud')
    create_links(cloud, iota.ledgers)

    try:
        exp.start()
        iota.start_network()
        print("Experiment started")
        input('Press any key...')

    except Exception as ex:
        print(ex)
    finally:
        exp.stop()
