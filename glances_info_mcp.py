import json
from typing import Any, List, Dict
import httpx
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("glances")

# 读取服务器配置
def load_servers_config(file_path: str) -> Dict[str, Dict[str, Any]]:
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# 加载服务器配置
SERVERS = load_servers_config('servers_config.json')

# 默认服务器配置
DEFAULT_SERVER = {
    "id": "server1",
    "env": "test"  # 可选值: test, prod
}

USER_AGENT = "glances-app/1.0"

def get_default_server_id() -> str:
    """获取默认服务器ID"""
    return DEFAULT_SERVER["id"]

def set_default_server_id(server_id: str) -> None:
    """设置默认服务器ID"""
    if server_id not in SERVERS:
        raise ValueError(f"未找到服务器配置: {server_id}")
    DEFAULT_SERVER["id"] = server_id
    DEFAULT_SERVER["env"] = "prod" if "生产" in SERVERS[server_id]["description"] else "test"

def get_server_url(server_id: str = None) -> str:
    """获取服务器API地址"""
    if server_id is None:
        server_id = get_default_server_id()
    if server_id not in SERVERS:
        raise ValueError(f"未找到服务器配置: {server_id}")
    return SERVERS[server_id]["url"]

async def make_glances_request(endpoint: str, server_id: str = None) -> dict[str, Any] | None:
    """Make a request to the Glances API with proper error handling."""
    if server_id is None:
        server_id = get_default_server_id()
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json"
    }
    url = f"{get_server_url(server_id)}/{endpoint}"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

async def make_glances_post_request(endpoint: str, server_id: str = None) -> bool:
    """Make a POST request to the Glances API with proper error handling."""
    if server_id is None:
        server_id = get_default_server_id()
    headers = {
        "User-Agent": USER_AGENT,
        "Content-Type": "application/json"
    }
    url = f"{get_server_url(server_id)}/{endpoint}"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return True
        except Exception:
            return False

@mcp.tool()
async def set_default_server(server_id: str) -> str:
    """设置默认服务器。
    
    参数:
        server_id: 服务器唯一标识
    
    返回:
        操作结果字符串
    """
    try:
        set_default_server_id(server_id)
        server = SERVERS[server_id]
        return f"已将默认服务器设置为: {server['name']} ({server['description']})"
    except ValueError as e:
        return str(e)

@mcp.tool()
async def get_default_server() -> str:
    """获取当前默认服务器信息。
    
    返回:
        默认服务器信息字符串
    """
    server_id = get_default_server_id()
    server = SERVERS[server_id]
    return f"""
当前默认服务器:
ID: {server_id}
名称: {server['name']}
环境: {'生产环境' if DEFAULT_SERVER['env'] == 'prod' else '测试环境'}
描述: {server['description']}
地址: {server['url']}
"""

# 添加服务器管理函数
@mcp.tool()
async def list_servers() -> str:
    """获取所有配置的服务器列表。
    
    返回:
        包含所有服务器信息的字符串
    """
    result = "配置的服务器列表:\n"
    for server_id, info in SERVERS.items():
        result += f"""
ID: {server_id}
名称: {info['name']}
地址: {info['url']}
描述: {info['description']}
"""
    return result

@mcp.tool()
async def add_server(server_id: str, name: str, url: str, description: str = "") -> str:
    """添加新的服务器配置。
    
    参数:
        server_id: 服务器唯一标识
        name: 服务器名称
        url: 服务器API地址
        description: 服务器描述
    
    返回:
        操作结果字符串
    """
    if server_id in SERVERS:
        return f"错误：服务器ID '{server_id}' 已存在"
    
    SERVERS[server_id] = {
        "name": name,
        "url": url,
        "description": description
    }
    return f"成功添加服务器 '{name}'"

@mcp.tool()
async def remove_server(server_id: str) -> str:
    """删除服务器配置。
    
    参数:
        server_id: 服务器唯一标识
    
    返回:
        操作结果字符串
    """
    if server_id not in SERVERS:
        return f"错误：未找到服务器ID '{server_id}'"
    
    del SERVERS[server_id]
    return f"成功删除服务器 '{server_id}'"

def format_system_info(data: dict) -> str:
    """Format system information into a readable string."""
    return f"""
系统信息:
主机名: {data.get('hostname', 'Unknown')}
操作系统: {data.get('os_name', 'Unknown')} {data.get('os_version', '')}
CPU使用率: {data.get('cpu', {}).get('total', 0)}%
内存使用率: {data.get('mem', {}).get('percent', 0)}%
磁盘使用率: {data.get('diskio', {}).get('percent', 0)}%
"""

