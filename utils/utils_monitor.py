import os, sys
import psutil
import socket
import time
from nvitop import Device
import subprocess


ubuntu_modules = ['drivetemp']    # tested on Ubuntu 20.04 LTS


def run_system_command(cmd):
    p = subprocess.run(cmd.split(' '), capture_output=True)
    return p

def load_necessary_modules(system_info, verbose=True):
    sysname = system_info['sysname']
    if 'Linux' in sysname:
        for ubuntu_module in ubuntu_modules:
            cmd = f'lsmod | grep {ubuntu_module}'   # check if module exists in system
            p = run_system_command(cmd)

            if p.returncode == 0:
                if verbose:
                    print('Loading necessary Linux modules...')
                cmd = f'sudo modprobe -v {ubuntu_module}'   # load kernel module
                if verbose:
                    print(cmd)

                p = run_system_command(cmd)
                if p.returncode != 0:
                    raise Exception(f'Error when loading module \'{ubuntu_module}\'. returncode={p.returncode}, stdout=\'{p.stdout.decode()}\', stderr=\'{p.stderr.decode()}\'')

            else:
                print(f'Warning: module \'{ubuntu_module}\' not found.')
    else:
        raise Exception(f'Sorry, system_monitor is not implemented for the system \'{sysname}\' yet!')


def get_kernel_info():
    system_info = {
        'nodename': os.uname().nodename,
        'sysname': os.uname().sysname,
        'kernel_version': os.uname().release,
        'arch': os.uname().machine,
    }
    net_if_addrs = psutil.net_if_addrs()
    for iface in list(net_if_addrs.keys()):
        if iface != 'lo':
            if len(net_if_addrs[iface]) > 0:
                system_info[f'{iface}_ipv4'] = net_if_addrs[iface][0].address
            if len(net_if_addrs[iface]) > 1:
                system_info[f'{iface}_ipv6'] = net_if_addrs[iface][1].address
    return system_info


def get_memory_info():
    memory_info = psutil.virtual_memory()
    swap_info = psutil.swap_memory()
    unit = 1024.0 ** 3   # GB
    return {
        'total_memory': memory_info.total / unit,
        'available_memory': memory_info.available / unit,
        'used_memory': memory_info.used / unit,
        'memory_percent': memory_info.percent,
        'swap_total': swap_info.total / unit,
        'swap_used': swap_info.used / unit,
        'swap_free': swap_info.free / unit,
        'swap_percent': swap_info.percent
    }


def get_cpu_info(interval=1):
    cpu_info = {
        # 'physical_cores': psutil.cpu_count(logical=False),
        'total_cores': psutil.cpu_count(logical=True),
        'processor_speed': psutil.cpu_freq().current,
        # 'cpu_usage_per_core': dict(enumerate(psutil.cpu_percent(percpu=True, interval=interval))),
        'total_cpu_usage': psutil.cpu_percent(interval=interval)
    }
    return cpu_info


def get_system_temperature_info():
    sensors_temp = psutil.sensors_temperatures()
    return sensors_temp


def get_gpu_info():
    gpu_info = {}
    devices = Device.all()
    for device in devices:
        gpu_name = 'gpu'+str(device.index)+'_'+device.name().replace(' ','_')
        gpu_info[gpu_name] = {}
        gpu_info[gpu_name]['device'] = device
        gpu_info[gpu_name]['processes'] = device.processes()
        gpu_info[gpu_name]['fan_speed'] = device.fan_speed()
        gpu_info[gpu_name]['temperature'] = device.temperature()
        gpu_info[gpu_name]['gpu_utilization'] = device.gpu_utilization()
        gpu_info[gpu_name]['memory_total_human'] = device.memory_total_human()
        gpu_info[gpu_name]['memory_used_human'] = device.memory_used_human()
        gpu_info[gpu_name]['memory_free_human'] = device.memory_free_human()
    return gpu_info


def get_disk_info():
    partitions = psutil.disk_partitions()
    disk_info = {}
    for partition in partitions:
        partition_usage = psutil.disk_usage(partition.mountpoint)
        disk_info[partition.mountpoint] = {
            'total_space': partition_usage.total / (1024.0 ** 3),
            'used_space': partition_usage.used / (1024.0 ** 3),
            'free_space': partition_usage.free / (1024.0 ** 3),
            'usage_percentage': partition_usage.percent
        }
    return disk_info


def get_network_info():
    net_io_counters = psutil.net_io_counters()
    return {
        'bytes_sent': net_io_counters.bytes_sent,
        'bytes_recv': net_io_counters.bytes_recv
    }


def get_process_info():
    process_info = []
    for process in psutil.process_iter(['pid', 'name', 'memory_percent', 'cpu_percent']):
        try:
            process_info.append({
                'pid': process.info['pid'],
                'name': process.info['name'],
                'memory_percent': process.info['memory_percent'],
                'cpu_percent': process.info['cpu_percent']
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return process_info


def get_load_average():
    load_avg_1, load_avg_5, load_avg_15 = psutil.getloadavg()
    return {
        'load_average_1': load_avg_1,
        'load_average_5': load_avg_5,
        'load_average_15': load_avg_15
    }


def get_disk_io_counters():
    io_counters = psutil.disk_io_counters()
    return {
        'read_count': io_counters.read_count,
        'write_count': io_counters.write_count,
        'read_bytes': io_counters.read_bytes,
        'write_bytes': io_counters.write_bytes,
        'read_time': io_counters.read_time,
        'write_time': io_counters.write_time
    }


def get_net_io_counters():
    io_counters = psutil.net_io_counters()
    return {
        'bytes_sent': io_counters.bytes_sent,
        'bytes_recv': io_counters.bytes_recv,
        'packets_sent': io_counters.packets_sent,
        'packets_recv': io_counters.packets_recv,
        'errin': io_counters.errin,
        'errout': io_counters.errout,
        'dropin': io_counters.dropin,
        'dropout': io_counters.dropout
    }


def get_system_uptime():
    boot_time_timestamp = psutil.boot_time()
    current_time_timestamp = time.time()
    uptime_seconds = current_time_timestamp - boot_time_timestamp
    uptime_minutes = uptime_seconds // 60
    uptime_hours = uptime_minutes // 60
    uptime_days = uptime_hours // 24
    uptime_str = f'{int(uptime_days)} days, {int(uptime_hours % 24)} hours, {int(uptime_minutes % 60)} minutes, {int(uptime_seconds % 60)} seconds'
    return {'uptime': uptime_str}
