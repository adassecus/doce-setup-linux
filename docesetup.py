#!/usr/bin/env python3
import os
import sys
import subprocess
import platform
import re
import time
import shutil
import socket
import getpass
from pathlib import Path
import pwd


def execute_command(command, silent=True):
    try:
        if silent:
            with open(os.devnull, 'w') as DEVNULL:
                return subprocess.run(command, shell=True, stdout=DEVNULL, stderr=DEVNULL).returncode
        else:
            return subprocess.run(command, shell=True).returncode
    except Exception as e:
        print(f"Erro ao executar comando: {command} - {str(e)}")
        return -1


def get_command_output(command):
    try:
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout.strip()
    except Exception as e:
        print(f"Erro ao obter saída do comando: {command} - {str(e)}")
        return ""


def detect_distro():
    if os.path.exists('/etc/os-release'):
        with open('/etc/os-release', 'r') as f:
            lines = f.readlines()
            info = {}
            for line in lines:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    info[key] = value.strip('"')
            
            distro = info.get('ID', '').lower()
            version = info.get('VERSION_ID', '').strip('"')
            return distro, version
    
    if shutil.which('lsb_release'):
        distro = get_command_output("lsb_release -si").lower()
        version = get_command_output("lsb_release -sr")
        return distro, version
    
    if os.path.exists('/etc/debian_version'):
        with open('/etc/debian_version', 'r') as f:
            version = f.read().strip()
        return 'debian', version
    
    return platform.system().lower(), platform.release()


def setup_package_manager(distro):
    if distro in ['ubuntu', 'debian', 'linuxmint', 'pop', 'elementary', 'zorin']:
        return "apt-get", "apt-get update", "apt-get install -y"
    elif distro in ['fedora', 'centos', 'rhel', 'rocky', 'almalinux']:
        if shutil.which('dnf'):
            return "dnf", "dnf check-update", "dnf install -y"
        else:
            return "yum", "yum check-update", "yum install -y"
    elif distro in ['arch', 'manjaro', 'endeavouros']:
        return "pacman", "pacman -Sy", "pacman -S --noconfirm"
    elif distro in ['opensuse', 'suse']:
        return "zypper", "zypper refresh", "zypper install -y"
    else:
        if shutil.which('apt-get'):
            return "apt-get", "apt-get update", "apt-get install -y"
        elif shutil.which('dnf'):
            return "dnf", "dnf check-update", "dnf install -y"
        elif shutil.which('yum'):
            return "yum", "yum check-update", "yum install -y"
        elif shutil.which('pacman'):
            return "pacman", "pacman -Sy", "pacman -S --noconfirm"
        elif shutil.which('zypper'):
            return "zypper", "zypper refresh", "zypper install -y"
        else:
            return "", "echo 'Atualização não disponível'", "echo 'Instalação não disponível'"


def install_deps(pkg_install, packages):
    for pkg in packages:
        if not shutil.which(pkg):
            print(f"Instalando {pkg}...")
            execute_command(f"{pkg_install} {pkg}")


def colorize(color, text):
    colors = {
        'red': '\033[0;31m',
        'green': '\033[0;32m',
        'yellow': '\033[0;33m',
        'blue': '\033[0;34m',
        'purple': '\033[0;35m',
        'cyan': '\033[0;36m',
        'reset': '\033[0m'
    }
    return f"{colors.get(color, '')}{text}{colors['reset']}"


def show_banner(distro, version):
    script_version = "1.0.0"
    os.system('clear')
    print(f"\n{colorize('cyan', '╔═══════════════════════════════════════════╗')}")
    print(f"{colorize('cyan', '║')}       {colorize('yellow', '🍬 Assistente de Configuração')}        {colorize('cyan', '║')}")
    print(f"{colorize('cyan', '║')}        {colorize('green', f'Universal Linux Setup v{script_version}')}       {colorize('cyan', '║')}")
    print(f"{colorize('cyan', '╚═══════════════════════════════════════════╝')}")
    print(f"\n{colorize('blue', f'Sistema detectado: {distro} {version}')}\n")


def ask(question):
    while True:
        response = input(f"{colorize('yellow', question)} (s/n): ").lower()
        if response in ['s', 'sim', 'y', 'yes']:
            return True
        elif response in ['n', 'nao', 'não', 'no']:
            return False
        else:
            print("Por favor, responda com s ou n.")


def check_root():
    if os.geteuid() != 0:
        print("Este script precisa ser executado como root.")
        print("Por favor, execute com sudo ou como usuário root.")
        sys.exit(1)


def detect_ssh_port():
    if os.path.exists('/etc/ssh/sshd_config'):
        with open('/etc/ssh/sshd_config', 'r') as f:
            for line in f:
                if line.strip().startswith('Port '):
                    port = line.strip().split()[1]
                    print(f"🔍 Porta SSH detectada: {port}")
                    return port
    
    print("Arquivo de configuração SSH não encontrado. Assumindo porta padrão 22.")
    return "22"