def format_process_info(processes: list) -> str:
    """Format process information into a readable string."""
    result = "进程信息 (前5个):\n"
    for i, proc in enumerate(processes[:5]):
        result += f"""
{i+1}. {proc.get('name', 'Unknown')} (PID: {proc.get('pid', 'Unknown')})
   CPU: {proc.get('cpu_percent', 0)}%
   内存: {proc.get('memory_percent', 0)}%
"""
    return result

def format_alert_info(alerts: List[dict]) -> str:
    """Format alert information into a readable string."""
    if not alerts:
        return "当前没有告警信息"
    
    result = "告警信息:\n"
    for alert in alerts:
        result += f"""
类型: {alert.get('type', 'Unknown')}
状态: {alert.get('state', 'Unknown')}
开始时间: {alert.get('begin', 'Unknown')}
结束时间: {alert.get('end', '-1' if alert.get('end') == -1 else alert.get('end', 'Unknown'))}
描述: {alert.get('desc', 'No description')}
"""
    return result

def format_cpu_info(data: dict) -> str:
    """Format CPU information into a readable string."""
    return f"""
CPU信息:
总使用率: {data.get('total', 0)}%
用户空间: {data.get('user', 0)}%
系统空间: {data.get('system', 0)}%
空闲: {data.get('idle', 0)}%
I/O等待: {data.get('iowait', 0)}%
"""

def format_memory_info(data: dict) -> str:
    """Format memory information into a readable string."""
    return f"""
内存信息:
总内存: {data.get('total', 0) / 1024 / 1024:.2f} MB
已使用: {data.get('used', 0) / 1024 / 1024:.2f} MB
空闲: {data.get('free', 0) / 1024 / 1024:.2f} MB
使用率: {data.get('percent', 0)}%
"""

def format_disk_info(data: dict) -> str:
    """Format disk I/O information into a readable string."""
    result = "磁盘I/O信息:\n"
    for disk, info in data.items():
        result += f"""
设备: {disk}
  读取: {info.get('read_bytes', 0) / 1024 / 1024:.2f} MB
  写入: {info.get('write_bytes', 0) / 1024 / 1024:.2f} MB
"""
    return result

def format_sensors_info(data: dict) -> str:
    """Format sensors information into a readable string."""
    result = "传感器信息:\n"
    for sensor_type, sensors in data.items():
        result += f"\n{sensor_type}:\n"
        if isinstance(sensors, list):
            for sensor in sensors:
                result += f"  {sensor.get('label', 'Unknown')}: {sensor.get('value', 0)} {sensor.get('unit', '')}\n"
        elif isinstance(sensors, dict):
            result += f"  值: {sensors.get('value', 0)} {sensors.get('unit', '')}\n"
    return result

def format_docker_info(containers: list) -> str:
    """Format Docker containers information into a readable string."""
    if not containers:
        return "没有运行中的Docker容器"
    
    result = "Docker容器信息:\n"
    for container in containers:
        result += f"""
容器ID: {container.get('id', 'Unknown')[:12]}
名称: {container.get('name', 'Unknown')}
镜像: {container.get('image', ['Unknown'])[0]}
状态: {container.get('status', 'Unknown')}
CPU使用率: {container.get('cpu_percent', 0)}%
内存使用率: {container.get('memory_percent', 0)}%
"""
    return result

def format_gpu_info(data: dict) -> str:
    """Format GPU information into a readable string."""
    if not data:
        return "没有检测到GPU或GPU信息不可用"
    
    result = "GPU信息:\n"
    for gpu in data:
        result += f"""
GPU ID: {gpu.get('gpu_id', 'Unknown')}
名称: {gpu.get('name', 'Unknown')}
温度: {gpu.get('temperature', 0)}°C
处理器使用率: {gpu.get('proc', 0)}%
内存使用率: {gpu.get('mem', 0)}%
风扇转速: {gpu.get('fan_speed', 0)} RPM
"""
    return result

def format_process_count(data: dict) -> str:
    """Format process count information into a readable string."""
    return f"""
进程统计:
总数: {data.get('total', 0)}
运行中: {data.get('running', 0)}
休眠: {data.get('sleeping', 0)}
其他: {data.get('other', 0)}
线程: {data.get('thread', 0)}
"""

