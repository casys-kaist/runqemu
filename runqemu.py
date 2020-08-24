#!/usr/bin/env python3

"""
   runqemu.py

    Created on: Dec. 15, 2018
        Author: Taekyung Heo <tkheo@casys.kaist.ac.kr>
"""

import argparse
import os
import socket

def str2bool(v):
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

def get_memory_option(num_cores, num_nodes, memory_size):
    option = ""

    if num_nodes == 1:
        memory_size_per_node = memory_size
        option += " -numa node,cpus=0-%d,memdev=node1mem" % (num_cores-1)
        option += " -object memory-backend-ram,prealloc=on,id=node1mem,size=%dG,host-nodes=0,policy=bind"\
                % (memory_size_per_node)

    elif num_nodes == 2:
        hostname = socket.gethostname()
        memory_size_per_node = memory_size / 2
        option += " -numa node,cpus=0-%d,memdev=node0mem" % (num_cores-1)
        option += " -numa node,memdev=node1mem"
        option += " -object memory-backend-ram,prealloc=on,id=node0mem,size=%dG,host-nodes=0,policy=bind"\
                % (memory_size_per_node)
        option += " -object memory-backend-ram,prealloc=on,id=node1mem,size=%dG,host-nodes=1,policy=bind"\
                % (memory_size_per_node)

    return option

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-drive_image_path", required=True)
    parser.add_argument("-ssh_port", type=int, default=2222)
    parser.add_argument("-enable_kvm", type=str2bool, default=True)
    parser.add_argument("-num_cores", type=int, required=True)
    parser.add_argument("-num_nodes", type=int, required=True)
    parser.add_argument("-memory_size", type=int, required=True)
    parser.add_argument("-vnc_port", type=int, default=0)
    parser.add_argument("-serial_port", type=int, default=1234)
    parser.add_argument("-use_graphic", type=str2bool, default=False)
    parser.add_argument("-qmp_path", type=str, default="/tmp/qmp")
    parser.add_argument("-hmp_path", type=str, default="/tmp/hmp")
    args = parser.parse_args()

    cmd = "qemu-system-x86_64"
    cmd += " -drive file=%s,index=0,media=disk,format=raw" % (args.drive_image_path)
    cmd += " -netdev user,id=hostnet0,hostfwd=tcp::%d-:22" % (args.ssh_port)
    cmd += " -device virtio-net-pci,netdev=hostnet0,id=net0,bus=pci.0,addr=0x3"
    if args.enable_kvm:
        cmd += " -enable-kvm"
    cmd += " -smp %d" % (args.num_cores)
    cmd += " -cpu host"
    cmd += " -m %dG" % (args.memory_size)
    cmd += get_memory_option(args.num_cores, args.num_nodes, args.memory_size)
    cmd += " -vnc :%d" % (args.vnc_port)
    cmd += " -serial tcp::%d,server,nowait" % (args.serial_port)
    if not args.use_graphic:
        cmd += " -nographic"
    if args.qmp_path != None:
        cmd += " -qmp unix:%s,server,nowait" % (args.qmp_path)
    if args.hmp_path != None:
        cmd += " -monitor unix:%s,server,nowait" % (args.hmp_path)

    print(cmd)
    cmd = "sudo numactl --cpunodebind=0 %s" % (cmd)
    os.system(cmd)

if __name__ == '__main__':
    main()