def configure_firewall(distro, ssh_port):
    print("🔥 Configurando firewall...")
    
    if shutil.which('ufw') or distro in ['ubuntu', 'debian', 'linuxmint', 'pop', 'elementary', 'zorin']:
        if not shutil.which('ufw'):
            execute_command("apt-get install -y ufw")
        
        print("Usando UFW como firewall.")
        execute_command("echo y | ufw reset")
        execute_command("ufw default deny incoming")
        execute_command("ufw default allow outgoing")
        execute_command(f"ufw limit {ssh_port}/tcp")
        
        common_ports = ["25565", "27015", "27016", "7777", "2302", "6667", "28960", 
                         "44405", "3724", "6112", "6881", "3784", "5000", "443", 
                         "80", "5222", "5223", "3478", "5938", "8080"]
        
        for porta in common_ports:
            execute_command(f"ufw allow {porta}")
        
        execute_command("ufw logging on")
        execute_command("echo y | ufw enable")
        
    elif shutil.which('firewall-cmd') or distro in ['fedora', 'centos', 'rhel', 'rocky', 'almalinux']:
        if not shutil.which('firewall-cmd'):
            execute_command("dnf install -y firewalld || yum install -y firewalld")
        
        print("Usando FirewallD como firewall.")
        execute_command("systemctl enable firewalld")
        execute_command("systemctl start firewalld")
        execute_command(f"firewall-cmd --permanent --add-port={ssh_port}/tcp")
        
        common_ports = ["25565", "27015", "27016", "7777", "2302", "6667", "28960", 
                         "44405", "3724", "6112", "6881", "3784", "5000", "443", 
                         "80", "5222", "5223", "3478", "5938", "8080"]
        
        for porta in common_ports:
            execute_command(f"firewall-cmd --permanent --add-port={porta}/tcp")
            execute_command(f"firewall-cmd --permanent --add-port={porta}/udp")
        
        execute_command("firewall-cmd --reload")
        
    elif shutil.which('iptables'):
        print("Usando IPTables como firewall.")
        
        if distro in ['ubuntu', 'debian', 'linuxmint']:
            execute_command("apt-get install -y iptables-persistent")
        
        execute_command("iptables -F")
        execute_command("iptables -X")
        execute_command("iptables -t nat -F")
        execute_command("iptables -t nat -X")
        execute_command("iptables -t mangle -F")
        execute_command("iptables -t mangle -X")
        
        execute_command("iptables -P INPUT DROP")
        execute_command("iptables -P FORWARD DROP")
        execute_command("iptables -P OUTPUT ACCEPT")
        
        execute_command("iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT")
        execute_command("iptables -A INPUT -i lo -j ACCEPT")
        execute_command(f"iptables -A INPUT -p tcp --dport {ssh_port} -j ACCEPT")
        
        common_ports = ["25565", "27015", "27016", "7777", "2302", "6667", "28960", 
                         "44405", "3724", "6112", "6881", "3784", "5000", "443", 
                         "80", "5222", "5223", "3478", "5938", "8080"]
        
        for porta in common_ports:
            execute_command(f"iptables -A INPUT -p tcp --dport {porta} -j ACCEPT")
            execute_command(f"iptables -A INPUT -p udp --dport {porta} -j ACCEPT")
        
        if distro in ['ubuntu', 'debian', 'linuxmint']:
            execute_command("netfilter-persistent save")
        elif distro in ['fedora', 'centos', 'rhel']:
            execute_command("service iptables save")
        else:
            execute_command("mkdir -p /etc/iptables")
            execute_command("iptables-save > /etc/iptables/rules.v4")
            
            service_file = """[Unit]
Description=Restore iptables rules
After=network.target

[Service]
Type=oneshot
ExecStart=/sbin/iptables-restore /etc/iptables/rules.v4
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
"""
            with open('/etc/systemd/system/iptables-restore.service', 'w') as f:
                f.write(service_file)
            
            execute_command("systemctl enable iptables-restore.service")
    else:
        print("Nenhum firewall detectado. Tentando instalar UFW...")
        execute_command("apt-get install -y ufw || dnf install -y ufw || yum install -y ufw || pacman -S --noconfirm ufw")
        if shutil.which('ufw'):
            configure_firewall(distro, ssh_port)
        else:
            print("Não foi possível instalar um firewall. A configuração do firewall foi ignorada.")
            return
    
    print("✅ Firewall configurado com sucesso!")
    time.sleep(2)


def configure_fail2ban(distro, ssh_port):
    print("🛡️ Instalando e configurando o fail2ban...")
    
    if not shutil.which('fail2ban-server'):
        execute_command(f"apt-get install -y fail2ban || dnf install -y fail2ban || yum install -y fail2ban || pacman -S --noconfirm fail2ban")
    
    os.makedirs('/etc/fail2ban/jail.d', exist_ok=True)
    os.makedirs('/etc/fail2ban/filter.d', exist_ok=True)
    
    log_paths = {
        'auth': next((p for p in ['/var/log/auth.log', '/var/log/secure'] if os.path.exists(p)), '/var/log/auth.log'),
        'apache': next((p for p in ['/var/log/apache2/access.log', '/var/log/httpd/access_log'] if os.path.exists(p)), '/var/log/apache2/access.log')
    }
    
    jail_config = f"""[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = {ssh_port}
filter = sshd
logpath = {log_paths['auth']}
maxretry = 3
bantime = 3600

[http-get-dos]
enabled = true
port = http,https
filter = http-get-dos
logpath = {log_paths['apache']}
maxretry = 300
findtime = 300
bantime = 3600
"""
    
    http_get_dos_filter = """[Definition]
failregex = ^<HOST> -.*"(GET|POST).*
ignoreregex =
"""
    
    game_server_filter = """[Definition]
failregex = ^<HOST> -.*"(GET|POST).*
ignoreregex =
"""
    
    with open('/etc/fail2ban/jail.local', 'w') as f:
        f.write(jail_config)
    
    with open('/etc/fail2ban/filter.d/http-get-dos.conf', 'w') as f:
        f.write(http_get_dos_filter)
    
    with open('/etc/fail2ban/filter.d/game-server.conf', 'w') as f:
        f.write(game_server_filter)
    
    if shutil.which('systemctl'):
        execute_command("systemctl enable fail2ban")
        execute_command("systemctl restart fail2ban")
    elif shutil.which('service'):
        execute_command("service fail2ban enable")
        execute_command("service fail2ban restart")
    else:
        execute_command("/etc/init.d/fail2ban restart")
    
    print("✅ Fail2ban configurado com sucesso!")
    time.sleep(2)


