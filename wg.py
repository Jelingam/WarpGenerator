import csv
import json
import os
import subprocess
import platform
import sys
import time
from random import randint
import datetime
import re
import ipaddress

try:
    from tqdm import tqdm
    import requests
except:
    print("installing packages : tqdm requests")
    subprocess.run("pip install --trusted-host https://pypi.tuna.tsinghua.edu.cn/simple/ tqdm requests", text=True, shell=True, capture_output=True)
    from tqdm import tqdm
    import requests

class Warp():
    
    def __init__(self):
        self.init_settings()
        self.starting_print_and_inputs()
        # if not self.ip_version4:
        #     self.print("Under Development, comming up in the next version just in few days ...", color = "red")
        #     sys.exit(0)
        self.check_platform()
        self.download_wgcf()
        self.download_warpendpoint()
        self.test_endpoints()
        self.generate_wiregurd_configs()
        
        if self.cpu in ["arm64", "armv7"]:
            self.copy_configs_to_device()
        pass
    
    def init_settings(self):
        self.noine_options = {
        "mtu" : [1306],
        "fake_packets_mode" : ["m1", "m2", "m3", "m4", "m5" "m6"],
        "fake_packets_delay" : ["5-10", "10-20", "20-50", "50-100"],
        "fake_packets_size" : ["40-100", "100-200"],
        "fake_packets" : ["5-10", "10-20", "20-40","40-80", "80-160"],
        }
        self.cpu = "arm64"
        self.util_path = "./utils"
        self.wgcf_path = "./wgcf"
        self.warpendpoint_path = "./warpendpoint"
        self.hiddifycli_path = "./HiddifyCli"
        self.warpendpoint_result_path = "./result.csv"
        self.current_config_path = "./current_config.json"
        self.hiddify_app_settings = "./hiddify_app_settings.json"
        self.ipv4_range_path = "./ipv4_range.txt"
        self.ipv6_range_path = "./ipv6_range.txt"
        self.ip_list_path = "./ip.txt"
        self.wgcf_profile_path = "./wgcf-profile.conf"
        self.minimum_config = 2
        self.zero_packet_loss_ips= []
        self.wireguard_configs = []
        self.ip_version4 = True         # alternative 6
  
    def starting_print_and_inputs(self):
        os.system('cls||clear')
        self.print(".:| Hiddify Warp config generator by Jelingam |:.", color = "red")
        print("\n")
        id_width = 7
        text_width = 20
        ip_width = 6
        total_width = id_width + text_width + ip_width + 8
        table_color = "white"
        self.print("|" + "-"*total_width + "|" , color = table_color)
        self.print(["| ", "ID", " | ", "Item", " | ",  "IPVer",  " |"], pad = [2, id_width, 3, text_width, 3, ip_width, 2], color = [table_color, "purple", table_color, "cyan", table_color, "yellow", table_color])        
        self.print("|" + "-"*total_width + "|" , color = table_color)
        self.print(["| ", "[1]", " | ", "Hiddify Warp v > 2", " | ",  "ipV4",  " |"], pad = [2, id_width, 3, text_width, 3, ip_width, 2], color = [table_color, "purple", table_color, "cyan", table_color, "yellow", table_color])
        self.print(["| ", "[2]", " | ", "Hiddify Warp v > 2", " | ",  "ipV6",  " |"], pad = [2, id_width, 3, text_width, 3, ip_width, 2], color = [table_color, "purple", table_color, "cyan", table_color, "yellow", table_color])        
        self.print("|" + "-"*total_width + "|" , color = table_color)
        print("\n ")
        ipv = input("Enter your choice: ")
        if ipv == "1":
            self.ip_version4 = True
        elif ipv == "2":
            self.ip_version4 = False
        else:
            self.print("please enter valid choice", color = "red")
            sys.exit()
        
    def run_command(self, command: str):
        return subprocess.run(command, text=True, shell=True, capture_output=True)

    def run_command_print(self, cmd):
        with subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=1, universal_newlines=True, shell= True) as p:
            proc = p.communicate()

    def install_libraries(self):
        if not self.check_bash_help_is_available("tar", "Usage: tar"):
            self.run_command("apt install tar")

    def print(self, text: str | list, pad: list = [], color: str|list = "white"):
        colors = {
                "red" : '\033[0;31m',
                "green" : '\033[0;32m',
                "yellow" : '\033[0;33m',
                "blue" : '\033[0;34m',
                "purple" : '\033[0;35m',
                "cyan" : '\033[0;36m',
                'white' : '\033[0m'
                }

        if isinstance(text, str) and isinstance(color, str):
            if color not in colors.keys():
                print(f"wrong Color = {color}")
                return
            text = self.truncate_and_pad(text, pad) if pad else text
            print(f"{colors[color]}{text}")
        
        if isinstance(text, list) and isinstance(color, list):
            for c in color:
                if c not in colors.keys():
                    print(f"wrong Color = {c}")
                    return
            if len(text) != len(color):
                print("please specify color for each text segment")
                return
            if pad != [] and (len(color) != len(pad) or len(text) != len(pad)):
                print("please specify color and pad for each text segment")
                return
            message = ""
            for t, c, p in zip(text, color, pad):
                _t = self.truncate_and_pad(t, p) if pad else t
                message += f"{colors[c]}{_t}"
            print(message)

    def remove_file(self, path:str = "" , pattern:str = ""):
        if os.path.isfile(path):
            os.remove(path)
            print(f"file {path} removed")
        if pattern != "":
            self.run_command(f"rm -rf {pattern}")
        
    def check_platform(self):
        machine = platform.machine().lower()
        cpus = {
        "arm64" : ["armv8", "armv8l", "arm64", "aarch64"],
        "amd64" : ["x86_64", "x64", "amd64"],
        "386" : ["i386", "i686"],
        "armv7": ["armv7l", "armv7"]
        }
        
        for c, valid_cpus in cpus.items():
            if any(p in machine for p in valid_cpus):
                self.cpu = c

        if "Windows" in platform.platform():
            print("this code not available for windows os right now")
            sys.exit(0)

    def chmod_file(self, path: str):
        if os.path.isfile(path):
            # self.run_command(f"chmod +x {path}")
            os.chmod(path, 0o775)
        else:
            print(f"file {path} not exists")

    def check_file_is_executable(self, path: str):
        if os.path.isfile(path):
            return os.access(path, os.X_OK)
        else:
            # print(f"file {path} not exists")
            return False

    def check_bash_help_is_available(self, path:str, start_text: str):
        try:
            s = self.run_command(f"{path} --help")
            if s.stdout.startswith(start_text) or s.stderr.startswith(start_text):
                return True
            else:
                return False   
        except:
            return False
        
    def download_wgcf(self):
        if os.path.isfile(self.wgcf_path):
            if self.check_file_is_executable(self.wgcf_path):
                if self.check_bash_help_is_available(self.wgcf_path, "wgcf is a utility for Cloudflare Warp"):
                    self.print("wgcf file is already exists.", color = "green")
                    return True 
                else:
                    os.remove(self.wgcf_path)
            else:
                os.remove(self.wgcf_path)                   
        
        if not os.path.isfile(self.wgcf_path):
            self.print("Downloading wgcf file ...", color = "cyan")
            if self.cpu == "arm64":
                wgcf_url = "https://github.com/Jelingam/WarpGenerator/raw/refs/heads/main/utils/wgcf"
            else:
                wgcf_url = f"https://github.com/ViRb3/wgcf/releases/download/v2.2.22/wgcf_2.2.22_linux_{self.cpu}"
            # self.run_command(f'curl -o {self.wgcf_path} -L "{wgcf_url}"')
            self.download(wgcf_url, self.wgcf_path)
            self.chmod_file(self.wgcf_path)
            if self.check_file_is_executable(self.wgcf_path):
                return True
            else:
                return False

    def download_warpendpoint(self):
        if os.path.isfile(self.warpendpoint_path):
            if self.check_file_is_executable(self.warpendpoint_path):
                if self.check_bash_help_is_available(self.warpendpoint_path, "Usage of"):
                    self.print("warpendpoint file is already exists.", color = "green")
                    return True
                else:
                    os.remove(self.warpendpoint_path)
            else:
                os.remove(self.warpendpoint_path)
        
        if not os.path.isfile(self.warpendpoint_path):
            self.print("Downloading warpendpoint file ...", color = "cyan")
            warpendpoint_url = f"https://github.com/Jelingam/WarpGenerator/raw/refs/heads/main/utils/warpendpint/{self.cpu}"
            # self.run_command(f'curl -L -o {self.warpendpoint_path} -# --retry 2 "{warpendpoint_url}"')
            self.download(warpendpoint_url, self.warpendpoint_path)
            self.chmod_file(self.warpendpoint_path)
            if self.check_file_is_executable(self.warpendpoint_path) and self.check_bash_help_is_available(self.warpendpoint_path, "Usage of"):
                self.print("warpendpoint downloaded successfuly", color = "green")
                return True
            else:
                return False

    def download_hiddifycli(self):
        gz_file = f"{self.hiddifycli_path}.tar.gz"
        if os.path.isfile(self.hiddifycli_path):
            if self.check_file_is_executable(self.hiddifycli_path):
                if self.check_bash_help_is_available(self.hiddifycli_path, "Usage:"):
                    self.print("hiddifycli file is already exists.", color = "green")
                    return True
                else:
                    os.remove(self.hiddifycli_path)
                    self.run_command(f"rm {gz_file}")
            else:
                os.remove(self.hiddifycli_path)
                self.run_command(f"rm {gz_file}")
        
        if not os.path.isfile(self.hiddifycli_path):
            self.print("Downloading hiddifycli file ...", color = "cyan")
            hiddifycli_url = f"https://github.com/hiddify/hiddify-core/releases/download/v3.1.8/hiddify-cli-linux-{self.cpu}.tar.gz"
            # self.run_command(f'curl -L -o {self.hiddifycli_path} -# --retry 2 "{hiddifycli_url}"')
            self.download(hiddifycli_url, gz_file)
            self.run_command(f"tar -xvzf {gz_file}")
            self.chmod_file(self.hiddifycli_path)
            if self.check_file_is_executable(self.hiddifycli_path) and self.check_bash_help_is_available(self.hiddifycli_path, "Usage of"):
                self.print("hiddifycli downloaded successfuly", "green")
                self.run_command(f"rm {gz_file}")
                return True
            else:
                return False

    def zero_packet_loss(self, row:list):
        loss = row[1]
        if type(loss) == str:
            loss = loss.replace("%", "")
            try:
                l = float(loss)
                if l == 0:
                    return True
            except:
                return False
        return False

    def read_endpoint_result(self):
        if os.path.isfile(self.warpendpoint_result_path):
            try:
                with open(self.warpendpoint_result_path, "rt", encoding='utf-8') as file:
                    reader = csv.reader(file)
                    self.result = list(reader)
                    self.result.pop(0)
                    return True
            except:
                return False
        return False

    def create_new_wgcf_profile(self):
        # self.remove_file(pattern = "wgcf-")
        self.run_command("wgcf register --accept-tos")
        self.run_command("wgcf generate")
    
    def download(self, url: str, fname: str):
        if os.path.isfile(fname):
            os.remove(fname)
        resp = requests.get(url, stream=True)
        total = int(resp.headers.get('content-length', 0))
        # Can also replace 'file' with a io.BytesIO object
        with open(fname, 'wb') as file, tqdm(
            desc=fname,
            total=total,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for data in resp.iter_content(chunk_size=1024):
                size = file.write(data)
                bar.update(size)

    def validate_ipv4(self, ip: str):
        striped_ip = ip.strip()
        is_ok = False
        if striped_ip.count(".") == 3:
            for i in striped_ip.split("."):
                if i.isdigit():
                    ii = int(i)
                    if ii >= 0 and ii <= 255:
                        is_ok = True
                    else:
                        is_ok = False
                        break
        return is_ok, striped_ip

    def validate_ipv4_range(self, ip_range: str):
        striped_ip_range = ip_range.strip()
        is_ok = False
        try:
            if striped_ip_range.count(".") == 3 and "/" in striped_ip_range:
                [ip0, end_range] = striped_ip_range.split("/")
                ok, ip0 = self.validate_ipv4(ip0)
                if ok:
                    start_range = ip0.split(".")[-1]
                    if start_range.isdigit() and end_range.isdigit():
                        s = int(start_range)
                        e = int(end_range)
                        if s < e:
                            is_ok = True
        except:
            print(f"ip range {striped_ip_range} is not valid")
        return is_ok, striped_ip_range

    def create_random_ips_from_ipv4_range(self, ip_range: str, count: int = 5):
        start_ip, end_range = ip_range.split("/")[0].split("."), int(ip_range.split("/")[1])
        ips = []
        start_range = int(start_ip[-1])
        if end_range - start_range > count:
            while len(ips) != count:
                rand = randint(start_range, end_range)
                ip = f"{start_ip[0]}.{start_ip[1]}.{start_ip[2]}.{rand}"
                if ip not in ips:
                    ips.append(ip)
        return ips
        
    def create_random_ips_from_ipv4_ranges(self, ip_ranges: str, count: int = 200):
        validate_ip_ranges = []
        unique_ips = []
        for _ip_range in ip_ranges:
            ok, ip_range = self.validate_ipv4_range(_ip_range)
            if ok:
                validate_ip_ranges.append(ip_range)
        all_ips = []
        while len(unique_ips) < count:
            for ip_range in validate_ip_ranges:
                ips = self.create_random_ips_from_ipv4_range(ip_range)
                for ip in ips:
                    all_ips.append(ip)
                unique_ips = list(set(all_ips))
        return unique_ips    

    def truncate_and_pad(self, string, length):
        string = string or ""
        return (string[:length-3] + '...').ljust(length) if len(string) > length else string.ljust(length)

    def random_ipv6_addr(self, network):
        """
        Generate a random IPv6 address in the given network
        Example: random_ipv6_addr("fd66:6cbb:8c10::/48")
        Returns an IPv6Address object.
        """
        net = ipaddress.IPv6Network(network)
        # Which of the network.num_addresses we want to select?
        addr_no = randint(0, net.num_addresses)
        # Create the random address by converting to a 128-bit integer, adding addr_no and converting back
        network_int = int.from_bytes(net.network_address.packed, byteorder="big")
        addr_int = network_int + addr_no
        addr = ipaddress.IPv6Address(addr_int.to_bytes(16, byteorder="big"))
        return addr

    def download_ipv6_range(self):
        url = "https://raw.githubusercontent.com/Jelingam/WarpGenerator/refs/heads/main/utils/ipv6_range.txt"
        self.download(url, self.ipv6_range_path)

    def create_random_ip_list(self, from_ip_range_file: bool = False, count: int = 200):
        if self.ip_version4:
            defult_ip_ranges = ["162.159.192.0/255", "162.159.193.0/255", "162.159.195.0/255", "188.114.96.0/255",
                                "188.114.97.0/255", "188.114.98.0/255", "188.114.99.0/255"]
            all_ips = []
            
            if from_ip_range_file:
                if os.path.isfile(self.ipv4_range_path):
                    with open(self.ipv4_range_path) as f:
                        ip_ranges = f.readlines()
                    all_ips = self.create_random_ips_from_ipv4_ranges(ip_ranges, count)
                    
                    # if ip ranges define in ip_range.txt is not enough
                    if len(all_ips) < count:
                        random_ips = self.create_random_ips_from_ipv4_ranges(defult_ip_ranges, count - len(all_ips) + 1)
                        for ip in random_ips:
                            all_ips.append(ip)
            else:
                all_ips = self.create_random_ips_from_ipv4_ranges(defult_ip_ranges, count)

            if len(all_ips) > count:
                while len(all_ips) != count:
                    all_ips.pop(randint(0, len(all_ips) - 1))
                with open(self.ip_list_path, "w") as f:
                    for i, ip in enumerate(all_ips):
                        if i == len(all_ips) - 1:
                            f.write(f"{ip}")
                        else:
                            f.write(f"{ip}\n")
                return True
            else:
                print(f"can't create {count} ips")
                return False
        
        else:

            if from_ip_range_file:
                try:
                    self.download_ipv6_range()
                    with open(self.ipv6_range_path) as f:
                        ip_ranges = f.readlines()
                    ipv6 = []
                    while len(ipv6) < count:
                        for network in ip_ranges:
                            for i in range(5):
                                ipv6.append(self.random_ipv6_addr(network.strip()))
                    with open(self.ip_list_path, "w") as f:
                        for i, ip in enumerate(ipv6):
                            if i == len(ipv6) - 1:
                                f.write(f"[{ip}]")
                            else:
                                f.write(f"[{ip}]\n")
                    return True
                except Exception as e:
                    print(e)
                    return False
            else:
                try:
                    ipv6 = []
                    for i in range(count // 2 + 1):
                        ipv60 = f"2606:4700:d0::{'%x' % randint(10, 65000)}:{'%x' % randint(10, 65000)}:{'%x' % randint(10, 65000)}:{'%x' % randint(10, 65000)}"
                        ipv61 = f"2606:4700:d1::{'%x' % randint(10, 65000)}:{'%x' % randint(10, 65000)}:{'%x' % randint(10, 65000)}:{'%x' % randint(10, 65000)}"
                        ipv6.append(ipv60)
                        ipv6.append(ipv61)
                        with open(self.ip_list_path, "w") as f:
                            for i, ip in enumerate(ipv6):
                                if i == len(ipv6) - 1:
                                    f.write(f"[{ip}]")
                                else:
                                    f.write(f"[{ip}]\n")
                    return True
                except Exception as e:
                    print(e)
                    return False
    
    def test_endpoints(self):
        max_retry = 1
        while max_retry > 0:
            if self.create_random_ip_list():
                self.run_command_print([self.warpendpoint_path, "-max",  "200"])
                if self.read_endpoint_result():
                    for row in self.result:
                        if self.zero_packet_loss(row):
                            if self.ip_version4:
                                ip = row[0].split(":")[0].strip()
                                port = row[0].split(":")[1].strip()
                            else:
                                ip = row[0].split("[")[1].split("]")[0]
                                port = row[0].split("]")[1].split(":")[-1]
                            ping = row[-1].strip().split()[0]
                            self.zero_packet_loss_ips.append([ip , port, ping])
                if len(self.zero_packet_loss_ips) >= self.minimum_config:
                    break
            max_retry -= 1
        
        if len(self.zero_packet_loss_ips) < self.minimum_config:
            self.print(f"Sorry! we cant find at least {self.minimum_config} clean IP for you in defined ip range", color = "red")
            self.print(f"consider to turn you VPN off and provide another Cloudflare ip range in 'ip_range.txt file'", color = "red")
            sys.exit(0)
                
        # self.run_command("clear")
        os.system('cls||clear')
        id_width = 4
        if self.ip_version4:
            ip_width = 16
        else:
            ip_width = 36
        port_width = 5
        ping_width = 5
        total_width = id_width + ip_width + port_width + ping_width + 9
        
        print("|-" + "-" * total_width + "-|")
        print(f"| {'ID'.ljust(id_width)} | {'IP'.ljust(ip_width)} | {'Port'.ljust(port_width)} | {'Ping'.ljust(ping_width)} |")
        print("|-" + "-" * total_width + "-|")
        
        for i, row in enumerate(self.zero_packet_loss_ips):
            ip = self.truncate_and_pad(row[0], ip_width)
            port = self.truncate_and_pad(row[1], port_width)
            ping = self.truncate_and_pad(row[2], ping_width)
            print(f"| {str(i+1).ljust(id_width)} | {ip} | {port} | {ping} |")
        print("|-" + "-" * total_width + "-|\n")
        self.print(f"we have find {len(self.zero_packet_loss_ips)} ip with zero packet loss", color = "green")

    def generate_keys_online(self):
        try:
            cmd = "curl -m5 -sSL https://wg-key.forvps.gq/"
            out = self.run_command(cmd).stdout
            public_key = out.split("\n")[0].split(":")[1].strip()
            private_key = out.split("\n")[1].split(":")[1].strip()
            if len(public_key) == 44 and len(private_key) == 44:
                return public_key, private_key
        except:
            return None, None

    def generate_keys_offline(self):
        p = self.wgcf_path.replace("./", "")
        wait_time = 10
        max_retry = 2
        def create_wgcf_account():
            print(f"Register a free account in cloudflare ...")
            args = " register --accept-tos"
            file = "wgcf-account.toml"
            retry = 0
            while not os.path.isfile(file) and retry < max_retry:
                if retry % 2 == 0:
                    cmd = self.wgcf_path + args
                else:
                    cmd = p + args
                start_time = time.time()
                self.run_command(cmd)
                while time.time() - start_time < wait_time:
                    if os.path.isfile(file):
                        self.print("\naccount registerd successfully", color = "green")
                        return
                    time.sleep(1)
                    print(f"try = {retry + 1} of {max_retry}\tremainimg time = {int(wait_time - (time.time() - start_time))}", end="\r")
                retry += 1

        def create_wgcf_profile():
            print(f"Create a profile for this account ...")
            args = " generate"
            file = "wgcf-profile.conf"
            retry = 0
            while not os.path.isfile(file) and retry < max_retry:
                if retry % 2 == 0:
                    cmd = self.wgcf_path + args
                else:
                    cmd = p + args
                start_time = time.time()
                self.run_command(cmd)
                while time.time() - start_time < wait_time:
                    if os.path.isfile(file):
                        self.print("\nprofile created successfully", color = "green")
                        return
                    time.sleep(1)
                    print(f"try = {retry + 1} of {max_retry}\tremainimg time = {int(wait_time - (time.time() - start_time))}", end="\r")
                retry += 1

        try:
            self.remove_file(pattern = "wgcf-*")
            create_wgcf_account()
            if os.path.isfile("wgcf-account.toml"):
                create_wgcf_profile()
            else:
                print("We can't register an account on Cloudflare; this problem happens because of these two issues:")
                print("1. Turn on VPN: Please consider this tool can't be run with VPN turned on.")
                print("2. According to issue #356 on ViRb3/wgcf: on some android devieces 'wgcf' may not working.")
                print("for solving this problem you can build this file from source.")
                option = input("Do you want build wgcf from source  (y/n):")
                if option == "n":
                    sys.exit()
                if option == "y":
                    self.build_wgcf_from_source()


            if os.path.isfile(self.wgcf_profile_path):
                with open(self.wgcf_profile_path, "r") as file:
                    lines = file.readlines()
                private_key = lines[1].split(" ")[2].strip()
                public_key = lines[7].split(" ")[2].strip()
                if len(public_key) == 44 and len(private_key) == 44:
                    return public_key, private_key
            return None, None
        except:
            return None, None    

    def build_wgcf_from_source(self):
        print("installing golang & wget")
        self.run_command("pkg install golang wget")
        
        print("download source file of wgcf")
        version = "2.2.22"
        self.run_command(f"wget https://github.com/ViRb3/wgcf/archive/refs/tags/v{version}.tar.gz")
        
        print("building wgcf. it takes about 5 min. don't worry, This process needs to be done once.")
        self.run_command(f"tar xzf v{version}.tar.gz")
        self.run_command(f"rm v{version}.tar.gz")
        self.run_command(f"cd wgcf-{version}")
        self.run_command("go build")
        self.run_command("cd .. && cp wgcf-{version}/wgcf ./")
        self.run_command(f"rm -rf wgcf-{version}")
        self.chmod_file(self.wgcf_path)
        self.generate_keys_offline()
        
    def generate_wiregurd_configs(self, online: bool = False, count: int = 50):
        
        if online:
            public_key, private_key = self.generate_keys_online()
            if not public_key:
                self.print("Generate keys online are not reachable", color = "red")
                online = False
        
        if not online:
            public_key, private_key = self.generate_keys_offline()
            if not public_key:
                self.print("Can't Generate offline keys with wgcf", color = "red")
                sys.exit(0)
        
        # return public_key, private_key
        
        for i, row in enumerate(self.zero_packet_loss_ips):
            [ip, port, _] = row
            w = WireguardConfig(f"W{i+1}", ip, port, public_key, private_key)
            self.wireguard_configs.append(w.config)
            if i > count:
                break
        
        outbounds = {"outbounds": []}
        for item in self.wireguard_configs:
            outbounds["outbounds"].append(item)
        now = datetime.datetime.now().strftime("%Y.%m.%d-%H.%M.%S")
        self.output_configs_path = f"./Wireguard_configs_{now}.txt"
        with open (self.output_configs_path, "w") as file:
            file.write("//profile-title: jelingam Scanner Warps\n")
            json.dump(outbounds, file, indent = 2)
        self.print(f"{len(self.zero_packet_loss_ips)} wireguard configs generated for hiddify in {self.output_configs_path}", color = "green")
        
    def copy_configs_to_device(self):
        storage_access_granted = False
        res = self.run_command("ls /storage/emulated/0/")
        out, err = res.stdout, res.stderr
        if not "denied" in out.lower() and not "denied" in err.lower():
            storage_access_granted = True
        # else:
        #     self.run_command("termux-setup-storage")
            
        #     res = self.run_command("")
        #     res = self.run_command("ls /storage/emulated/")
        #     out, err = res.stdout, res.stderr
        #     print(f"out = {out}")
        if storage_access_granted:
            self.run_command(f"cp {self.output_configs_path} /storage/emulated/0/")
            print(f"you can find this file in your android storage device")

    def generate_random_noise(self, count, fixed_noises: dict = {}):
        mtu_options = fixed_noises.get("mtu") if fixed_noises.get("mtu") else self.noine_options["mtu"]
        fake_packets_mode_options = fixed_noises.get("fake_packets_mode") if fixed_noises.get("fake_packets_mode") else self.noine_options["fake_packets_mode"]
        fake_packets_delay_options = fixed_noises.get("fake_packets_delay") if fixed_noises.get("fake_packets_delay") else self.noine_options["fake_packets_delay"]
        fake_packets_size_options = fixed_noises.get("fake_packets_size") if fixed_noises.get("fake_packets_size") else self.noine_options["fake_packets_size"]
        fake_packets_options = fixed_noises.get("fake_packets") if fixed_noises.get("fake_packets") else self.noine_options["fake_packets"]
        random_noises = []
        # while len(random_noises) < count:
        
        # TODO complete this function, create a random option from availabe and user select options
      
class WireguardConfig:
    def __init__(self, tag: str , ip: str, port: str | int, public_key: str, private_key: str, noise: dict = {}):       
        self.config = {
            "type": "wireguard",
            "tag": tag,
            "local_address":       [
            "172.16.0.2/24",
            "2606:4700:110:8056:6ec9:563a:d8e7:5097/128"
            ],
            "private_key": private_key,
            "server": ip,
            "server_port": int(port),
            "peer_public_key": public_key,
            "mtu": noise.get("mtu") if noise.get("mtu") else 1280,
            "fake_packets": noise.get("fake_packets") if noise.get("fake_packets") else "40-80",
            "fake_packets_size": noise.get("fake_packets_size") if noise.get("fake_packets_size") else "40-100",
            "fake_packets_delay": noise.get("fake_packets_delay") if noise.get("fake_packets_delay") else "5-10",
            "fake_packets_mode": noise.get("fake_packets_mode") if noise.get("fake_packets_mode") else "m4"
        }


if __name__ == "__main__":
    w = Warp()
