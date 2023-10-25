import sys, os
import time
import numpy as np
import argparse

from utils import utils_monitor as um


def parse_args():
    parser = argparse.ArgumentParser(prog='system_monitor')
    parser.add_argument('--interval', default=1.0, type=float)
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args()
    return args



def print_generic_dict(dict, dict_name, end=''):
    for i, key in enumerate(list(dict.keys())):
        print(f'{dict_name}[\'{key}\']: {dict[key]}')
    if end != '':
        print(end)


def print_cpu_info(cpu_info):
    print('CPU  -', end='')
    for i, key in enumerate(list(cpu_info.keys())):
        print(f'  {key}: {cpu_info[key]};', end='')
    print()


def print_system_temp_info(temp_info):
    print('TEMPS  -')
    for i, key in enumerate(list(temp_info.keys())):
        for j, item in enumerate(temp_info[key]):
            print(f'   {key}.{item.label}: {item.current};', end='')
        print()


def print_gpu_info(gpu_info):
    # print('GPU  -')
    # for i, key_gpu in enumerate(list(gpu_info.keys())):
    #     gpu = gpu_info[key_gpu]
    #     print(f'   {key_gpu}')
    #     for j, key_item in enumerate(list(gpu.keys())):
    #         value = gpu[key_item]
    #         print(f'   {key_item}: {value}')
    #     print()
    for i, key_gpu in enumerate(list(gpu_info.keys())):
        gpu = gpu_info[key_gpu]
        print('%s: (temp: %.1f°C, util: %d%%)    ' % (key_gpu, gpu['temperature'], gpu['gpu_utilization']), end='')
    print()


def main(args):
    sys_info = um.get_kernel_info()
    print_generic_dict(sys_info, dict_name='sys_info', end='---------------')

    um.load_necessary_modules(sys_info, verbose=True)
    print('---------------')

    while True:
        cpu_info = um.get_cpu_info(args.interval)
        print_cpu_info(cpu_info)

        system_temp_info = um.get_system_temperature_info()
        print_system_temp_info(system_temp_info)

        gpu_info = um.get_gpu_info()
        print_gpu_info(gpu_info)
        # memory_info = um.get_memory_info()

        # log_wandb(cpu_info, 'cpu_info')
        # log_wandb(gpu_info, 'gpu_info')
        # log_wandb(memory_info, 'memory_info')

        time.sleep(args.interval)



if __name__ == '__main__':

    args = parse_args()

    main(args)