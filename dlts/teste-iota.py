from iota.iota import (IotaBasic)
from typing import List
from fogbed import (
    FogbedExperiment, Container, Resources, Services,
    CloudResourceModel, EdgeResourceModel, FogResourceModel, VirtualInstance,
    setLogLevel,
)
setLogLevel('info')


def create_links(cloud: VirtualInstance, devices: List[VirtualInstance]):
    for device in devices:
        exp.add_link(device, cloud)


if (__name__ == '__main__'):
    exp = FogbedExperiment()
    iota = IotaBasic(exp=exp)
    cloud = exp.add_virtual_instance('cloud')
    ledgers, nodes = iota.create_ledger('coo')
    create_links(cloud, ledgers)

    try:
        exp.start()
        # iota.start_network()
        # print(nodes[0].cmd(f'ping -c 4 {nodes[1].ip}'))
        # exp.start_cli()
        # input('Press any key...')
    except Exception as ex:
        print(ex)
    finally:
        exp.stop()
