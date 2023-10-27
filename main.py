import sys, os
import time
import numpy as np
import argparse
import wandb
from datetime import datetime

from utils import utils_monitor as um
from config.configs import EasyConfig


def parse_args():
    parser = argparse.ArgumentParser(prog='system_monitor')
    parser.add_argument('--config', default='config/default_config.yaml', type=str)
    parser.add_argument('--interval', default=5.0, type=float)
    parser.add_argument('--verbose', action='store_true')
    parser.add_argument('--no-wandb', action='store_true')
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
    for i, key_gpu in enumerate(list(gpu_info.keys())):
        gpu = gpu_info[key_gpu]
        print('%s: (temp: %.1f°C, util: %d%%)    ' % (key_gpu, gpu['temperature'], gpu['gpu_utilization']), end='')
    print()


def print_memory_info(memory_info):
    print('MEM  -', end='')
    for i, key in enumerate(list(memory_info.keys())):
        print('  %s: %.1fGB' % (key, memory_info[key]), end='')
    print()


def init_wandb_logger(cfg, sys_info):
    wandb_logger = None
    if cfg.wandb.using_wandb:
        wandb.login(key=cfg.wandb.api_key)
        project_name = sys_info['nodename'] + cfg.wandb.project if cfg.wandb.project.startswith('_') else sys_info['nodename'] + '_' + cfg.wandb.project
        run_name = 'start_' + datetime.now().strftime("%Y-%m-%d_%H:%M")
        wandb_logger = wandb.init(
                entity = cfg.wandb.entity, 
                project = project_name,
                sync_tensorboard = True,
                resume=cfg.wandb.resume,
                name = run_name,
                notes = cfg.wandb.notes) if cfg.wandb.log_all else None
    return wandb_logger


def log_wandb(wandb_logger, dict_info):
    sys_info, cpu_info, system_temp_info, gpu_info, memory_info = \
        dict_info['sys_info'], dict_info['cpu_info'], dict_info['system_temp_info'], dict_info['gpu_info'], dict_info['memory_info'], 

    # log CPU info
    for i, key in enumerate(list(cpu_info.keys())):
        wandb_logger.log({
            'cpu_info/'+str(key): cpu_info[key],
        })
    
    # log TEMPERATURES info
    for i, key in enumerate(list(system_temp_info.keys())):
        for j, item in enumerate(system_temp_info[key]):
            wandb_logger.log({
                'system_temp_info/'+str(key)+'.'+str(j)+'.'+str(item.label): item.current,
            })
    
    # log GPU info
    for i, key_gpu in enumerate(list(gpu_info.keys())):
        gpu = gpu_info[key_gpu]
        wandb_logger.log({
            'gpu_info/'+str(key_gpu)+'.temperature': gpu['temperature'],
            'gpu_info/'+str(key_gpu)+'.gpu_utilization': gpu['gpu_utilization'],
        })
    
    # log MEMORY info
    for i, key in enumerate(list(memory_info.keys())):
        wandb_logger.log({
            'memory_info/'+str(key): memory_info[key],
        })



def main(args, cfg):
    sys_info = um.get_kernel_info()
    print_generic_dict(sys_info, dict_name='sys_info', end='---------------')

    um.load_necessary_modules(sys_info, verbose=True)
    print('---------------')

    if not args.no_wandb:
        print('Initializing wand...')
        wandb_logger = init_wandb_logger(cfg, sys_info)
        print('---------------')

    while True:
        cpu_info = um.get_cpu_info()
        system_temp_info = um.get_system_temperature_info()
        gpu_info = um.get_gpu_info()
        memory_info = um.get_memory_info()

        date_time_now = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
        print(date_time_now)
        print_cpu_info(cpu_info)
        print_system_temp_info(system_temp_info)
        print_gpu_info(gpu_info)
        print_memory_info(memory_info)

        dict_info = {
            'sys_info': sys_info,
            'cpu_info': cpu_info,
            'system_temp_info': system_temp_info,
            'gpu_info': gpu_info,
            'memory_info': memory_info
        }
        if not args.no_wandb:
            log_wandb(wandb_logger, dict_info)

        print('---------------')
        time.sleep(args.interval)



if __name__ == '__main__':
    args = parse_args()
    cfg = EasyConfig()
    cfg.load(args.config, recursive=True)

    main(args, cfg)