def format_connections_info(data: dict) -> str:
    """Format network connections information into a readable string."""
    return f"""
网络连接统计:
已建立连接: {data.get('ESTABLISHED', 0)}
监听端口: {data.get('LISTEN', 0)}
等待连接: {data.get('SYN_SENT', 0)}
接收连接: {data.get('SYN_RECV', 0)}
已发起连接: {data.get('initiated', 0)}
已终止连接: {data.get('terminated', 0)}
"""

def format_ip_info(data: dict) -> str:
    """Format IP information into a readable string."""
    result = "IP地址信息:\n"
    for interface, addresses in data.items():
        result += f"\n{interface}:\n"
        for addr in addresses:
            result += f"  {addr.get('address', 'Unknown')} ({addr.get('family', 'Unknown')})\n"
    return result

@mcp.tool()
async def get_system_info(server_id: str = None) -> str:
    """获取Linux服务器的系统信息。
    
    参数:
        server_id: 服务器ID
    
    返回:
        包含CPU、内存、磁盘等系统信息的字符串
    """
    try:
        data = await make_glances_request("system", server_id)
        
        if not data:
            return f"无法获取服务器 '{server_id}' 的系统信息。"
        
        return f"服务器 '{SERVERS[server_id]['name']}' 的系统信息:\n" + format_system_info(data)
    except ValueError as e:
        return str(e)

@mcp.tool()
async def get_process_info(server_id: str = None) -> str:
    """获取Linux服务器上运行的进程信息。
    
    参数:
        server_id: 服务器ID
    
    返回:
        包含进程名称、PID、CPU和内存使用率的字符串
    """
    try:
        data = await make_glances_request("processlist", server_id)
        
        if not data:
            return f"无法获取服务器 '{server_id}' 的进程信息。"
        
        return f"服务器 '{SERVERS[server_id]['name']}' 的进程信息:\n" + format_process_info(data)
    except ValueError as e:
        return str(e)

@mcp.tool()
async def get_network_info(server_id: str = None) -> str:
    """获取Linux服务器的网络信息。
    
    参数:
        server_id: 服务器ID
    
    返回:
        包含网络接口和流量信息的字符串
    """
    data = await make_glances_request("network", server_id)
    
    if not data:
        return "无法获取网络信息。"
    
    result = "网络信息:\n"
    
    for interface in data:
        # 获取接口名称
        interface_name = interface.get('interface_name', 'unknown')
        
        # 计算速率，转换为更友好的单位
        recv_rate = interface.get('bytes_recv_rate_per_sec', 0)
        sent_rate = interface.get('bytes_sent_rate_per_sec', 0)
        
        # 获取总流量
        total_recv = interface.get('bytes_recv_gauge', 0)
        total_sent = interface.get('bytes_sent_gauge', 0)
        
        # 获取链接速度（转换为Gbps）
        speed_gbps = interface.get('speed', 0) / (1024 * 1024 * 1024)
        
        result += f"""
接口: {interface_name}
  链接速度: {speed_gbps:.2f} Gbps
  当前速率:
    接收: {format_bytes_rate(recv_rate)}/s
    发送: {format_bytes_rate(sent_rate)}/s
  总流量:
    接收: {format_bytes(total_recv)}
    发送: {format_bytes(total_sent)}
"""
    return result

