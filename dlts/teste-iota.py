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
    iota = IotaBasic(exp=exp)
    cloud = exp.add_virtual_instance('cloud')


    ### NODE1 ###
    ledger1 = exp.add_virtual_instance('ledger1')
    node1 = Container(
        name='node1',
        dimage='hornet',
        volumes=[f"{os.path.abspath('iota/config/config-node.json')}:/app/config.json:ro",
                 f"{os.path.abspath('iota/config/profiles.json')}:/app/profiles.json"
                 f"{os.path.abspath('iota/config/peering-node.json')}:/app/peering.json"
                 f"{os.path.abspath('iota/db/private-tangle/node1.db')}:/app/db"
                 f"{os.path.abspath('iota/p2pstore/node1')}:/app/p2pstore"
                 f"{os.path.abspath('iota/snapshots')}:/app/snapshots"]
    )
    exp.add_docker(
        container=node1,
        datacenter=ledger1)
    exp.add_link(ledger1, cloud)

    ### COO ###
    ledger2 = exp.add_virtual_instance('ledger2')
    coo = Container(
        name='coo',
        dimage='hornet'
    )
    exp.add_docker(
        container=coo,
        datacenter=ledger2)
    exp.add_link(ledger2, cloud)

    ### spammer ###
    ledger3 = exp.add_virtual_instance('ledger3')
    spammer = Container(
        name='spammer',
        dimage='hornet'
    )
    exp.add_docker(
        container=spammer,
        datacenter=ledger3)
    exp.add_link(ledger3, cloud)

    ### node-autopeering ###
    ledger4 = exp.add_virtual_instance('ledger4')
    node_autopeering = Container(
        name='auto',
        dimage='hornet'
    )
    exp.add_docker(
        container=node_autopeering,
        datacenter=ledger4)
    exp.add_link(ledger4, cloud)


    # ledgers, nodes = iota.create_ledger('coo')
    # create_links(cloud, ledgers)

    try:
        exp.start()
        #print(node1.cmd(f'ping -c 4 {node2.ip}'))
        #exp.start_cli()
        input('Press any key...')
        # iota.start_network()
        # print(nodes[0].cmd(f'ping -c 4 {nodes[1].ip}'))
        # exp.start_cli()
        # input('Press any key...')
    except Exception as ex:
        print(ex)
    finally:
        exp.stop()
