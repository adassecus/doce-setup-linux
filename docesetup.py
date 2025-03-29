#!/usr/bin/env python3
import os
import sys
import subprocess
import platform
import re
import time
import shutil
import getpass
import pwd
from pathlib import Path
import ipaddress
from datetime import datetime
import threading

try:
    import tqdm
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    from rich.prompt import Prompt, Confirm
    from rich.table import Table
    from rich.markdown import Markdown
    from rich import print as rprint
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

class LinuxSetup:
    def __init__(self):
        self.distro, self.version = self._detect_distro()
        self.pkg_manager, self.pkg_update, self.pkg_install = self._setup_package_manager()
        self.console = Console() if RICH_AVAILABLE else None
        self.ssh_port = self._detect_ssh_port()
        self.script_version = "1.1"
        
    def _execute_command(self, command, silent=True):
        try:
            if silent:
                with open(os.devnull, 'w') as DEVNULL:
                    return subprocess.run(command, shell=True, stdout=DEVNULL, stderr=DEVNULL).returncode
            else:
                return subprocess.run(command, shell=True).returncode
        except Exception as e:
            self._print_error(f"Erro ao executar comando: {command} - {str(e)}")
            return -1

    def _get_command_output(self, command):
        try:
            result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return result.stdout.strip()
        except Exception as e:
            self._print_error(f"Erro ao obter saída do comando: {command} - {str(e)}")
            return ""

    def _detect_distro(self):
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
            distro = self._get_command_output("lsb_release -si").lower()
            version = self._get_command_output("lsb_release -sr")
            return distro, version
        
        if os.path.exists('/etc/debian_version'):
            with open('/etc/debian_version', 'r') as f:
                version = f.read().strip()
            return 'debian', version
        
        return platform.system().lower(), platform.release()

    def _setup_package_manager(self):
        distro = self.distro
        
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

    def _detect_ssh_port(self):
        if os.path.exists('/etc/ssh/sshd_config'):
            with open('/etc/ssh/sshd_config', 'r') as f:
                for line in f:
                    if line.strip().startswith('Port '):
                        port = line.strip().split()[1]
                        return port
        return "22"

    def _check_root(self):
        if os.geteuid() != 0:
            self._print_error("Este script precisa ser executado como root.")
            self._print_error("Por favor, execute com sudo ou como usuário root.")
            sys.exit(1)

    def _install_deps(self, packages):
        if RICH_AVAILABLE:
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]Instalando dependências..."),
                BarColumn(),
                TextColumn("[bold]{task.percentage:.0f}%"),
                TimeElapsedColumn(),
            ) as progress:
                task = progress.add_task("[green]Instalando...", total=len(packages))
                
                for pkg in packages:
                    if not shutil.which(pkg):
                        self._execute_command(f"{self.pkg_install} {pkg}")
                    progress.update(task, advance=1)
        else:
            for pkg in packages:
                if not shutil.which(pkg):
                    print(f"Instalando {pkg}...")
                    self._execute_command(f"{self.pkg_install} {pkg}")

    def _update_config(self, filename, param, value):
        if not os.path.exists(filename):
            return False
            
        with open(filename, 'r') as f:
            content = f.read()
        
        if re.search(rf'^[#\s]*{param}\s', content, re.MULTILINE):
            content = re.sub(rf'^[#\s]*{param}.*', f'{param} {value}', content, flags=re.MULTILINE)
        else:
            content += f'\n{param} {value}'
        
        with open(filename, 'w') as f:
            f.write(content)
        return True

    def _print_header(self, text):
        if RICH_AVAILABLE:
            self.console.print(Panel(f"[bold cyan]{text}[/]", 
                                     expand=False, 
                                     border_style="blue", 
                                     padding=(1, 2)))
        else:
            print(f"\n==== {text} ====\n")

    def _print_success(self, text):
        if RICH_AVAILABLE:
            self.console.print(f"[bold green]✓ {text}[/]")
        else:
            print(f"✓ {text}")

    def _print_error(self, text):
        if RICH_AVAILABLE:
            self.console.print(f"[bold red]✗ {text}[/]")
        else:
            print(f"✗ {text}")

    def _print_info(self, text):
        if RICH_AVAILABLE:
            self.console.print(f"[blue]ℹ {text}[/]")
        else:
            print(f"ℹ {text}")

    def _print_warning(self, text):
        if RICH_AVAILABLE:
            self.console.print(f"[bold yellow]⚠ {text}[/]")
        else:
            print(f"⚠ {text}")

    def _ask(self, question):
        if RICH_AVAILABLE:
            return Confirm.ask(question)
        else:
            while True:
                response = input(f"{question} (s/n): ").lower()
                if response in ['s', 'sim', 'y', 'yes']:
                    return True
                elif response in ['n', 'nao', 'não', 'no']:
                    return False
                else:
                    print("Por favor, responda com s ou n.")

    def _select_option(self, question, options):
        if RICH_AVAILABLE:
            return Prompt.ask(question, choices=options)
        else:
            print(question)
            for i, option in enumerate(options, 1):
                print(f"{i}. {option}")
            
            while True:
                try:
                    choice = int(input("Escolha uma opção: "))
                    if 1 <= choice <= len(options):
                        return options[choice-1]
                    else:
                        print("Opção inválida.")
                except ValueError:
                    print("Por favor, digite um número.")

    def show_banner(self):
        os.system('clear')
        if RICH_AVAILABLE:
            self.console.print(Panel.fit(
                f"[bold yellow]🍬 Doce Setup v{self.script_version}[/]\n"
                f"[cyan]Sistema detectado: {self.distro.capitalize()} {self.version}[/]",
                padding=(1, 15),
                title="[bold blue]Bem-vindo ao Setup![/]",
                subtitle="[italic]Configuração simplificada para servidores Linux[/]",
                border_style="blue"
            ))
        else:
            print(f"\n==== 🍬 Doce Setup v{self.script_version} ====")
            print(f"Sistema detectado: {self.distro.capitalize()} {self.version}\n")

    def configure_root_ssh(self):
        self._print_header("Configuração de Acesso SSH para Root")
        
        if self._ask("🔑 Deseja permitir acesso SSH para o usuário root com senha?"):
            self._print_info("Configurando acesso SSH para root...")
            
            ssh_config = '/etc/ssh/sshd_config'
            self._update_config(ssh_config, 'PermitRootLogin', 'yes')
            self._update_config(ssh_config, 'PasswordAuthentication', 'yes')
            
            if self._ask("Deseja alterar a senha do usuário root?"):
                self._print_info("Digite a nova senha do root:")
                try:
                    password = getpass.getpass()
                    if password:
                        self._execute_command(f"echo 'root:{password}' | chpasswd")
                        
                        if self._ask("Deseja aplicar a mesma senha para todos os outros usuários?"):
                            self._print_info("Aplicando senha para outros usuários...")
                            for user in pwd.getpwall():
                                if user.pw_uid >= 1000 and user.pw_uid < 65534:
                                    self._execute_command(f"echo '{user.pw_name}:{password}' | chpasswd")
                        
                        self._print_success("Senha alterada com sucesso!")
                    else:
                        self._print_error("Senha vazia não permitida.")
                        return
                except Exception as e:
                    self._print_error(f"Erro ao alterar a senha: {str(e)}")
                    return
            
            if RICH_AVAILABLE:
                with Progress(SpinnerColumn(), TextColumn("[bold blue]Reiniciando serviço SSH...")) as progress:
                    progress.add_task("reiniciando", total=None)
                    self._execute_command("systemctl restart sshd || service sshd restart || /etc/init.d/ssh restart")
            else:
                print("Reiniciando serviço SSH...")
                self._execute_command("systemctl restart sshd || service sshd restart || /etc/init.d/ssh restart")
            
            self._print_success("Acesso SSH para root configurado com sucesso!")
            self._print_info(f"Porta SSH atual: {self.ssh_port}")
        else:
            self._print_info("Configuração de acesso SSH para root ignorada.")

    def disable_ssh_timeout(self):
        self._print_header("Desativação do Timeout do SSH")
        
        if self._ask("⏳ Deseja desativar o timeout da sessão SSH (5 horas)?"):
            self._print_info("Configurando timeout do SSH...")
            
            ssh_config = '/etc/ssh/sshd_config'
            if os.path.exists(ssh_config):
                self._update_config(ssh_config, 'ClientAliveInterval', '290')
                self._update_config(ssh_config, 'ClientAliveCountMax', '63')
                
                if RICH_AVAILABLE:
                    with Progress(SpinnerColumn(), TextColumn("[bold blue]Aplicando configurações...")) as progress:
                        progress.add_task("aplicando", total=None)
                        self._execute_command("systemctl restart sshd || service sshd restart || /etc/init.d/ssh restart")
                else:
                    print("Aplicando configurações...")
                    self._execute_command("systemctl restart sshd || service sshd restart || /etc/init.d/ssh restart")
                
                self._print_success("Timeout do SSH desativado com sucesso!")
                self._print_info("As sessões SSH agora permanecerão ativas por aproximadamente 5 horas.")
            else:
                self._print_error("Arquivo de configuração SSH não encontrado.")
        else:
            self._print_info("Configuração de timeout do SSH ignorada.")

    def create_swap(self):
        self._print_header("Configuração de Memória Swap")
        
       
        swap_exists = self._get_command_output("swapon --show")
        
        if swap_exists:
            self._print_info("Memória swap já existe no sistema.")
            swap_info = self._get_command_output("free -h | grep Swap")
            if RICH_AVAILABLE:
                self.console.print(f"[green]Info de Swap: {swap_info}[/]")
            else:
                print(f"Info de Swap: {swap_info}")
                
            
            if '/swapfile' in swap_exists or '/swap' in swap_exists:
                if self._ask("Deseja remover a swap existente e criar uma nova?"):
                   
                    swap_file = None
                    for line in swap_exists.splitlines():
                        if '/swapfile' in line:
                            swap_file = '/swapfile'
                            break
                        elif '/swap' in line:
                            swap_file = '/swap'
                            break
                    
                    if swap_file:
                        if RICH_AVAILABLE:
                            with Progress(
                                SpinnerColumn(),
                                TextColumn("[bold blue]Removendo swap existente..."),
                                BarColumn(),
                                TextColumn("[bold]{task.description}"),
                            ) as progress:
                                task = progress.add_task("[green]Desativando swap...", total=None)
                                self._execute_command(f"swapoff {swap_file}")
                                
                                progress.update(task, description="Removendo entradas do fstab...")
                                if os.path.exists('/etc/fstab'):
                                    with open('/etc/fstab', 'r') as f:
                                        fstab_content = f.read()
                                    
                                    fstab_content = re.sub(r'.*swapfile.*\n?', '', fstab_content)
                                    fstab_content = re.sub(r'.*swap.*\n?', '', fstab_content)
                                    
                                    with open('/etc/fstab', 'w') as f:
                                        f.write(fstab_content)
                                
                                progress.update(task, description="Removendo arquivo swap...")
                                self._execute_command(f"rm -f {swap_file}")
                        else:
                            print("Desativando swap...")
                            self._execute_command(f"swapoff {swap_file}")
                            
                            print("Removendo entradas do fstab...")
                            if os.path.exists('/etc/fstab'):
                                with open('/etc/fstab', 'r') as f:
                                    fstab_content = f.read()
                                
                                fstab_content = re.sub(r'.*swapfile.*\n?', '', fstab_content)
                                fstab_content = re.sub(r'.*swap.*\n?', '', fstab_content)
                                
                                with open('/etc/fstab', 'w') as f:
                                    f.write(fstab_content)
                            
                            print("Removendo arquivo swap...")
                            self._execute_command(f"rm -f {swap_file}")
                        
                        self._print_success("Swap removida com sucesso!")
                    else:
                        self._print_error("Não foi possível identificar o arquivo swap.")
                        return
                else:
                    return
            else:
                self._print_warning("A swap existente parece estar em uma partição dedicada e não pode ser facilmente removida.")
                if not self._ask("Deseja continuar e adicionar mais swap?"):
                    return
        
        
        if self._ask("💾 Deseja criar uma memória swap?"):
            sizes = ["2G", "4G", "8G", "16G", "32G"]
            swap_size = self._select_option("Selecione o tamanho da memória swap:", sizes)
            
            self._print_info(f"Criando memória swap de {swap_size}...")
            
            if RICH_AVAILABLE:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[bold blue]Configurando swap..."),
                    BarColumn(),
                    TextColumn("[bold]{task.description}"),
                ) as progress:
                    task1 = progress.add_task("[green]Alocando arquivo swap...", total=None)
                    self._execute_command(f"fallocate -l {swap_size} /swapfile")
                    progress.update(task1, description="Definindo permissões...")
                    self._execute_command("chmod 600 /swapfile")
                    progress.update(task1, description="Formatando swap...")
                    self._execute_command("mkswap /swapfile")
                    progress.update(task1, description="Ativando swap...")
                    self._execute_command("swapon /swapfile")
                    progress.update(task1, description="Configurando inicialização automática...")
                    
                    fstab_entry = "/swapfile none swap sw 0 0"
                    if os.path.exists('/etc/fstab'):
                        with open('/etc/fstab', 'r') as f:
                            fstab_content = f.read()
                        
                        if '/swapfile' in fstab_content:
                            fstab_content = re.sub(r'.*swapfile.*', fstab_entry, fstab_content)
                            with open('/etc/fstab', 'w') as f:
                                f.write(fstab_content)
                        else:
                            with open('/etc/fstab', 'a') as f:
                                f.write(f'\n{fstab_entry}\n')
            else:
                print("Alocando arquivo swap...")
                self._execute_command(f"fallocate -l {swap_size} /swapfile")
                print("Definindo permissões...")
                self._execute_command("chmod 600 /swapfile")
                print("Formatando swap...")
                self._execute_command("mkswap /swapfile")
                print("Ativando swap...")
                self._execute_command("swapon /swapfile")
                print("Configurando inicialização automática...")
                
                fstab_entry = "/swapfile none swap sw 0 0"
                if os.path.exists('/etc/fstab'):
                    with open('/etc/fstab', 'r') as f:
                        fstab_content = f.read()
                    
                    if '/swapfile' in fstab_content:
                        fstab_content = re.sub(r'.*swapfile.*', fstab_entry, fstab_content)
                        with open('/etc/fstab', 'w') as f:
                            f.write(fstab_content)
                    else:
                        with open('/etc/fstab', 'a') as f:
                            f.write(f'\n{fstab_entry}\n')
            
            self._print_success(f"Memória swap de {swap_size} criada e configurada com sucesso!")
            
           
            new_swap_info = self._get_command_output("free -h | grep Swap")
            if RICH_AVAILABLE:
                self.console.print(f"[green]Nova Info de Swap: {new_swap_info}[/]")
            else:
                print(f"Nova Info de Swap: {new_swap_info}")
        else:
            self._print_info("Configuração de memória swap ignorada.")

    def enable_32bit_arch(self):
        self._print_header("Ativação da Arquitetura 32 bits")
        
        if self._ask("🏗️ Deseja ativar a arquitetura 32 bits (para compatibilidade com aplicativos mais antigos)?"):
            self._print_info("Ativando arquitetura 32 bits...")
            
            if RICH_AVAILABLE:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[bold blue]Configurando arquitetura 32 bits..."),
                    BarColumn(),
                    TextColumn("[bold]{task.description}"),
                ) as progress:
                    task = progress.add_task("[green]Processando...", total=None)
                    
                    if self.distro in ['ubuntu', 'debian', 'linuxmint', 'pop', 'elementary', 'zorin']:
                        progress.update(task, description="Adicionando arquitetura i386...")
                        self._execute_command("dpkg --add-architecture i386")
                        progress.update(task, description="Atualizando repositórios...")
                        self._execute_command("apt-get update")
                        progress.update(task, description="Instalando bibliotecas...")
                        self._execute_command("apt-get install -y libc6:i386 libncurses5:i386 libstdc++6:i386")
                    elif self.distro in ['fedora', 'centos', 'rhel', 'rocky', 'almalinux']:
                        progress.update(task, description="Instalando suporte 32 bits...")
                        self._execute_command("dnf install -y glibc.i686 ncurses-libs.i686 libstdc++.i686")
                    elif self.distro in ['arch', 'manjaro', 'endeavouros']:
                        progress.update(task, description="Instalando suporte 32 bits...")
                        self._execute_command("pacman -S --noconfirm lib32-glibc lib32-ncurses lib32-gcc-libs")
                    else:
                        progress.update(task, description="Tentando método genérico...")
                        self._execute_command("dpkg --add-architecture i386 || echo 'Não foi possível adicionar arquitetura i386'")
                        self._execute_command("apt-get update || echo 'Não foi possível atualizar os repositórios'")
                        self._execute_command("apt-get install -y libc6:i386 libncurses5:i386 libstdc++6:i386 || echo 'Não foi possível instalar bibliotecas de compatibilidade'")
            else:
                if self.distro in ['ubuntu', 'debian', 'linuxmint', 'pop', 'elementary', 'zorin']:
                    print("Adicionando arquitetura i386...")
                    self._execute_command("dpkg --add-architecture i386")
                    print("Atualizando repositórios...")
                    self._execute_command("apt-get update")
                    print("Instalando bibliotecas...")
                    self._execute_command("apt-get install -y libc6:i386 libncurses5:i386 libstdc++6:i386")
                elif self.distro in ['fedora', 'centos', 'rhel', 'rocky', 'almalinux']:
                    print("Instalando suporte 32 bits...")
                    self._execute_command("dnf install -y glibc.i686 ncurses-libs.i686 libstdc++.i686")
                elif self.distro in ['arch', 'manjaro', 'endeavouros']:
                    print("Instalando suporte 32 bits...")
                    self._execute_command("pacman -S --noconfirm lib32-glibc lib32-ncurses lib32-gcc-libs")
                else:
                    print("Tentando método genérico...")
                    self._execute_command("dpkg --add-architecture i386 || echo 'Não foi possível adicionar arquitetura i386'")
                    self._execute_command("apt-get update || echo 'Não foi possível atualizar os repositórios'")
                    self._execute_command("apt-get install -y libc6:i386 libncurses5:i386 libstdc++6:i386 || echo 'Não foi possível instalar bibliotecas de compatibilidade'")
            
            self._print_success("Arquitetura 32 bits ativada com sucesso!")
            self._print_info("Agora você poderá executar aplicativos 32 bits em seu sistema.")
        else:
            self._print_info("Ativação da arquitetura 32 bits ignorada.")

    def _detect_web_server(self):
        
        apache_installed = (self._execute_command("which apache2") == 0) or (self._execute_command("which httpd") == 0)
        apache_running = (self._execute_command("systemctl is-active --quiet apache2") == 0) or (self._execute_command("systemctl is-active --quiet httpd") == 0)
        
        
        nginx_installed = self._execute_command("which nginx") == 0
        nginx_running = self._execute_command("systemctl is-active --quiet nginx") == 0
        
        if apache_running:
            return "apache"
        elif nginx_running:
            return "nginx"
        elif apache_installed:
            return "apache"
        elif nginx_installed:
            return "nginx"
        else:
            return None

    def _configure_nginx_site(self, domain, ssl_cert, ssl_key):
        nginx_conf = f"""server {{
    listen 80;
    listen [::]:80;
    server_name {domain};
    return 301 https://$host$request_uri;
}}

server {{
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name {domain};

    ssl_certificate {ssl_cert};
    ssl_certificate_key {ssl_key};
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    root /var/www/html;
    index index.html index.htm index.nginx-debian.html;

    location / {{
        try_files $uri $uri/ =404;
    }}
}}
"""
        
        
        self._execute_command("mkdir -p /etc/nginx/sites-available")
        self._execute_command("mkdir -p /etc/nginx/sites-enabled")
        
        
        with open(f"/etc/nginx/sites-available/{domain}", "w") as f:
            f.write(nginx_conf)
        
        
        if not os.path.exists(f"/etc/nginx/sites-enabled/{domain}"):
            self._execute_command(f"ln -s /etc/nginx/sites-available/{domain} /etc/nginx/sites-enabled/")
        
        
        if os.path.exists("/etc/nginx/sites-enabled/default"):
            self._execute_command("rm -f /etc/nginx/sites-enabled/default")
        
        
        self._execute_command("mkdir -p /var/www/html")
        
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Bem-vindo a {domain}</title>
    <style>
        body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
        h1 {{ color: #3366cc; }}
        .container {{ max-width: 800px; margin: 0 auto; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Bem-vindo a {domain}!</h1>
        <p>Este site está protegido com SSL pelo Certbot.</p>
        <p>Seu certificado foi instalado com sucesso!</p>
        <p><small>Configurado com Doce Setup</small></p>
    </div>
</body>
</html>
"""
        
        with open("/var/www/html/index.html", "w") as f:
            f.write(html_content)
        
        
        if self._execute_command("nginx -t") == 0:
            self._execute_command("systemctl restart nginx")
            return True
        else:
            self._print_error("Erro na configuração do Nginx. Verifique a sintaxe.")
            return False

    def _configure_apache_site(self, domain, ssl_cert, ssl_key):
        apache_conf = f"""<VirtualHost *:80>
    ServerName {domain}
    Redirect permanent / https://{domain}/
</VirtualHost>

<VirtualHost *:443>
    ServerName {domain}
    
    DocumentRoot /var/www/html
    
    SSLEngine on
    SSLCertificateFile {ssl_cert}
    SSLCertificateKeyFile {ssl_key}
    
    <Directory /var/www/html>
        Options -Indexes +FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>
    
    ErrorLog ${{APACHE_LOG_DIR}}/error.log
    CustomLog ${{APACHE_LOG_DIR}}/access.log combined
</VirtualHost>
"""
        
        
        apache_conf_dir = "/etc/apache2" if os.path.exists("/etc/apache2") else "/etc/httpd"
        sites_available = f"{apache_conf_dir}/sites-available"
        sites_enabled = f"{apache_conf_dir}/sites-enabled"
        
        
        self._execute_command(f"mkdir -p {sites_available}")
        self._execute_command(f"mkdir -p {sites_enabled}")
        
        
        with open(f"{sites_available}/{domain}.conf", "w") as f:
            f.write(apache_conf)
        
       
        if os.path.exists(f"{sites_available}/{domain}.conf") and not os.path.exists(f"{sites_enabled}/{domain}.conf"):
            if os.path.exists("/usr/sbin/a2ensite"):
                self._execute_command(f"a2ensite {domain}")
            else:
                self._execute_command(f"ln -s {sites_available}/{domain}.conf {sites_enabled}/")
        
       
        if os.path.exists("/usr/sbin/a2enmod"):
            self._execute_command("a2enmod ssl")
            self._execute_command("a2enmod rewrite")
        
       
        self._execute_command("mkdir -p /var/www/html")
        
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Bem-vindo a {domain}</title>
    <style>
        body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
        h1 {{ color: #3366cc; }}
        .container {{ max-width: 800px; margin: 0 auto; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Bem-vindo a {domain}!</h1>
        <p>Este site está protegido com SSL pelo Certbot.</p>
        <p>Seu certificado foi instalado com sucesso!</p>
        <p><small>Configurado com Doce Setup</small></p>
    </div>
</body>
</html>
"""
        
        with open("/var/www/html/index.html", "w") as f:
            f.write(html_content)
        
        
        if self.distro in ['ubuntu', 'debian']:
            self._execute_command("systemctl restart apache2")
        else:
            self._execute_command("systemctl restart httpd")
            
        return True

    def configure_ssl_certificate(self):
        self._print_header("Configuração de Certificado SSL")
        
        if self._ask("🔐 Deseja configurar um certificado SSL gratuito?"):
            
            web_server = self._detect_web_server()
            
            if not web_server:
                self._print_info("Nenhum servidor web detectado. É necessário um servidor web para configurar SSL.")
                server_options = ["apache", "nginx", "nenhum"]
                selected_server = self._select_option("Qual servidor web você deseja instalar?", server_options)
                
                if selected_server == "nenhum":
                    self._print_info("Configuração SSL cancelada. É necessário um servidor web para continuar.")
                    return
                
                
                self._print_info(f"Instalando servidor web {selected_server}...")
                if RICH_AVAILABLE:
                    with Progress(SpinnerColumn(), TextColumn(f"[bold blue]Instalando {selected_server}...")) as progress:
                        task = progress.add_task("instalando", total=None)
                        
                        if selected_server == "apache":
                            if self.distro in ['ubuntu', 'debian', 'linuxmint', 'pop', 'elementary', 'zorin']:
                                self._execute_command("apt-get install -y apache2")
                            elif self.distro in ['fedora', 'centos', 'rhel', 'rocky', 'almalinux']:
                                self._execute_command("dnf install -y httpd mod_ssl")
                            elif self.distro in ['arch', 'manjaro', 'endeavouros']:
                                self._execute_command("pacman -S --noconfirm apache")
                            else:
                                self._execute_command("apt-get install -y apache2 || dnf install -y httpd || pacman -S --noconfirm apache")
                        else:  
                            if self.distro in ['ubuntu', 'debian', 'linuxmint', 'pop', 'elementary', 'zorin']:
                                self._execute_command("apt-get install -y nginx")
                            elif self.distro in ['fedora', 'centos', 'rhel', 'rocky', 'almalinux']:
                                self._execute_command("dnf install -y nginx")
                            elif self.distro in ['arch', 'manjaro', 'endeavouros']:
                                self._execute_command("pacman -S --noconfirm nginx")
                            else:
                                self._execute_command("apt-get install -y nginx || dnf install -y nginx || pacman -S --noconfirm nginx")
                else:
                    print(f"Instalando servidor web {selected_server}...")
                    if selected_server == "apache":
                        if self.distro in ['ubuntu', 'debian', 'linuxmint', 'pop', 'elementary', 'zorin']:
                            self._execute_command("apt-get install -y apache2")
                        elif self.distro in ['fedora', 'centos', 'rhel', 'rocky', 'almalinux']:
                            self._execute_command("dnf install -y httpd mod_ssl")
                        elif self.distro in ['arch', 'manjaro', 'endeavouros']:
                            self._execute_command("pacman -S --noconfirm apache")
                        else:
                            self._execute_command("apt-get install -y apache2 || dnf install -y httpd || pacman -S --noconfirm apache")
                    else:  
                        if self.distro in ['ubuntu', 'debian', 'linuxmint', 'pop', 'elementary', 'zorin']:
                            self._execute_command("apt-get install -y nginx")
                        elif self.distro in ['fedora', 'centos', 'rhel', 'rocky', 'almalinux']:
                            self._execute_command("dnf install -y nginx")
                        elif self.distro in ['arch', 'manjaro', 'endeavouros']:
                            self._execute_command("pacman -S --noconfirm nginx")
                        else:
                            self._execute_command("apt-get install -y nginx || dnf install -y nginx || pacman -S --noconfirm nginx")
                
                
                if selected_server == "apache":
                    if self.distro in ['ubuntu', 'debian']:
                        self._execute_command("systemctl enable apache2 && systemctl start apache2")
                    else:
                        self._execute_command("systemctl enable httpd && systemctl start httpd")
                else:  
                    self._execute_command("systemctl enable nginx && systemctl start nginx")
                
                web_server = selected_server
                self._print_success(f"Servidor web {selected_server} instalado e iniciado com sucesso!")

            
            if not shutil.which('certbot'):
                self._print_info("Instalando Certbot...")
                
                if RICH_AVAILABLE:
                    with Progress(SpinnerColumn(), TextColumn("[bold blue]Instalando Certbot...")) as progress:
                        task = progress.add_task("instalando", total=None)
                        
                        if web_server == "apache":
                            if self.distro in ['ubuntu', 'debian', 'linuxmint', 'pop', 'elementary', 'zorin']:
                                self._execute_command("apt-get install -y certbot python3-certbot-apache")
                            elif self.distro in ['fedora', 'centos', 'rhel', 'rocky', 'almalinux']:
                                self._execute_command("dnf install -y certbot python3-certbot-apache")
                            else:
                                self._execute_command("apt-get install -y certbot python3-certbot-apache || dnf install -y certbot python3-certbot-apache || echo 'Não foi possível instalar o plugin Apache para o Certbot'")
                        else:  
                            if self.distro in ['ubuntu', 'debian', 'linuxmint', 'pop', 'elementary', 'zorin']:
                                self._execute_command("apt-get install -y certbot python3-certbot-nginx")
                            elif self.distro in ['fedora', 'centos', 'rhel', 'rocky', 'almalinux']:
                                self._execute_command("dnf install -y certbot python3-certbot-nginx")
                            else:
                                self._execute_command("apt-get install -y certbot python3-certbot-nginx || dnf install -y certbot python3-certbot-nginx || echo 'Não foi possível instalar o plugin Nginx para o Certbot'")
                else:
                    print("Instalando Certbot...")
                    if web_server == "apache":
                        if self.distro in ['ubuntu', 'debian', 'linuxmint', 'pop', 'elementary', 'zorin']:
                            self._execute_command("apt-get install -y certbot python3-certbot-apache")
                        elif self.distro in ['fedora', 'centos', 'rhel', 'rocky', 'almalinux']:
                            self._execute_command("dnf install -y certbot python3-certbot-apache")
                        else:
                            self._execute_command("apt-get install -y certbot python3-certbot-apache || dnf install -y certbot python3-certbot-apache || echo 'Não foi possível instalar o plugin Apache para o Certbot'")
                    else:  
                        if self.distro in ['ubuntu', 'debian', 'linuxmint', 'pop', 'elementary', 'zorin']:
                            self._execute_command("apt-get install -y certbot python3-certbot-nginx")
                        elif self.distro in ['fedora', 'centos', 'rhel', 'rocky', 'almalinux']:
                            self._execute_command("dnf install -y certbot python3-certbot-nginx")
                        else:
                            self._execute_command("apt-get install -y certbot python3-certbot-nginx || dnf install -y certbot python3-certbot-nginx || echo 'Não foi possível instalar o plugin Nginx para o Certbot'")
            
            
            self._print_info("Somente certificados baseados em domínio estão disponíveis.")
            self._print_info("Para configurar um certificado SSL, você precisará de:")
            self._print_info("1. Um domínio apontando para o IP deste servidor")
            self._print_info("2. As portas 80 e 443 abertas no firewall")
            
            
            self._print_info("Para continuar, forneça as seguintes informações:")
            
            email = input("Digite seu email para notificações de segurança e renovação: ")
            
            
            self._print_info("\nVocê deverá adicionar domínios um por vez.")
            self._print_info("Por exemplo: seudominio.com, depois www.seudominio.com, depois app.seudominio.com")
            self._print_info("Todos estes domínios devem apontar para o IP deste servidor.")
            
            domains = []
            while True:
                domain = input("\nDigite UM domínio ou subdomínio (ou deixe vazio para finalizar): ")
                if not domain:
                    break
                    
                if domain.replace('.', '').isdigit():
                    self._print_error("Domínio inválido. Por favor, use um nome de domínio válido.")
                    continue
                    
                domains.append(domain)
                self._print_info(f"Domínio '{domain}' adicionado à lista. Total: {len(domains)} domínio(s).")
                if len(domains) > 0:
                    self._print_info("Continue adicionando domínios um por vez ou deixe vazio para finalizar.")
            
            if not domains:
                self._print_error("Nenhum domínio foi especificado. A configuração SSL foi cancelada.")
                return
            
            self._print_info(f"Configurando certificado SSL para: {', '.join(domains)}...")
            
            
            if web_server == "apache":
                if self.distro in ['ubuntu', 'debian']:
                    self._execute_command("systemctl stop apache2")
                else:
                    self._execute_command("systemctl stop httpd")
            else:  
                self._execute_command("systemctl stop nginx")
            
            
            domains_str = " ".join([f"-d {d}" for d in domains])
            primary_domain = domains[0]
            
            if RICH_AVAILABLE:
                with Progress(SpinnerColumn(), TextColumn(f"[bold blue]Obtendo certificado para {len(domains)} domínio(s)...")) as progress:
                    task = progress.add_task("obtendo", total=None)
                    result = self._execute_command(f"certbot certonly --standalone {domains_str} --email {email} --agree-tos --non-interactive", silent=False)
            else:
                print(f"Obtendo certificado para {len(domains)} domínio(s)...")
                result = self._execute_command(f"certbot certonly --standalone {domains_str} --email {email} --agree-tos --non-interactive", silent=False)
            
            
            if not os.path.exists(f"/etc/letsencrypt/live/{primary_domain}/fullchain.pem"):
                self._print_error("Não foi possível obter o certificado. Verifique se os domínios apontam para este servidor.")
                
                
                if web_server == "apache":
                    if self.distro in ['ubuntu', 'debian']:
                        self._execute_command("systemctl start apache2")
                    else:
                        self._execute_command("systemctl start httpd")
                else:  
                    self._execute_command("systemctl start nginx")
                    
                return
            
            
            if web_server == "apache":
                self._configure_apache_site(primary_domain, 
                                           f"/etc/letsencrypt/live/{primary_domain}/fullchain.pem", 
                                           f"/etc/letsencrypt/live/{primary_domain}/privkey.pem")
            else:  
                self._configure_nginx_site(primary_domain, 
                                          f"/etc/letsencrypt/live/{primary_domain}/fullchain.pem", 
                                          f"/etc/letsencrypt/live/{primary_domain}/privkey.pem")
            
            
            cron_job = "0 3 * * * root certbot renew --quiet"
            with open('/etc/cron.d/certbot', 'w') as f:
                f.write(f"SHELL=/bin/sh\n")
                f.write(f"PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin\n")
                f.write(f"{cron_job}\n")
            
            self._print_success(f"Certificado SSL para {len(domains)} domínio(s) instalado e configurado com sucesso!")
            self._print_info(f"Seu site está disponível em: https://{primary_domain}")
            self._print_info(f"Certificados armazenados em: /etc/letsencrypt/live/{primary_domain}/")
            self._print_info("A renovação automática foi configurada para ocorrer diariamente às 3h da manhã.")
            
            
            if RICH_AVAILABLE:
                cert_info = Table(title="Informações do Certificado SSL")
                cert_info.add_column("Arquivo", style="cyan")
                cert_info.add_column("Caminho", style="green")
                cert_info.add_row("Certificado", f"/etc/letsencrypt/live/{primary_domain}/fullchain.pem")
                cert_info.add_row("Chave Privada", f"/etc/letsencrypt/live/{primary_domain}/privkey.pem")
                cert_info.add_row("Cadeia", f"/etc/letsencrypt/live/{primary_domain}/chain.pem")
                self.console.print(cert_info)
            else:
                print("\nInformações do Certificado SSL:")
                print(f"Certificado: /etc/letsencrypt/live/{primary_domain}/fullchain.pem")
                print(f"Chave Privada: /etc/letsencrypt/live/{primary_domain}/privkey.pem")
                print(f"Cadeia: /etc/letsencrypt/live/{primary_domain}/chain.pem")
            
            if self._ask("Deseja adicionar outro certificado para diferentes domínios?"):
                self.configure_ssl_certificate()
        else:
            self._print_info("Configuração do certificado SSL ignorada.")

    def remove_ssl_certificates(self):
        self._print_header("Remoção de Certificados SSL")
        
        
        cert_list = self._get_command_output("certbot certificates")
        
        if "No certificates found" in cert_list or not cert_list:
            self._print_info("Nenhum certificado SSL encontrado para remover.")
            return
        
        self._print_info("Certificados SSL encontrados:")
        print(cert_list)
        
       
        domains = []
        for line in cert_list.splitlines():
            if "Domains:" in line:
                domains_str = line.split("Domains:")[1].strip()
                domains.extend(domains_str.split())
        
        if not domains:
            self._print_info("Não foi possível identificar os domínios dos certificados.")
            return
        
       
        if len(domains) > 1:
            remove_all = self._ask("Deseja remover todos os certificados SSL?")
            
            if remove_all:
                if RICH_AVAILABLE:
                    with Progress(SpinnerColumn(), TextColumn("[bold blue]Removendo todos os certificados...")) as progress:
                        task = progress.add_task("removendo", total=None)
                        self._execute_command("certbot delete --non-interactive", silent=False)
                else:
                    print("Removendo todos os certificados...")
                    self._execute_command("certbot delete --non-interactive", silent=False)
                
                self._print_success("Todos os certificados SSL foram removidos com sucesso!")
            else:
                self._print_info("Escolha um domínio para remover o certificado:")
                domain = self._select_option("Selecione o domínio:", domains)
                
                if RICH_AVAILABLE:
                    with Progress(SpinnerColumn(), TextColumn(f"[bold blue]Removendo certificado para {domain}...")) as progress:
                        task = progress.add_task("removendo", total=None)
                        self._execute_command(f"certbot delete --cert-name {domain} --non-interactive", silent=False)
                else:
                    print(f"Removendo certificado para {domain}...")
                    self._execute_command(f"certbot delete --cert-name {domain} --non-interactive", silent=False)
                
                self._print_success(f"Certificado SSL para {domain} removido com sucesso!")
        else:
            domain = domains[0]
            
            if self._ask(f"Deseja remover o certificado SSL para {domain}?"):
                if RICH_AVAILABLE:
                    with Progress(SpinnerColumn(), TextColumn(f"[bold blue]Removendo certificado para {domain}...")) as progress:
                        task = progress.add_task("removendo", total=None)
                        self._execute_command(f"certbot delete --cert-name {domain} --non-interactive", silent=False)
                else:
                    print(f"Removendo certificado para {domain}...")
                    self._execute_command(f"certbot delete --cert-name {domain} --non-interactive", silent=False)
                
                self._print_success(f"Certificado SSL para {domain} removido com sucesso!")
            else:
                self._print_info("Remoção de certificado SSL cancelada.")
        
       
        if self._ask("Deseja também remover as configurações do servidor web?"):
            web_server = self._detect_web_server()
            
            if web_server == "apache":
                for domain in domains:
                    apache_conf_dir = "/etc/apache2" if os.path.exists("/etc/apache2") else "/etc/httpd"
                    sites_available = f"{apache_conf_dir}/sites-available"
                    sites_enabled = f"{apache_conf_dir}/sites-enabled"
                    
                    if os.path.exists(f"{sites_enabled}/{domain}.conf"):
                        if os.path.exists("/usr/sbin/a2dissite"):
                            self._execute_command(f"a2dissite {domain}")
                        else:
                            self._execute_command(f"rm -f {sites_enabled}/{domain}.conf")
                    
                    if os.path.exists(f"{sites_available}/{domain}.conf"):
                        self._execute_command(f"rm -f {sites_available}/{domain}.conf")
                
                
                if self.distro in ['ubuntu', 'debian']:
                    self._execute_command("systemctl restart apache2")
                else:
                    self._execute_command("systemctl restart httpd")
            
            elif web_server == "nginx":
                for domain in domains:
                    if os.path.exists(f"/etc/nginx/sites-enabled/{domain}"):
                        self._execute_command(f"rm -f /etc/nginx/sites-enabled/{domain}")
                    
                    if os.path.exists(f"/etc/nginx/sites-available/{domain}"):
                        self._execute_command(f"rm -f /etc/nginx/sites-available/{domain}")
                
                
                self._execute_command("systemctl restart nginx")
            
            self._print_success("Configurações do servidor web removidas com sucesso!")

    def disable_services(self):
        self._print_header("Desativação de Serviços Desnecessários")
        
        if self._ask("🔌 Deseja desativar serviços não necessários para liberar recursos?"):
            services_to_disable = [
                'cups-browsed',  
                'avahi-daemon', 
                'bluetooth',    
                'ModemManager', 
                'wpa_supplicant' 
            ]
            
            
            if RICH_AVAILABLE:
                services_table = Table(title="Serviços Disponíveis para Desativação")
                services_table.add_column("Serviço", style="cyan")
                services_table.add_column("Descrição", style="green")
                
                services_table.add_row("cups-browsed", "Descoberta de impressoras na rede")
                services_table.add_row("avahi-daemon", "Descoberta de serviços na rede local")
                services_table.add_row("bluetooth", "Suporte a dispositivos Bluetooth")
                services_table.add_row("ModemManager", "Gerenciamento de modems e conexões móveis")
                services_table.add_row("wpa_supplicant", "Cliente para redes Wi-Fi")
                
                self.console.print(services_table)
            else:
                print("\nServiços Disponíveis para Desativação:")
                print("cups-browsed - Descoberta de impressoras na rede")
                print("avahi-daemon - Descoberta de serviços na rede local")
                print("bluetooth - Suporte a dispositivos Bluetooth")
                print("ModemManager - Gerenciamento de modems e conexões móveis")
                print("wpa_supplicant - Cliente para redes Wi-Fi")
                print("")
            
            selected_services = []
            for service in services_to_disable:
                if self._ask(f"Deseja desativar o serviço {service}?"):
                    selected_services.append(service)
            
            if not selected_services:
                self._print_info("Nenhum serviço selecionado para desativação.")
                return
            
            self._print_info(f"Desativando {len(selected_services)} serviços selecionados...")
            
            if RICH_AVAILABLE:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[bold blue]Desativando serviços..."),
                    BarColumn(),
                    TextColumn("[bold]{task.percentage:.0f}%"),
                ) as progress:
                    task = progress.add_task("[green]Processando...", total=len(selected_services)*3)
                    
                    for service in selected_services:
                        self._execute_command(f"systemctl disable {service}")
                        progress.update(task, advance=1)
                        self._execute_command(f"systemctl stop {service}")
                        progress.update(task, advance=1)
                        self._execute_command(f"systemctl mask {service}")
                        progress.update(task, advance=1)
            else:
                for service in selected_services:
                    print(f"Desativando {service}...")
                    self._execute_command(f"systemctl disable {service}")
                    self._execute_command(f"systemctl stop {service}")
                    self._execute_command(f"systemctl mask {service}")
        
            self._print_success(f"{len(selected_services)} serviços desativados com sucesso!")
            self._print_info("Os serviços não iniciarão mais na inicialização do sistema.")
        else:
            self._print_info("Desativação de serviços ignorada.")

    def translate_to_portuguese(self):
        self._print_header("Tradução Completa para Português do Brasil")
        
        if self._ask("🌎 Deseja traduzir completamente o sistema para Português do Brasil?"):
            self._print_info("Configurando localização para pt_BR.UTF-8...")
            
            if RICH_AVAILABLE:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[bold blue]Configurando localização..."),
                    BarColumn(),
                    TextColumn("[bold]{task.description}"),
                ) as progress:
                    task = progress.add_task("[green]Instalando pacotes de idioma...", total=None)
                    
                    
                    if self.distro in ['ubuntu', 'debian', 'linuxmint', 'pop', 'elementary', 'zorin']:
                        self._execute_command("apt-get install -y locales language-pack-pt language-pack-pt-base language-pack-gnome-pt")
                    elif self.distro in ['fedora', 'centos', 'rhel', 'rocky', 'almalinux']:
                        self._execute_command("dnf install -y glibc-langpack-pt langpacks-pt_BR")
                    elif self.distro in ['arch', 'manjaro', 'endeavouros']:
                        self._execute_command("pacman -S --noconfirm glibc lib32-glibc")
                    else:
                        progress.update(task, description="Tentando método genérico...")
                        self._execute_command("apt-get install -y locales language-pack-pt language-pack-pt-base || dnf install -y glibc-langpack-pt || echo 'Não foi possível instalar pacotes de idioma'")
                    
                    
                    progress.update(task, description="Gerando locales...")
                    self._execute_command("locale-gen pt_BR.UTF-8 || echo 'Não foi possível gerar locales'")
                    
                    
                    progress.update(task, description="Configurando variáveis de ambiente...")
                    
                    
                    locale_file = ""
                    if os.path.exists("/etc/locale.conf"):
                        locale_file = "/etc/locale.conf"
                    elif os.path.exists("/etc/default/locale"):
                        locale_file = "/etc/default/locale"
                    
                    if locale_file:
                        with open(locale_file, 'w') as f:
                            f.write("LANG=pt_BR.UTF-8\n")
                            f.write("LANGUAGE=pt_BR:pt:en\n")
                            f.write("LC_ALL=pt_BR.UTF-8\n")
                    else:
                       
                        with open("/etc/locale.conf", 'w') as f:
                            f.write("LANG=pt_BR.UTF-8\n")
                            f.write("LANGUAGE=pt_BR:pt:en\n")
                            f.write("LC_ALL=pt_BR.UTF-8\n")
                    
                    
                    self._execute_command("update-locale LANG=pt_BR.UTF-8 LANGUAGE=pt_BR:pt:en LC_ALL=pt_BR.UTF-8 || echo 'Não foi possível atualizar locale'")
                    
                    
                    progress.update(task, description="Configurando para todos os usuários...")
                    
                    for user in pwd.getpwall():
                        if user.pw_uid >= 1000 and user.pw_uid < 65534:
                            home = user.pw_dir
                            if os.path.exists(home):
                                
                                bashrc = os.path.join(home, ".bashrc")
                                if os.path.exists(bashrc):
                                    with open(bashrc, 'a') as f:
                                        f.write("\n# Configuração de idioma\n")
                                        f.write("export LANG=pt_BR.UTF-8\n")
                                        f.write("export LANGUAGE=pt_BR:pt:en\n")
                                        f.write("export LC_ALL=pt_BR.UTF-8\n")
                                
                                
                                zshrc = os.path.join(home, ".zshrc")
                                if os.path.exists(zshrc):
                                    with open(zshrc, 'a') as f:
                                        f.write("\n# Configuração de idioma\n")
                                        f.write("export LANG=pt_BR.UTF-8\n")
                                        f.write("export LANGUAGE=pt_BR:pt:en\n")
                                        f.write("export LC_ALL=pt_BR.UTF-8\n")
                                
                                
                                self._execute_command(f"chown -R {user.pw_name}:{user.pw_name} {home}/.bashrc {home}/.zshrc 2>/dev/null || true")
                    
                    
                    progress.update(task, description="Configurando interface gráfica...")
                    if self.distro in ['ubuntu', 'debian', 'linuxmint', 'pop', 'elementary', 'zorin']:
                        self._execute_command("apt-get install -y task-brazilian-portuguese")
                    
                    if os.path.exists("/usr/bin/localectl"):
                        self._execute_command("localectl set-locale LANG=pt_BR.UTF-8")
                        self._execute_command("localectl set-keymap br-abnt2")
                    
                   
                    if os.path.exists("/etc/X11/xorg.conf.d"):
                        if not os.path.exists("/etc/X11/xorg.conf.d/00-keyboard.conf"):
                            with open("/etc/X11/xorg.conf.d/00-keyboard.conf", 'w') as f:
                                f.write('Section "InputClass"\n')
                                f.write('    Identifier "system-keyboard"\n')
                                f.write('    MatchIsKeyboard "on"\n')
                                f.write('    Option "XkbLayout" "br"\n')
                                f.write('    Option "XkbVariant" "abnt2"\n')
                                f.write('EndSection\n')
            else:
                print("Instalando pacotes de idioma...")
                if self.distro in ['ubuntu', 'debian', 'linuxmint', 'pop', 'elementary', 'zorin']:
                    self._execute_command("apt-get install -y locales language-pack-pt language-pack-pt-base language-pack-gnome-pt")
                elif self.distro in ['fedora', 'centos', 'rhel', 'rocky', 'almalinux']:
                    self._execute_command("dnf install -y glibc-langpack-pt langpacks-pt_BR")
                elif self.distro in ['arch', 'manjaro', 'endeavouros']:
                    self._execute_command("pacman -S --noconfirm glibc lib32-glibc")
                else:
                    print("Tentando método genérico...")
                    self._execute_command("apt-get install -y locales language-pack-pt language-pack-pt-base || dnf install -y glibc-langpack-pt || echo 'Não foi possível instalar pacotes de idioma'")
                
                print("Gerando locales...")
                self._execute_command("locale-gen pt_BR.UTF-8 || echo 'Não foi possível gerar locales'")
                
                print("Configurando variáveis de ambiente...")
                
              
                locale_file = ""
                if os.path.exists("/etc/locale.conf"):
                    locale_file = "/etc/locale.conf"
                elif os.path.exists("/etc/default/locale"):
                    locale_file = "/etc/default/locale"
                
                if locale_file:
                    with open(locale_file, 'w') as f:
                        f.write("LANG=pt_BR.UTF-8\n")
                        f.write("LANGUAGE=pt_BR:pt:en\n")
                        f.write("LC_ALL=pt_BR.UTF-8\n")
                else:
                    
                    with open("/etc/locale.conf", 'w') as f:
                        f.write("LANG=pt_BR.UTF-8\n")
                        f.write("LANGUAGE=pt_BR:pt:en\n")
                        f.write("LC_ALL=pt_BR.UTF-8\n")
                
                
                self._execute_command("update-locale LANG=pt_BR.UTF-8 LANGUAGE=pt_BR:pt:en LC_ALL=pt_BR.UTF-8 || echo 'Não foi possível atualizar locale'")
                
                
                print("Configurando para todos os usuários...")
                
                for user in pwd.getpwall():
                    if user.pw_uid >= 1000 and user.pw_uid < 65534:
                        home = user.pw_dir
                        if os.path.exists(home):
                            
                            bashrc = os.path.join(home, ".bashrc")
                            if os.path.exists(bashrc):
                                with open(bashrc, 'a') as f:
                                    f.write("\n# Configuração de idioma\n")
                                    f.write("export LANG=pt_BR.UTF-8\n")
                                    f.write("export LANGUAGE=pt_BR:pt:en\n")
                                    f.write("export LC_ALL=pt_BR.UTF-8\n")
                            
                            
                            zshrc = os.path.join(home, ".zshrc")
                            if os.path.exists(zshrc):
                                with open(zshrc, 'a') as f:
                                    f.write("\n# Configuração de idioma\n")
                                    f.write("export LANG=pt_BR.UTF-8\n")
                                    f.write("export LANGUAGE=pt_BR:pt:en\n")
                                    f.write("export LC_ALL=pt_BR.UTF-8\n")
                            
                            
                            self._execute_command(f"chown -R {user.pw_name}:{user.pw_name} {home}/.bashrc {home}/.zshrc 2>/dev/null || true")
                
               
                print("Configurando interface gráfica...")
                if self.distro in ['ubuntu', 'debian', 'linuxmint', 'pop', 'elementary', 'zorin']:
                    self._execute_command("apt-get install -y task-brazilian-portuguese")
                
                if os.path.exists("/usr/bin/localectl"):
                    self._execute_command("localectl set-locale LANG=pt_BR.UTF-8")
                    self._execute_command("localectl set-keymap br-abnt2")
                
              
                if os.path.exists("/etc/X11/xorg.conf.d"):
                    if not os.path.exists("/etc/X11/xorg.conf.d/00-keyboard.conf"):
                        with open("/etc/X11/xorg.conf.d/00-keyboard.conf", 'w') as f:
                            f.write('Section "InputClass"\n')
                            f.write('    Identifier "system-keyboard"\n')
                            f.write('    MatchIsKeyboard "on"\n')
                            f.write('    Option "XkbLayout" "br"\n')
                            f.write('    Option "XkbVariant" "abnt2"\n')
                            f.write('EndSection\n')
            
            self._print_success("Sistema configurado para Português do Brasil!")
            self._print_info("As alterações completas serão visíveis após reiniciar o sistema.")
            self._print_warning("O teclado também foi configurado para o padrão ABNT2 brasileiro.")
        else:
            self._print_info("Tradução do sistema ignorada.")

    def install_rich_if_needed(self):
        try:
            import rich
            return True
        except ImportError:
            print("Instalando a biblioteca 'rich' para melhorar a interface...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "rich", "tqdm"])
                print("Biblioteca 'rich' instalada! Reiniciando o script...")
                os.execv(sys.executable, ['python3'] + sys.argv)
                return True
            except Exception as e:
                print(f"Não foi possível instalar a biblioteca 'rich'. Continuando com a interface básica.")
                print(f"Erro: {str(e)}")
                return False

    def run(self):
        self._check_root()
        
        if not RICH_AVAILABLE:
            self.install_rich_if_needed()
        
        self.show_banner()
        
        self._print_header("Preparando o Sistema")
        if RICH_AVAILABLE:
            with Progress(SpinnerColumn(), TextColumn("[bold blue]Atualizando repositórios...")) as progress:
                task = progress.add_task("atualizando", total=None)
                self._execute_command(self.pkg_update)
        else:
            print("Atualizando repositórios...")
            self._execute_command(self.pkg_update)
        
        basic_deps = ['wget', 'curl', 'ca-certificates', 'openssl']
        self._install_deps(basic_deps)
        
        options = [
            ("1", "🔑 Configurar Acesso SSH para Root", self.configure_root_ssh),
            ("2", "⏳ Desativar Timeout do SSH", self.disable_ssh_timeout),
            ("3", "💾 Criar/Remover Memória Swap", self.create_swap),
            ("4", "🏗️ Ativar Arquitetura 32 bits", self.enable_32bit_arch),
            ("5", "🔐 Configurar Certificado SSL", self.configure_ssl_certificate),
            ("6", "🗑️ Remover Certificados SSL", self.remove_ssl_certificates),
            ("7", "🔌 Desativar Serviços Desnecessários", self.disable_services),
            ("8", "🌎 Traduzir Sistema para Português", self.translate_to_portuguese),
        ]
        
        all_option = "9"
        exit_option = "0"
        
        while True:
            self._print_header("Menu Principal")
            
            if RICH_AVAILABLE:
                menu_panel = Panel(
                    "\n".join([f"[cyan]{opt[0]}[/] - {opt[1]}" for opt in options]) + 
                    f"\n\n[yellow]{all_option}[/] - 🔄 Executar Todas as Configurações" +
                    f"\n[red]{exit_option}[/] - ❌ Sair",
                    title="Opções Disponíveis",
                    border_style="blue",
                    padding=(1, 2)
                )
                self.console.print(menu_panel)
                
                choice = Prompt.ask("\nEscolha uma opção", choices=[opt[0] for opt in options] + [all_option, exit_option])
            else:
                for opt_num, opt_name, _ in options:
                    print(f"{opt_num} - {opt_name}")
                print(f"{all_option} - 🔄 Executar Todas as Configurações")
                print(f"{exit_option} - ❌ Sair")
                
                choice = input("\nEscolha uma opção: ")
            
            if choice == all_option:  
                for _, _, func in options:
                    if func != self.remove_ssl_certificates:  
                        func()
                
                if self._ask("\n🔄 Deseja reiniciar o sistema para aplicar todas as alterações?"):
                    self._print_info("Reiniciando o sistema em 5 segundos...")
                    time.sleep(5)
                    self._execute_command("reboot")
                else:
                    self._print_info("Lembre-se que algumas alterações só serão aplicadas após reiniciar o sistema.")
                break
                
            elif choice == exit_option:  
                self._print_info("Encerrando o programa. Até a próxima! 👋")
                break
                
            else:
                for opt_num, _, func in options:
                    if choice == opt_num:
                        func()
                        break
                
                input("\nPressione Enter para continuar...")
                os.system('clear')
                self.show_banner()


if __name__ == "__main__":
    setup = LinuxSetup()
    setup.run()
