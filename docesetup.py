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
        self.script_version = "0.7"
        
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
            self.console.print(Panel(f"[bold cyan]{text}[/]", expand=False))
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
                f"[cyan]Sistema detectado: {self.distro} {self.version}[/]",
                padding=(1, 15),
                title="Bem-vindo!",
                border_style="blue"
            ))
        else:
            print(f"\n==== 🍬 Doce Setup v{self.script_version} ====")
            print(f"Sistema detectado: {self.distro} {self.version}\n")

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
            else:
                self._print_error("Arquivo de configuração SSH não encontrado.")
        else:
            self._print_info("Configuração de timeout do SSH ignorada.")

    def create_swap(self):
        self._print_header("Configuração de Memória Swap")
        
        swap_exists = self._get_command_output("swapon --show")
        if swap_exists:
            self._print_info("Memória swap já existe no sistema.")
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
        else:
            self._print_info("Ativação da arquitetura 32 bits ignorada.")

    def configure_ssl_certificate(self):
    self._print_header("Configuração de Certificado SSL")
    
    if self._ask("🔐 Deseja configurar um certificado SSL gratuito?"):
        if not shutil.which('certbot'):
            self._print_info("Instalando Certbot...")
            
            if RICH_AVAILABLE:
                with Progress(SpinnerColumn(), TextColumn("[bold blue]Instalando Certbot...")) as progress:
                    task = progress.add_task("instalando", total=None)
                    
                    if self.distro in ['ubuntu', 'debian', 'linuxmint', 'pop', 'elementary', 'zorin']:
                        self._execute_command("apt-get install -y certbot python3-certbot-apache")
                    elif self.distro in ['fedora', 'centos', 'rhel', 'rocky', 'almalinux']:
                        self._execute_command("dnf install -y certbot || yum install -y certbot")
                    elif self.distro in ['arch', 'manjaro', 'endeavouros']:
                        self._execute_command("pacman -S --noconfirm certbot")
                    else:
                        self._execute_command("apt-get install -y certbot || dnf install -y certbot || yum install -y certbot || pacman -S --noconfirm certbot")
            else:
                print("Instalando Certbot...")
                if self.distro in ['ubuntu', 'debian', 'linuxmint', 'pop', 'elementary', 'zorin']:
                    self._execute_command("apt-get install -y certbot python3-certbot-apache")
                elif self.distro in ['fedora', 'centos', 'rhel', 'rocky', 'almalinux']:
                    self._execute_command("dnf install -y certbot || yum install -y certbot")
                elif self.distro in ['arch', 'manjaro', 'endeavouros']:
                    self._execute_command("pacman -S --noconfirm certbot")
                else:
                    self._execute_command("apt-get install -y certbot || dnf install -y certbot || yum install -y certbot || pacman -S --noconfirm certbot")
        
        self._print_info("Somente certificados baseados em domínio estão disponíveis, pois são reconhecidos pelos navegadores sem avisos de segurança, diferente de certificados baseados em IP.")
        
        email = input("Digite seu email para notificações de segurança e renovação: ")
        
        domains = []
        while True:
            domain = input("Digite um domínio ou subdomínio (ex: seudominio.com, sub.seudominio.com) ou deixe vazio para finalizar: ")
            if not domain:
                break
                
            if domain.replace('.', '').isdigit():
                self._print_error("Domínio inválido. Por favor, use um nome de domínio válido.")
                continue
                
            domains.append(domain)
            self._print_info(f"Domínio '{domain}' adicionado à lista.")
        
        if not domains:
            self._print_error("Nenhum domínio foi especificado. A configuração SSL foi cancelada.")
            return
        
        domains_str = ",".join([f"-d {d}" for d in domains])
        primary_domain = domains[0]
        
        self._print_info(f"Configurando certificado SSL para: {', '.join(domains)}...")
        
        if RICH_AVAILABLE:
            with Progress(SpinnerColumn(), TextColumn(f"[bold blue]Obtendo certificado para {len(domains)} domínio(s)...")) as progress:
                task = progress.add_task("obtendo", total=None)
                self._execute_command(f"certbot certonly --standalone {domains_str} --email {email} --agree-tos --non-interactive")
        else:
            print(f"Obtendo certificado para {len(domains)} domínio(s)...")
            self._execute_command(f"certbot certonly --standalone {domains_str} --email {email} --agree-tos --non-interactive")
        
        cron_job = "0 3 * * * root certbot renew --quiet"
        with open('/etc/cron.d/certbot', 'w') as f:
            f.write(f"SHELL=/bin/sh\n")
            f.write(f"PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin\n")
            f.write(f"{cron_job}\n")
        
        self._print_success(f"Certificado SSL para {len(domains)} domínio(s) instalado com sucesso!")
        self._print_info(f"Certificados armazenados em: /etc/letsencrypt/live/{primary_domain}/")
        self._print_info("A renovação automática foi configurada para ocorrer diariamente às 3h da manhã.")
        
        if self._ask("Deseja adicionar outro certificado para diferentes domínios?"):
            self.configure_ssl_certificate()
    else:
        self._print_info("Configuração do certificado SSL ignorada.")

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
            
            selected_services = []
            for service in services_to_disable:
                if self._ask(f"Deseja desativar o serviço {service}?"):
                    selected_services.append(service)
            
            if not selected_services:
                self._print_info("Nenhum serviço selecionado para desativação.")
                return
            
            self._print_info("Desativando serviços selecionados...")
            
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
        
            self._print_success("Serviços desnecessários desativados com sucesso!")
        else:
            self._print_info("Desativação de serviços ignorada.")
            
    def install_rich_if_needed(self):
        """Tenta instalar o pacote Rich se estiver faltando para melhorar a interface"""
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
        """Executa todas as etapas do setup"""
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
            ("3", "💾 Criar Memória Swap", self.create_swap),
            ("4", "🏗️ Ativar Arquitetura 32 bits", self.enable_32bit_arch),
            ("5", "🔐 Configurar Certificado SSL", self.configure_ssl_certificate),
            ("6", "🔌 Desativar Serviços Desnecessários", self.disable_services),
        ]
        
        all_option = "8"
        exit_option = "9"
        
        while True:
            self._print_header("Menu Principal")
            
            if RICH_AVAILABLE:
                for opt_num, opt_name, _ in options:
                    self.console.print(f"[cyan]{opt_num}[/] - {opt_name}")
                self.console.print(f"[yellow]{all_option}[/] - 🔄 Executar Todas as Configurações")
                self.console.print(f"[red]{exit_option}[/] - ❌ Sair")
                
                choice = Prompt.ask("\nEscolha uma opção", choices=[opt[0] for opt in options] + [all_option, exit_option])
            else:
                for opt_num, opt_name, _ in options:
                    print(f"{opt_num} - {opt_name}")
                print(f"{all_option} - 🔄 Executar Todas as Configurações")
                print(f"{exit_option} - ❌ Sair")
                
                choice = input("\nEscolha uma opção: ")
            
            if choice == all_option:  
                for _, _, func in options:
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


if __name__ == "__main__":
    setup = LinuxSetup()
    setup.run()