def format_bytes(bytes_value: float) -> str:
    """将字节数转换为人类可读格式"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024
    return f"{bytes_value:.2f} PB"

def format_bytes_rate(bytes_per_sec: float) -> str:
    """将字节率转换为人类可读格式"""
    return format_bytes(bytes_per_sec)

@mcp.tool()
async def get_alert_info(server_id: str = None) -> str:
    """获取系统告警信息。
    
    参数:
        server_id: 服务器ID
    
    返回:
        包含当前系统告警的字符串
    """
    data = await make_glances_request("alert", server_id)
    
    if data is None:
        return "无法获取告警信息。"
    
    return format_alert_info(data)

@mcp.tool()
async def clear_all_alerts(server_id: str = None) -> str:
    """清除所有系统告警。
    
    参数:
        server_id: 服务器ID
    
    返回:
        操作结果字符串
    """
    success = await make_glances_post_request("events/clear/all", server_id)
    return "已成功清除所有告警。" if success else "清除告警失败。"

@mcp.tool()
async def get_cpu_info(server_id: str = None) -> str:
    """获取详细的CPU信息。
    
    参数:
        server_id: 服务器ID
    
    返回:
        包含CPU使用情况的字符串
    """
    data = await make_glances_request("cpu", server_id)
    
    if not data:
        return "无法获取CPU信息。"
    
    return format_cpu_info(data)

@mcp.tool()
async def get_memory_info(server_id: str = None) -> str:
    """获取详细的内存信息。
    
    参数:
        server_id: 服务器ID
    
    返回:
        包含内存使用情况的字符串
    """
    data = await make_glances_request("mem", server_id)
    
    if not data:
        return "无法获取内存信息。"
    
    return format_memory_info(data)

@mcp.tool()
async def get_disk_io_info(server_id: str = None) -> str:
    """获取磁盘I/O信息。
    
    参数:
        server_id: 服务器ID
    
    返回:
        包含磁盘读写情况的字符串
    """
    data = await make_glances_request("diskio", server_id)
    
    if not data:
        return "无法获取磁盘I/O信息。"
    
    return format_disk_info(data)

@mcp.tool()
async def get_plugins_list(server_id: str = None) -> str:
    """获取已启用的插件列表。
    
    参数:
        server_id: 服务器ID
    
    返回:
        包含插件列表的字符串
    """
    data = await make_glances_request("pluginslist", server_id)
    
    if not data:
        return "无法获取插件列表。"
    
    return f"已启用的插件:\n{', '.join(data)}"

@mcp.tool()
async def get_sensors_info(server_id: str = None) -> str:
    """获取系统传感器信息。
    
    参数:
        server_id: 服务器ID
    
    返回:
        包含温度、风扇等传感器信息的字符串
    """
    data = await make_glances_request("sensors", server_id)
    
    if not data:
        return "无法获取传感器信息。"
    
    return format_sensors_info(data)

@mcp.tool()
async def get_docker_info(server_id: str = None) -> str:
    """获取Docker容器信息。
    
    参数:
        server_id: 服务器ID
    
    返回:
        包含Docker容器状态的字符串
    """
    data = await make_glances_request("containers", server_id)
    
    if not data:
        return "无法获取Docker容器信息。"
    
    return format_docker_info(data)

@mcp.tool()
async def get_gpu_info(server_id: str = None) -> str:
    """获取GPU信息。
    
    参数:
        server_id: 服务器ID
    
    返回:
        包含GPU使用情况的字符串
    """
    data = await make_glances_request("gpu", server_id)
    
    if not data:
        return "无法获取GPU信息。"
    
    return format_gpu_info(data)

@mcp.tool()
async def get_quicklook(server_id: str = None) -> str:
    """获取系统快速概览信息。
    
    参数:
        server_id: 服务器ID
    
    返回:
        包含系统关键指标的字符串
    """
    data = await make_glances_request("quicklook", server_id)
    
    if not data:
        return "无法获取系统概览信息。"
    
    return f"""
系统概览:
CPU: {data.get('cpu', 0)}%
内存: {data.get('mem', 0)}%
交换分区: {data.get('swap', 0)}%
系统负载: {data.get('load', '0 0 0')}
"""

@mcp.tool()
async def get_fs_info(server_id: str = None) -> str:
    """获取文件系统信息。
    
    参数:
        server_id: 服务器ID
    
    返回:
        包含文件系统使用情况的字符串
    """
    data = await make_glances_request("fs", server_id)
    
    if not data:
        return "无法获取文件系统信息。"
    
    result = "文件系统信息:\n"
    for fs in data:
        result += f"""
