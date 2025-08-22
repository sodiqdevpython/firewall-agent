import psutil
import time
import hashlib
import os
from collections import defaultdict

def get_traffic_info(last_seconds=5):
    def get_process_hash(exe_path):
        try:
            if os.path.exists(exe_path):
                hasher = hashlib.sha256()
                with open(exe_path, 'rb') as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        hasher.update(chunk)
                return hasher.hexdigest()
        except (PermissionError, OSError, IOError):
            pass
        return "UNKNOWN"

    def get_process_exe_path(pid):
        try:
            proc = psutil.Process(pid)
            return proc.exe()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return "UNKNOWN"

    def format_bytes_simple(bytes_value):
        if bytes_value == 0:
            return "0B"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f}{unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f}TB"

    initial_time = time.time()
    initial_process_io = {}
    initial_network_io = psutil.net_io_counters()
    
    try:
        active_connections = psutil.net_connections(kind='inet')
    except psutil.AccessDenied:
        active_connections = []
    
    active_pids = set()
    connection_details = defaultdict(list)
    
    for conn in active_connections:
        if (conn.raddr and 
            not conn.raddr.ip.startswith("127.") and 
            conn.pid):
            active_pids.add(conn.pid)
            
            connection_details[conn.pid].append({
                'local_address': f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "unknown",
                'remote_address': f"{conn.raddr.ip}:{conn.raddr.port}"
            })
    
    for pid in active_pids:
        try:
            proc = psutil.Process(pid)
            io_counters = proc.io_counters()
            initial_process_io[pid] = {
                'read_bytes': io_counters.read_bytes,
                'write_bytes': io_counters.write_bytes,
                'process_name': proc.name(),
                'exe_path': get_process_exe_path(pid)
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    time.sleep(last_seconds)
    
    final_time = time.time()
    final_network_io = psutil.net_io_counters()
    actual_duration = final_time - initial_time
    
    process_list = []
    
    for pid in active_pids:
        if pid in initial_process_io:
            try:
                proc = psutil.Process(pid)
                final_io = proc.io_counters()
                initial_io = initial_process_io[pid]
                
                read_delta = max(0, final_io.read_bytes - initial_io['read_bytes'])
                write_delta = max(0, final_io.write_bytes - initial_io['write_bytes'])
                
                exe_path = initial_io['exe_path']
                file_hash = get_process_hash(exe_path)
                
                connection_list = {}
                connections = connection_details.get(pid, [])
                for i, conn in enumerate(connections, 1):
                    connection_list[str(i)] = {
                        "local_address": conn['local_address'],
                        "remote_address": conn['remote_address']
                    }
                
                process_dict = {
                    "image_path": exe_path,
                    "pid": pid,
                    "name": initial_io['process_name'],
                    "hash": file_hash,
                    "sent": format_bytes_simple(write_delta),
                    "received": format_bytes_simple(read_delta),
                    "connections": len(connections),
                    "connection_list": connection_list
                }

                if read_delta > 0 or write_delta > 0 or len(connections) > 0:
                    process_list.append(process_dict)
                
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    
    total_stats = {
        "duration_seconds": actual_duration,
        "total_bytes_sent": final_network_io.bytes_sent - initial_network_io.bytes_sent,
        "total_bytes_received": final_network_io.bytes_recv - initial_network_io.bytes_recv,
        "total_packets_sent": final_network_io.packets_sent - initial_network_io.packets_sent,
        "total_packets_received": final_network_io.packets_recv - initial_network_io.packets_recv
    }
    
    return {
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
        "duration": actual_duration,
        "total_statistics": total_stats,
        "processes": process_list
    }