def configure_sysctl_protection():
    print("🔧 Configurando parâmetros de rede para proteção adicional...")
    
    if not os.path.exists('/etc/sysctl.conf'):
        open('/etc/sysctl.conf', 'w').close()
    
    with open('/etc/sysctl.conf', 'r') as f:
        sysctl_content = f.read()
    
    parameters_to_remove = [
        'net.ipv4.tcp_tw_recycle', 'net.ipv4.conf.all.rp_filter', 'net.ipv4.conf.default.rp_filter',
        'net.ipv4.icmp_echo_ignore_broadcasts', 'net.ipv4.tcp_syncookies', 'net.ipv4.tcp_max_syn_backlog',
        'net.ipv4.tcp_synack_retries', 'net.ipv4.tcp_syn_retries', 'net.ipv4.tcp_tw_reuse',
        'net.ipv4.icmp_ratelimit', 'net.ipv4.ipfrag_low_thresh', 'net.ipv4.ipfrag_time',
        'net.ipv4.tcp_rfc1337', 'net.ipv4.tcp_timestamps', 'net.ipv4.conf.all.accept_source_route',
        'net.ipv4.conf.all.accept_redirects', 'net.ipv4.conf.all.secure_redirects'
    ]
    
    for param in parameters_to_remove:
        sysctl_content = re.sub(fr'^{param}.*\n?', '', sysctl_content, flags=re.MULTILINE)
    
    optimization_config = """
# Proteção contra ataques de rede
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_max_syn_backlog = 2048
net.ipv4.tcp_synack_retries = 2
net.ipv4.tcp_syn_retries = 5
net.ipv4.tcp_tw_reuse = 1
net.ipv4.icmp_ratelimit = 100
net.ipv4.ipfrag_low_thresh = 196608
net.ipv4.ipfrag_time = 60
net.ipv4.tcp_rfc1337 = 1
net.ipv4.tcp_timestamps = 0
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.all.secure_redirects = 1

# Otimização de desempenho
net.core.netdev_max_backlog = 5000
net.core.rmem_max = 16777216
net.core.somaxconn = 1024
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216
net.ipv4.tcp_fin_timeout = 15
net.ipv4.tcp_keepalive_time = 300
net.ipv4.tcp_keepalive_probes = 5
net.ipv4.tcp_keepalive_intvl = 15

# Otimização de memória
vm.swappiness = 10
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5
vm.vfs_cache_pressure = 50
"""
    
    with open('/etc/sysctl.conf', 'w') as f:
        f.write(sysctl_content + optimization_config)
    
    sysctl_success = execute_command("sysctl -p") == 0
    
    if not sysctl_success:
        print("Erro ao aplicar configurações sysctl. Verificando compatibilidade...")
        with open('/etc/sysctl.conf', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    execute_command(f"sysctl -w {line}")
    
    print("✅ Parâmetros de rede compatíveis aplicados com sucesso!")
    time.sleep(2)


def create_ssh_port_service(distro):
    print("🔧 Configurando serviço para detectar e liberar porta SSH...")
    
    script_content = """#!/usr/bin/env python3
import os
import subprocess
import shutil
import re

def execute_command(command):
    try:
        subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception:
        pass

def detect_ssh_port():
    if os.path.exists('/etc/ssh/sshd_config'):
        with open('/etc/ssh/sshd_config', 'r') as f:
            for line in f:
                if line.strip().startswith('Port '):
                    return line.strip().split()[1]
    return "22"

def main():
    ssh_port = detect_ssh_port()
    
    if shutil.which('ufw'):
        status_output = subprocess.run("ufw status", shell=True, stdout=subprocess.PIPE, text=True).stdout
        if f"{ssh_port}/tcp" not in status_output:
            execute_command(f"ufw allow {ssh_port}/tcp")
            execute_command("ufw reload")
    elif shutil.which('firewall-cmd'):
        list_ports = subprocess.run("firewall-cmd --list-ports", shell=True, stdout=subprocess.PIPE, text=True).stdout
        if f"{ssh_port}/tcp" not in list_ports:
            execute_command(f"firewall-cmd --permanent --add-port={ssh_port}/tcp")
            execute_command("firewall-cmd --reload")
    elif shutil.which('iptables'):
        iptables_list = subprocess.run("iptables -L INPUT -n", shell=True, stdout=subprocess.PIPE, text=True).stdout
        if f"dpt:{ssh_port}" not in iptables_list:
            execute_command(f"iptables -A INPUT -p tcp --dport {ssh_port} -j ACCEPT")
            if shutil.which('netfilter-persistent'):
                execute_command("netfilter-persistent save")
            elif os.path.exists('/etc/iptables'):
                execute_command("iptables-save > /etc/iptables/rules.v4")

if __name__ == "__main__":
    main()
"""
    
    with open('/usr/local/bin/detect_ssh_port.py', 'w') as f:
        f.write(script_content)
    
    os.chmod('/usr/local/bin/detect_ssh_port.py', 0o755)
    
    if os.path.exists('/etc/systemd/system'):
        service_content = """[Unit]
Description=Detectar e liberar porta SSH no firewall
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/detect_ssh_port.py
RemainAfterExit=true

[Install]
WantedBy=multi-user.target
"""
        
        with open('/etc/systemd/system/detect-ssh-port.service', 'w') as f:
            f.write(service_content)
        
        execute_command("systemctl daemon-reload")
        execute_command("systemctl enable detect-ssh-port.service")
        execute_command("systemctl start detect-ssh-port.service")
    else:
        try:
            current_crontab = get_command_output("crontab -l 2>/dev/null") or ""
            if "@reboot /usr/local/bin/detect_ssh_port.py" not in current_crontab:
                with open('/tmp/crontab.txt', 'w') as f:
                    f.write(current_crontab + "\n@reboot /usr/local/bin/detect_ssh_port.py\n")
                execute_command("crontab /tmp/crontab.txt")
                os.remove('/tmp/crontab.txt')
        except Exception:
            pass
        
        if os.path.exists('/etc/rc.local'):
            with open('/etc/rc.local', 'r') as f:
                rc_content = f.read()
            
            if 'exit 0' in rc_content:
                rc_content = rc_content.replace('exit 0', '/usr/local/bin/detect_ssh_port.py\nexit 0')
            else:
                rc_content += '\n/usr/local/bin/detect_ssh_port.py\nexit 0\n'
            
            with open('/etc/rc.local', 'w') as f:
                f.write(rc_content)
        else:
            with open('/etc/rc.local', 'w') as f:
                f.write("""#!/bin/bash
/usr/local/bin/detect_ssh_port.py
exit 0
""")
            os.chmod('/etc/rc.local', 0o755)
    
    print("✅ Serviço de detecção de porta SSH configurado com sucesso!")
    time.sleep(2)


def change_locale():
    print("Escolha um idioma da lista abaixo digitando o número correspondente:")
    print("1. 🇺🇸 en_US.UTF-8 - Inglês (Estados Unidos)")
    print("2. 🇪🇸 es_ES.UTF-8 - Espanhol (Espanha)")
    print("3. 🇫🇷 fr_FR.UTF-8 - Francês (França)")
    print("4. 🇩🇪 de_DE.UTF-8 - Alemão (Alemanha)")
    print("5. 🇮🇹 it_IT.UTF-8 - Italiano (Itália)")
    print("6. 🇧🇷 pt_BR.UTF-8 - Português (Brasil)")
    print("7. 🇷🇺 ru_RU.UTF-8 - Russo (Rússia)")
    print("8. 🇨🇳 zh_CN.UTF-8 - Chinês (China)")
    print("9. 🇯🇵 ja_JP.UTF-8 - Japonês (Japão)")
    print("10. 🇰🇷 ko_KR.UTF-8 - Coreano (Coreia)")
    print("11. 🇸🇦 ar_SA.UTF-8 - Árabe (Arábia Saudita)")

    try:
        lang_choice = int(input("Digite o número do idioma escolhido: "))
    except ValueError:
        lang_choice = 0

    locales = ["en_US.UTF-8", "es_ES.UTF-8", "fr_FR.UTF-8", "de_DE.UTF-8", "it_IT.UTF-8", 
               "pt_BR.UTF-8", "ru_RU.UTF-8", "zh_CN.UTF-8", "ja_JP.UTF-8", "ko_KR.UTF-8", "ar_SA.UTF-8"]
    
    if 1 <= lang_choice <= 11:
        new_locale = locales[lang_choice-1]
    else:
        print("Escolha inválida. Usando en_US.UTF-8 por padrão.")
        new_locale = "en_US.UTF-8"

    print(f"Configurando o idioma do sistema para {new_locale}...")
    
    distro, _ = detect_distro()
    
    if distro in ['ubuntu', 'debian', 'linuxmint', 'pop', 'elementary', 'zorin']:
        execute_command("apt-get install -y locales")
        
        if os.path.exists('/etc/locale.gen'):
            with open('/etc/locale.gen', 'r') as f:
                content = f.read()
            content = re.sub(f"^#\s*{new_locale}", f"{new_locale}", content, flags=re.MULTILINE)
            with open('/etc/locale.gen', 'w') as f:
                f.write(content)
        else:
            with open('/etc/locale.gen', 'w') as f:
                f.write(f"{new_locale} UTF-8\n")
        
        execute_command("locale-gen")
        execute_command(f"update-locale LANG={new_locale} LANGUAGE={new_locale} LC_ALL={new_locale}")
    elif distro in ['fedora', 'centos', 'rhel', 'rocky', 'almalinux']:
        lang_code = new_locale.split('_')[0]
        execute_command(f"dnf install -y glibc-langpack-{lang_code} || yum install -y glibc-langpack-{lang_code}")
        execute_command(f"localectl set-locale LANG={new_locale}")
    elif distro in ['arch', 'manjaro', 'endeavouros']:
        with open('/etc/locale.conf', 'w') as f:
            f.write(f"LANG={new_locale}\n")
        with open('/etc/locale.gen', 'w') as f:
            f.write(f"{new_locale} UTF-8\n")
        execute_command("locale-gen")
    elif distro in ['opensuse', 'suse']:
        with open('/etc/locale.conf', 'w') as f:
            f.write(f"LANG={new_locale}\n")
    else:
        with open('/etc/locale.conf', 'w') as f:
            f.write(f"LANG={new_locale}\n")
        if shutil.which('locale-gen'):
            with open('/etc/locale.gen', 'a') as f:
                f.write(f"{new_locale} UTF-8\n")
            execute_command("locale-gen")
    
    os.environ['LANG'] = new_locale
    os.environ['LANGUAGE'] = new_locale
    os.environ['LC_ALL'] = new_locale
    
    print(f"Idioma do sistema alterado para {new_locale} com sucesso! 🎉")
    time.sleep(2)


def optimize_network():
    print("🌐 Otimizando configurações de rede...")
    
    for iface in os.listdir('/sys/class/net/'):
        if iface != 'lo':
            execute_command(f"ethtool -s {iface} speed 1000 duplex full autoneg on")
            execute_command(f"ip link set {iface} txqueuelen 1000")
            execute_command(f"ethtool -G {iface} rx 4096 tx 4096")
            execute_command(f"ethtool -K {iface} gro on gso on tso on")
    
    print("✅ Configuração de rede otimizada com sucesso!")
    time.sleep(2)


def change_ssh_settings():
    if not os.path.exists('/etc/ssh/sshd_config'):
        print("Arquivo de configuração SSH não encontrado.")
        return False
    
    def update_config(filename, param, value):
        with open(filename, 'r') as f:
            content = f.read()
        
        if re.search(rf'^[#\s]*{param}\s', content, re.MULTILINE):
            content = re.sub(rf'^[#\s]*{param}.*', f'{param} {value}', content, flags=re.MULTILINE)
        else:
            content += f'\n{param} {value}'
        
        with open(filename, 'w') as f:
            f.write(content)
    
    change_port = ask("🔧 Deseja alterar a porta do SSH?")
    if change_port:
        new_port = input("Digite a nova porta do SSH: ")
        try:
            new_port = int(new_port)
            if new_port < 1 or new_port > 65535:
                print("Porta inválida. Usando porta 22.")
                new_port = 22
        except ValueError:
            print("Porta inválida. Usando porta 22.")
            new_port = 22
        
        print(f"Alterando a porta do SSH para {new_port}...")
        update_config('/etc/ssh/sshd_config', 'Port', new_port)
    
    increase_timeout = ask("⏳ Deseja aumentar o limite de timeout do SSH para 5 horas?")
    if increase_timeout:
        print("Aumentando o limite de timeout do SSH para 5 horas...")
        update_config('/etc/ssh/sshd_config', 'ClientAliveInterval', '290')
        update_config('/etc/ssh/sshd_config', 'ClientAliveCountMax', '63')
    
    if change_port or increase_timeout:
        execute_command("systemctl restart sshd || service sshd restart || /etc/init.d/ssh restart")
        print("Configurações SSH atualizadas com sucesso!")
    
    return change_port


def change_root_password():
    print("🔑 Vamos alterar a senha do root. Por favor, digite a nova senha:")
    
    password = getpass.getpass()
    if not password:
        print("Senha vazia não permitida.")
        return
    
    execute_command(f"echo 'root:{password}' | chpasswd")
    
    def update_config(filename, param, value):
        with open(filename, 'r') as f:
            content = f.read()
        
        if re.search(rf'^[#\s]*{param}\s', content, re.MULTILINE):
            content = re.sub(rf'^[#\s]*{param}.*', f'{param} {value}', content, flags=re.MULTILINE)
        else:
            content += f'\n{param} {value}'
        
        with open(filename, 'w') as f:
            f.write(content)
    
    if os.path.exists('/etc/ssh/sshd_config'):
        update_config('/etc/ssh/sshd_config', 'PermitRootLogin', 'yes')
        update_config('/etc/ssh/sshd_config', 'PasswordAuthentication', 'yes')
        execute_command("systemctl restart sshd || service sshd restart || /etc/init.d/ssh restart")
    
    if ask("🔄 Deseja aplicar a mesma senha do root para todos os outros usuários?"):
        print("Aplicando a mesma senha do root para todos os outros usuários...")
        for user in pwd.getpwall():
            if user.pw_uid >= 1000 and user.pw_uid < 65534:
                execute_command(f"echo '{user.pw_name}:{password}' | chpasswd")
    
    print("Senhas alteradas com sucesso!")
    time.sleep(2)


def install_lamp_stack(pkg_manager, pkg_install):
    apache_installed = False
    
    if ask("🌐 Deseja instalar o Apache? Isso é necessário para instalar o MariaDB e o phpMyAdmin posteriormente."):
        print("Instalando dependências do Apache...")
        execute_command(f"{pkg_install} apt-transport-https ca-certificates curl software-properties-common")
        
        print("Instalando Apache...")
        if execute_command(f"{pkg_install} apache2 || {pkg_install} httpd") == 0:
            execute_command("systemctl start apache2 || systemctl start httpd || service apache2 start || service httpd start")
            execute_command("systemctl enable apache2 || systemctl enable httpd || chkconfig apache2 on || chkconfig httpd on")
            print("Apache instalado com sucesso! 🌐")
            apache_installed = True
        else:
            print("Falha ao instalar o Apache.")
        
        time.sleep(2)
        os.system('clear')
    
    mariadb_installed = False
    if apache_installed and ask("🗄️ Deseja instalar o MariaDB?"):
        print("Instalando MariaDB...")
        
        if pkg_manager in ['apt-get', 'apt']:
            execute_command(f"{pkg_install} software-properties-common dirmngr")
            execute_command(f"{pkg_install} mariadb-server mariadb-client")
        elif pkg_manager in ['dnf', 'yum']:
            execute_command(f"{pkg_install} mariadb-server")
        elif pkg_manager == 'pacman':
            execute_command(f"{pkg_install} mariadb")
            execute_command("mariadb-install-db --user=mysql --basedir=/usr --datadir=/var/lib/mysql")
        else:
            execute_command(f"{pkg_install} mariadb-server || {pkg_install} mariadb")
        
        execute_command("systemctl start mariadb || systemctl start mysql || service mariadb start || service mysql start")
        execute_command("systemctl enable mariadb || systemctl enable mysql || chkconfig mariadb on || chkconfig mysql on")
        
        print("Por favor, digite a senha do root para o MariaDB:")
        mariadb_root_password = getpass.getpass()
        
        print("Configurando MariaDB...")
        # Criando script para configuração segura
        with open('/tmp/mysql_secure.sql', 'w') as f:
            f.write(f"""
UPDATE mysql.user SET Password=PASSWORD('{mariadb_root_password}') WHERE User='root';
DELETE FROM mysql.user WHERE User='';
DROP DATABASE IF EXISTS test;
DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';
FLUSH PRIVILEGES;
""")
        
        execute_command("mysql -u root < /tmp/mysql_secure.sql")
        os.remove('/tmp/mysql_secure.sql')
        
        # Configurar otimizações no MariaDB
        config_file = ""
        for path in ['/etc/mysql/mariadb.conf.d/50-server.cnf', '/etc/my.cnf', '/etc/mysql/my.cnf']:
            if os.path.exists(path):
                config_file = path
                break
        
        if config_file:
            with open(config_file, 'r') as f:
                content = f.read()
            
            if '[mysqld]' not in content:
                content += "\n[mysqld]\n"
            
            # Adicionar otimizações
            optimizations = {
                'sql_mode': '""',
                'innodb_buffer_pool_size': '1G',
                'innodb_log_file_size': '256M',
                'innodb_file_per_table': '1',
                'max_connections': '200',
                'query_cache_size': '64M',
                'query_cache_type': '1',
                'tmp_table_size': '64M',
                'max_heap_table_size': '64M',
                'thread_cache_size': '8',
                'table_open_cache': '400',
                'key_buffer_size': '32M',
                'join_buffer_size': '8M',
                'sort_buffer_size': '4M',
                'read_rnd_buffer_size': '4M'
            }
            
            for key, value in optimizations.items():
                if re.search(fr'^[#\s]*{key}\s*=', content, re.MULTILINE):
                    content = re.sub(fr'^[#\s]*{key}\s*=.*', f'{key} = {value}', content, flags=re.MULTILINE)
                else:
                    content = re.sub(r'\[mysqld\]', f'[mysqld]\n{key} = {value}', content)
            
            with open(config_file, 'w') as f:
                f.write(content)
            
            execute_command("systemctl restart mariadb || systemctl restart mysql || service mariadb restart || service mysql restart")
        
        print("MariaDB instalado e configurado com sucesso!")
        mariadb_installed = True
        time.sleep(2)
        os.system('clear')
    
    if apache_installed and mariadb_installed and ask("🌐 Deseja instalar o PHP e phpMyAdmin?"):
        print("Instalando PHP e dependências...")
        
        if pkg_manager in ['apt-get', 'apt']:
            execute_command(f"{pkg_install} php libapache2-mod-php php-mysql php-json php-pear php-mbstring")
        elif pkg_manager in ['dnf', 'yum']:
            execute_command(f"{pkg_install} php php-mysqlnd php-json php-pear php-mbstring")
        elif pkg_manager == 'pacman':
            execute_command(f"{pkg_install} php php-apache php-mysql")
        else:
            execute_command(f"{pkg_install} php php-mysql php-json php-pear php-mbstring")
        
        print("Instalando phpMyAdmin...")
        
        if pkg_manager in ['apt-get', 'apt']:
            # Configuração para instalação não interativa
            execute_command(f"echo 'phpmyadmin phpmyadmin/dbconfig-install boolean true' | debconf-set-selections")
            execute_command(f"echo 'phpmyadmin phpmyadmin/app-password-confirm password {mariadb_root_password}' | debconf-set-selections")
            execute_command(f"echo 'phpmyadmin phpmyadmin/mysql/admin-pass password {mariadb_root_password}' | debconf-set-selections")
            execute_command(f"echo 'phpmyadmin phpmyadmin/mysql/app-pass password {mariadb_root_password}' | debconf-set-selections")
            execute_command(f"echo 'phpmyadmin phpmyadmin/reconfigure-webserver multiselect apache2' | debconf-set-selections")
            execute_command(f"{pkg_install} phpmyadmin")
        else:
            # Para outras distribuições, a instalação pode variar. Tentaremos o método mais comum.
            if pkg_manager in ['dnf', 'yum']:
                execute_command(f"{pkg_install} phpMyAdmin")
            elif pkg_manager == 'pacman':
                execute_command(f"{pkg_install} phpmyadmin")
            else:
                print("A instalação automatizada do phpMyAdmin não está disponível para esta distribuição.")
                print("Por favor, instale manualmente ou consulte a documentação da sua distribuição.")
        
        # Reiniciar Apache para aplicar as alterações
        execute_command("systemctl restart apache2 || systemctl restart httpd || service apache2 restart || service httpd restart")
        
        print("Configuração do PHP e phpMyAdmin concluída! 🌐")
        print("Você pode acessar o phpMyAdmin com o usuário 'root' e a senha do MariaDB que você definiu.")
        time.sleep(4)
        os.system('clear')


def configure_ssl_certificate():
    print("🔐 Instalando Certbot para gerenciar certificados SSL...")
    
    distro, _ = detect_distro()
    
    # Instalar Certbot baseado na distribuição
    if distro in ['ubuntu', 'debian', 'linuxmint', 'pop', 'elementary', 'zorin']:
        execute_command("apt-get install -y certbot python3-certbot-apache")
    elif distro in ['fedora', 'centos', 'rhel', 'rocky', 'almalinux']:
        execute_command("dnf install -y certbot python3-certbot-apache || yum install -y certbot python3-certbot-apache")
    elif distro in ['arch', 'manjaro', 'endeavouros']:
        execute_command("pacman -S --noconfirm certbot certbot-apache")
    else:
        execute_command("apt-get install -y certbot python3-certbot-apache || dnf install -y certbot python3-certbot-apache || yum install -y certbot python3-certbot-apache || pacman -S --noconfirm certbot")
    
    email = input("Por favor, digite seu email para notificações de segurança e renovação do certificado: ")
    domain = input("Por favor, digite seu domínio (exemplo: seudominio.com), IP numérico não é permitido: ")
    
    if not domain or domain.replace('.', '').isdigit():
        print("Domínio inválido. A configuração SSL foi cancelada.")
        return
    
    print(f"Configurando Certbot para {domain}...")
    execute_command(f"certbot --apache -d {domain} --email {email} --agree-tos --non-interactive --redirect")
    
    # Configurar renovação automática
    cron_job = "0 3 * * * root certbot renew --quiet --deploy-hook \"systemctl reload apache2 || systemctl reload httpd || service apache2 reload || service httpd reload\""
    
    with open('/etc/cron.d/certbot', 'w') as f:
        f.write(f"SHELL=/bin/sh\n")
        f.write(f"PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin\n")
        f.write(f"{cron_job}\n")
    
    print("Certificado SSL instalado e configurado com sucesso! 🔐")
    time.sleep(2)
    os.system('clear')


def install_varnish():
    print("⚡ Instalando Varnish para caching...")
    
    distro, _ = detect_distro()
    
    if distro in ['ubuntu', 'debian', 'linuxmint', 'pop', 'elementary', 'zorin']:
        execute_command("apt-get install -y varnish")
    elif distro in ['fedora', 'centos', 'rhel', 'rocky', 'almalinux']:
        execute_command("dnf install -y varnish || yum install -y varnish")
    elif distro in ['arch', 'manjaro', 'endeavouros']:
        execute_command("pacman -S --noconfirm varnish")
    else:
        execute_command("apt-get install -y varnish || dnf install -y varnish || yum install -y varnish || pacman -S --noconfirm varnish")
    
    # Configurar Varnish
    with open('/etc/varnish/default.vcl', 'w') as f:
        f.write("""vcl 4.0;
backend default {
    .host = "127.0.0.1";
    .port = "8080";
}
""")
    
    # Atualizar configuração de portas
    varnish_config_file = None
    for path in ['/etc/default/varnish', '/etc/varnish/varnish.params']:
        if os.path.exists(path):
            varnish_config_file = path
            break
    
    if varnish_config_file:
        with open(varnish_config_file, 'r') as f:
            content = f.read()
        
        if 'DAEMON_OPTS' in content:
            content = re.sub(r'DAEMON_OPTS=.*', 'DAEMON_OPTS="-a :80 -T localhost:6082 -f /etc/varnish/default.vcl -S /etc/varnish/secret -s malloc,256m"', content)
        else:
            content += '\nDAEMON_OPTS="-a :80 -T localhost:6082 -f /etc/varnish/default.vcl -S /etc/varnish/secret -s malloc,256m"\n'
        
        with open(varnish_config_file, 'w') as f:
            f.write(content)
    
    # Atualizar portas do Apache
    apache_configs = []
    for path in ['/etc/apache2/ports.conf', '/etc/httpd/conf/httpd.conf']:
        if os.path.exists(path):
            apache_configs.append(path)
    
    for config in apache_configs:
        with open(config, 'r') as f:
            content = f.read()
        
        content = re.sub(r'Listen\s+80', 'Listen 8080', content)
        
        with open(config, 'w') as f:
            f.write(content)
    
    # Atualizar virtualhosts
    for vhost_dir in ['/etc/apache2/sites-available', '/etc/httpd/conf.d']:
        if os.path.exists(vhost_dir):
            for file in os.listdir(vhost_dir):
                if file.endswith('.conf'):
                    vhost_path = os.path.join(vhost_dir, file)
                    with open(vhost_path, 'r') as f:
                        content = f.read()
                    
                    content = re.sub(r'<VirtualHost\s+\*:80>', '<VirtualHost *:8080>', content)
                    
                    with open(vhost_path, 'w') as f:
                        f.write(content)
    
    # Reiniciar serviços
    execute_command("systemctl restart apache2 || systemctl restart httpd || service apache2 restart || service httpd restart")
    execute_command("systemctl restart varnish || service varnish restart")
    
    # Configurar firewall
    execute_command("ufw allow 6082/tcp || firewall-cmd --permanent --add-port=6082/tcp || iptables -A INPUT -p tcp --dport 6082 -j ACCEPT")
    execute_command("ufw allow 80/tcp || firewall-cmd --permanent --add-port=80/tcp || iptables -A INPUT -p tcp --dport 80 -j ACCEPT")
    execute_command("ufw reload || firewall-cmd --reload")
    
    print("Varnish instalado e configurado com sucesso! ⚡")
    time.sleep(2)
    os.system('clear')


def install_drivers():
    print("🔧 Detectando e instalando drivers atualizados...")
    
    distro, _ = detect_distro()
    
    if distro in ['ubuntu', 'debian', 'linuxmint', 'pop', 'elementary', 'zorin']:
        # Configurar repositórios para incluir componentes não-livres
        sources_file = '/etc/apt/sources.list'
        if os.path.exists(sources_file):
            with open(sources_file, 'r') as f:
                content = f.read()
            
            if 'non-free' not in content:
                content = re.sub(r'main(\s+contrib)?', r'main contrib non-free', content)
                with open(sources_file, 'w') as f:
                    f.write(content)
            
            execute_command("apt-get update")
        
        # Instalar ferramentas de detecção
        execute_command("apt-get install -y pciutils usbutils")
        
        # Instalar drivers comuns
        execute_command("apt-get install -y firmware-linux-free firmware-linux-nonfree")
        execute_command("apt-get install -y firmware-misc-nonfree")
        execute_command("apt-get install -y firmware-realtek")
        execute_command("apt-get install -y firmware-iwlwifi")
        execute_command("apt-get install -y intel-microcode")
    
    elif distro in ['fedora', 'centos', 'rhel', 'rocky', 'almalinux']:
        # Fedora já inclui repositórios não-livres por padrão
        execute_command("dnf install -y pciutils usbutils")
        execute_command("dnf install -y kernel-firmware")
        execute_command("dnf install -y iwl*-firmware")
        execute_command("dnf install -y microcode_ctl")
    
    elif distro in ['arch', 'manjaro', 'endeavouros']:
        execute_command("pacman -S --noconfirm pciutils usbutils")
        execute_command("pacman -S --noconfirm linux-firmware")
        execute_command("pacman -S --noconfirm intel-ucode amd-ucode")
    
    else:
        # Método genérico
        execute_command("apt-get install -y pciutils usbutils || dnf install -y pciutils usbutils || yum install -y pciutils usbutils || pacman -S --noconfirm pciutils usbutils")
        execute_command("apt-get install -y firmware-linux || dnf install -y kernel-firmware || yum install -y kernel-firmware || pacman -S --noconfirm linux-firmware")
    
    print("Drivers atualizados instalados com sucesso! 🔧")
    time.sleep(2)
    os.system('clear')


def disable_services():
    print("🔌 Desativando serviços não necessários para liberar recursos...")
    
    services_to_disable = ['cups-browsed', 'avahi-daemon', 'bluetooth']
    
    for service in services_to_disable:
        execute_command(f"systemctl disable {service}")
        execute_command(f"systemctl stop {service}")
        execute_command(f"systemctl mask {service}")
    
    print("Serviços não necessários desativados com sucesso! 🔌")
    time.sleep(2)
    os.system('clear')


def setup_performance_tuning():
    print("🛠️ Configurando tuned para otimização de desempenho...")
    
    distro, _ = detect_distro()
    
    if distro in ['fedora', 'centos', 'rhel', 'rocky', 'almalinux']:
        execute_command("dnf install -y tuned || yum install -y tuned")
    elif distro in ['ubuntu', 'debian', 'linuxmint', 'pop', 'elementary', 'zorin']:
        execute_command("apt-get install -y tuned")
    else:
        execute_command("apt-get install -y tuned || dnf install -y tuned || yum install -y tuned || pacman -S --noconfirm tuned")
    
    execute_command("systemctl start tuned")
    execute_command("systemctl enable tuned")
    execute_command("tuned-adm profile throughput-performance")
    
    print("Tuning automático configurado com sucesso! 🛠️")
    time.sleep(2)
    os.system('clear')

def configure_swap():
    swap_exists = get_command_output("swapon --show")
    if not swap_exists:
        swap_size = input("Digite o tamanho da memória swap (por exemplo, 4G para 4 Gigabytes): ").upper()
        if not swap_size:
            swap_size = "4G"
        
        print(f"Criando memória swap de {swap_size}...")
        
        size_match = re.match(r'(\d+)([GMK])', swap_size)
        if not size_match:
            print("Formato de tamanho inválido. Usando 4G como padrão.")
            swap_size = "4G"
        
        execute_command(f"fallocate -l {swap_size} /swapfile")
        execute_command("chmod 600 /swapfile")
        execute_command("mkswap /swapfile")
        execute_command("swapon /swapfile")
        
        fstab_entry = "/swapfile none swap sw 0 0"
        with open('/etc/fstab', 'r') as f:
            fstab_content = f.read()
        
        if '/swapfile' in fstab_content:
            fstab_content = re.sub(r'.*swapfile.*', fstab_entry, fstab_content)
            with open('/etc/fstab', 'w') as f:
                f.write(fstab_content)
        else:
            with open('/etc/fstab', 'a') as f:
                f.write(f'\n{fstab_entry}\n')

def main():
    check_root()
    
    distro, version = detect_distro()
    pkg_manager, pkg_update, pkg_install = setup_package_manager(distro)
    
    show_banner(distro, version)
    
    execute_command(pkg_update)
    install_deps(pkg_install, ['wget', 'curl', 'ca-certificates'])
    
    ssh_port = detect_ssh_port()
    
    if ask("🔑 Deseja alterar a senha do root?"):
        change_root_password()
        os.system('clear')
    
    ssh_port_changed = False
    if ask("🔧 Deseja alterar configurações do SSH?"):
        ssh_port_changed = change_ssh_settings()
        os.system('clear')
    
    if ask("💾 Deseja criar uma memória swap?"):
        configure_swap()
        os.system('clear')
    
    if ask("🌐 Deseja otimizar o adaptador de rede para melhorar o desempenho?"):
        optimize_network()
        os.system('clear')
    
    if ask("🏗️ Deseja ativar a arquitetura 32 bits (para compatibilidade com aplicativos mais antigos)?"):
        if distro in ['ubuntu', 'debian', 'linuxmint', 'pop', 'elementary', 'zorin']:
            execute_command("dpkg --add-architecture i386")
            execute_command("apt-get update")
            execute_command("apt-get install -y libc6:i386 libncurses5:i386 libstdc++6:i386")
        elif distro in ['fedora', 'centos', 'rhel', 'rocky', 'almalinux']:
            execute_command("dnf install -y glibc.i686 ncurses-libs.i686 libstdc++.i686")
        elif distro in ['arch', 'manjaro', 'endeavouros']:
            execute_command("pacman -S --noconfirm lib32-glibc lib32-ncurses lib32-gcc-libs")
        else:
            execute_command("dpkg --add-architecture i386 || echo 'Não foi possível adicionar arquitetura i386'")
            execute_command("apt-get update || echo 'Não foi possível atualizar os repositórios'")
            execute_command("apt-get install -y libc6:i386 libncurses5:i386 libstdc++6:i386 || echo 'Não foi possível instalar bibliotecas de compatibilidade'")
        
        print("Arquitetura 32 bits configurada com sucesso! 🏗️")
        time.sleep(2)
        os.system('clear')
    
    if ask("🛠️ Deseja configurar tuned para otimização de desempenho?"):
        setup_performance_tuning()
    
    if ask("🌐 Deseja instalar o stack LAMP (Apache, MariaDB, PHP)?"):
        install_lamp_stack(pkg_manager, pkg_install)
    
    if ask("🔐 Deseja instalar um certificado SSL gratuito com renovação automática?"):
        configure_ssl_certificate()
    
    if ask("⚡ Deseja instalar e configurar caching com Varnish?"):
        install_varnish()
    
    if ask("🔧 Deseja detectar e instalar todos os drivers atualizados?"):
        install_drivers()
    
    if ask("🔌 Deseja desativar serviços não necessários para liberar recursos?"):
        disable_services()
    
    if ask("🛡️ Deseja configurar o fail2ban para proteção adicional?"):
        configure_fail2ban(distro, ssh_port)
    
    if ask("🔧 Deseja configurar parâmetros sysctl para proteção adicional?"):
        configure_sysctl_protection()
    
    if ask("🔥 Deseja configurar o firewall para proteger todas as portas de jogos e serviços populares?"):
        configure_firewall(distro, ssh_port)
    
    if ask("🔧 Deseja configurar um serviço para detectar e liberar automaticamente a porta SSH no firewall após reinicializações?"):
        create_ssh_port_service(distro)
    
    if ask("🌍 Deseja alterar o idioma do sistema?"):
        change_locale()
    
    print("\n✅ Configuração concluída com sucesso! ✅\n")
    
    if ssh_port_changed:
        print(f"⚠️ ATENÇÃO: A porta SSH foi alterada. Não se esqueça de usar a nova porta ao se conectar.")
    
    if ask("🔄 Deseja reiniciar o servidor agora para aplicar todas as alterações?"):
        print("Reiniciando o servidor...")
        time.sleep(3)
        execute_command("reboot")
    else:
        print("As alterações serão aplicadas na próxima reinicialização.")
        print("Algumas configurações podem exigir uma reinicialização para funcionar corretamente.")
    
    print("\nObrigado por usar o Assistente de Configuração Universal para Linux! 🍬")


if __name__ == "__main__":
    main()