挂载点: {fs.get('mnt_point', 'Unknown')}
设备: {fs.get('device_name', 'Unknown')}
总空间: {fs.get('size', 0) / 1024 / 1024 / 1024:.2f} GB
已用: {fs.get('used', 0) / 1024 / 1024 / 1024:.2f} GB
可用: {fs.get('free', 0) / 1024 / 1024 / 1024:.2f} GB
使用率: {fs.get('percent', 0)}%
"""
    return result

@mcp.tool()
async def get_uptime(server_id: str = None) -> str:
    """获取系统运行时间。
    
    参数:
        server_id: 服务器ID
    
    返回:
        包含系统运行时间的字符串
    """
    data = await make_glances_request("uptime", server_id)
    
    if not data:
        return "无法获取系统运行时间。"
    
    # Convert seconds to days, hours, minutes
    seconds = int(data)
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    
    return f"系统已运行: {days}天 {hours}小时 {minutes}分钟"

@mcp.tool()
async def get_all_stats(server_id: str = None) -> str:
    """获取所有系统统计信息。
    
    参数:
        server_id: 服务器ID
    
    返回:
        包含所有可用系统信息的字符串
    """
    try:
        data = await make_glances_request("all", server_id)
        
        if not data:
            return f"无法获取服务器 '{server_id}' 的系统统计信息。"
        
        result = f"服务器 '{SERVERS[server_id]['name']}' 的统计信息汇总:\n"
        result += await get_system_info(server_id)
        result += "\n" + await get_cpu_info(server_id)
        result += "\n" + await get_memory_info(server_id)
        result += "\n" + await get_disk_io_info(server_id)
        result += "\n" + await get_network_info(server_id)
        result += "\n" + await get_uptime(server_id)
        
        return result
    except ValueError as e:
        return str(e)

@mcp.tool()
async def get_process_count(server_id: str = None) -> str:
    """获取进程统计信息。
    
    参数:
        server_id: 服务器ID
    
    返回:
        包含进程数量统计的字符串
    """
    data = await make_glances_request("processcount", server_id)
    
    if not data:
        return "无法获取进程统计信息。"
    
    return format_process_count(data)

@mcp.tool()
async def get_connections_stats(server_id: str = None) -> str:
    """获取网络连接统计信息。
    
    参数:
        server_id: 服务器ID
    
    返回:
        包含网络连接统计的字符串
    """
    data = await make_glances_request("connections", server_id)
    
    if not data:
        return "无法获取网络连接统计信息。"
    
    return format_connections_info(data)

@mcp.tool()
async def get_ip_addresses(server_id: str = None) -> str:
    """获取IP地址信息。
    
    参数:
        server_id: 服务器ID
    
    返回:
        包含IP地址信息的字符串
    """
    data = await make_glances_request("ip", server_id)
    
    if not data:
        return "无法获取IP地址信息。"
    
    return format_ip_info(data)

@mcp.tool()
async def get_load_average(server_id: str = None) -> str:
    """获取系统负载信息。
    
    参数:
        server_id: 服务器ID
    
    返回:
        包含系统负载的字符串
    """
    data = await make_glances_request("load", server_id)
    
    if not data:
        return "无法获取系统负载信息。"
    
    return f"""
系统负载:
1分钟: {data.get('min1', 0):.2f}
5分钟: {data.get('min5', 0):.2f}
15分钟: {data.get('min15', 0):.2f}
CPU核心数: {data.get('cpucore', 0)}
"""

@mcp.tool()
async def get_swap_info(server_id: str = None) -> str:
    """获取交换分区信息。
    
    参数:
        server_id: 服务器ID
    
    返回:
        包含交换分区使用情况的字符串
    """
    data = await make_glances_request("memswap", server_id)
    
    if not data:
        return "无法获取交换分区信息。"
    
    return f"""
交换分区信息:
总大小: {data.get('total', 0) / 1024 / 1024:.2f} MB
已使用: {data.get('used', 0) / 1024 / 1024:.2f} MB
空闲: {data.get('free', 0) / 1024 / 1024:.2f} MB
使用率: {data.get('percent', 0)}%
"""

@mcp.tool()
async def get_version_info(server_id: str = None) -> str:
    """获取Glances版本信息。
    
    参数:
        server_id: 服务器ID
    
    返回:
        包含版本信息的字符串
    """
    data = await make_glances_request("version", server_id)
    
    if not data:
        return "无法获取版本信息。"
    
    return f"""
Glances版本信息:
版本号: {data.get('version', 'Unknown')}
系统: {data.get('system', 'Unknown')}
Python版本: {data.get('python_version', 'Unknown')}
"""

@mcp.tool()
async def get_process_list(server_id: str = None) -> str:
    """获取指定服务器的进程列表信息。
    
    参数:
        server_id: 服务器ID
    
    返回:
        包含进程信息的字符串
    """
    # 获取进程列表数据
    data = await make_glances_request("processlist", server_id)
    
    if not data:
        return f"无法获取服务器 '{server_id}' 的进程列表信息。"
    
    # 格式化进程信息
    result = "进程信息:\n"
    for proc in data:
        result += f"""
PID: {proc.get('pid', 'Unknown')}
名称: {proc.get('name', 'Unknown')}
命令行: {proc.get('cmdline', 'Unknown')}
用户名: {proc.get('username', 'Unknown')}
线程数: {proc.get('num_threads', 0)}
CPU使用率: {proc.get('cpu_percent', 0)}%
内存使用率: {proc.get('memory_percent', 0)}%
"""
    
    return result

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')