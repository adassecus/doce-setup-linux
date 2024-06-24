#!/bin/bash

echo "🍬 Bem-vindo ao DoceSetup - Seu Assistente de Configuração do Debian Server!"
echo "Por favor, responda às perguntas para configurar o servidor de forma fácil e rápida."

# Função para fazer perguntas e capturar respostas
ask() {
    while true; do
        echo -n "$1 (y/n): "
        read -r yn < /dev/tty
        case $yn in
            [Yy]* ) return 0;;
            [Nn]* ) return 1;;
            * ) echo "Por favor, responda com y ou n.";;
        esac
    done
}

# Função para detectar a porta SSH
detectar_porta_ssh() {
  PORTA_SSH=$(grep -E "^Port " /etc/ssh/sshd_config | awk '{print $2}')
  if [ -z "$PORTA_SSH" ]; then
    PORTA_SSH=22
  fi
  echo "🔍 Porta SSH detectada: $PORTA_SSH"
}

# Função para configurar o firewall
configurar_firewall() {
  echo "🔥 Configurando firewall..."
  apt-get update -qq > /dev/null
  apt-get install -y ufw -qq > /dev/null
  echo "y" | ufw reset > /dev/null 2>&1
  ufw default deny incoming > /dev/null
  ufw default allow outgoing > /dev/null
  
  # Detectar e permitir porta SSH
  detectar_porta_ssh
  ufw limit $PORTA_SSH/tcp > /dev/null # Habilitar rate limiting para SSH

  # Permitir todas as portas de jogos e serviços populares
  PORTAS_SERVICOS=("25565" "27015" "27016" "7777" "2302" "6667" "28960" "44405" "3724" "6112" "6881" "3784" "5000" "443" "80" "5222" "5223" "3478" "5938")
  for porta in "${PORTAS_SERVICOS[@]}"; do
    ufw allow $porta > /dev/null
  done

  # Configurar proteção contra SYN Flood
  ufw logging on
  ufw limit synflood

  ufw enable < /dev/null > /dev/null 2>&1
  ufw reload < /dev/null > /dev/null 2>&1
  echo "✅ Firewall configurado com sucesso!"
}

# Função para instalar e configurar o fail2ban
configurar_fail2ban() {
  echo "🛡️ Instalando e configurando o fail2ban..."
  apt-get install -y fail2ban -qq > /dev/null
  systemctl enable fail2ban > /dev/null 2>&1
  systemctl start fail2ban > /dev/null 2>&1
  
  # Configuração avançada do fail2ban
  cat <<EOF > /etc/fail2ban/jail.local
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = $PORTA_SSH
filter = sshd
logpath = /var/log/auth.log

[http-get-dos]
enabled = true
port = http,https
filter = http-get-dos
logpath = /var/log/apache2/access.log
maxretry = 300
findtime = 300
bantime = 3600

[apache-auth]
enabled = true
port = http,https
filter = apache-auth
logpath = /var/log/apache2/error.log
maxretry = 6

[game-server]
enabled = true
port = 25565,27015,27016,7777,2302,6667,28960,44405,3724,6112,6881,3784,5000
filter = game-server
logpath = /var/log/syslog
maxretry = 10
findtime = 60
bantime = 600

[discord-telegram]
enabled = true
port = 443,80,5222,5223,3478,5938
filter = discord-telegram
logpath = /var/log/syslog
maxretry = 10
findtime = 60
bantime = 600

[generic-dos]
enabled = true
port = all
filter = generic-dos
logpath = /var/log/syslog
maxretry = 100
findtime = 60
bantime = 600
EOF

  cat <<EOF > /etc/fail2ban/filter.d/game-server.conf
[Definition]
failregex = ^<HOST> -.*"(GET|POST).*
ignoreregex =
EOF

  cat <<EOF > /etc/fail2ban/filter.d/discord-telegram.conf
[Definition]
failregex = ^<HOST> -.*"(GET|POST).*
ignoreregex =
EOF

  cat <<EOF > /etc/fail2ban/filter.d/generic-dos.conf
[Definition]
failregex = ^<HOST> -.*"(GET|POST|HEAD|OPTIONS).*
ignoreregex =
EOF

  systemctl restart fail2ban > /dev/null
  echo "✅ Fail2ban configurado com sucesso!"
}

# Função para instalar e configurar o ModSecurity
configurar_modsecurity() {
  echo "🔒 Instalando e configurando o ModSecurity..."
  apt-get install -y libapache2-mod-security2 -qq > /dev/null
  a2enmod security2 > /dev/null
  systemctl restart apache2 > /dev/null
  echo "✅ ModSecurity configurado com sucesso!"
}

# Função para configurar sysctl para proteção adicional
configurar_sysctl_protecao() {
  echo "🔧 Configurando parâmetros de rede para proteção adicional..."
  
  # Remover configurações duplicadas e obsoletas
  sed -i '/net.ipv4.tcp_tw_recycle/d' /etc/sysctl.conf
  sed -i '/net.ipv4.conf.all.rp_filter/d' /etc/sysctl.conf
  sed -i '/net.ipv4.conf.default.rp_filter/d' /etc/sysctl.conf
  sed -i '/net.ipv4.icmp_echo_ignore_broadcasts/d' /etc/sysctl.conf
  sed -i '/net.ipv4.tcp_syncookies/d' /etc/sysctl.conf
  sed -i '/net.ipv4.tcp_max_syn_backlog/d' /etc/sysctl.conf
  sed -i '/net.ipv4.tcp_synack_retries/d' /etc/sysctl.conf
  sed -i '/net.ipv4.tcp_syn_retries/d' /etc/sysctl.conf
  sed -i '/net.ipv4.tcp_tw_reuse/d' /etc/sysctl.conf
  sed -i '/net.ipv4.icmp_ratelimit/d' /etc/sysctl.conf
  sed -i '/net.ipv4.ipfrag_low_thresh/d' /etc/sysctl.conf
  sed -i '/net.ipv4.ipfrag_time/d' /etc/sysctl.conf
  sed -i '/net.ipv4.tcp_rfc1337/d' /etc/sysctl.conf
  sed -i '/net.ipv4.tcp_timestamps/d' /etc/sysctl.conf
  sed -i '/net.ipv4.conf.all.accept_source_route/d' /etc/sysctl.conf
  sed -i '/net.ipv4.conf.all.accept_redirects/d' /etc/sysctl.conf
  sed -i '/net.ipv4.conf.all.secure_redirects/d' /etc/sysctl.conf

  # Adicionar novas configurações
  cat <<EOF >> /etc/sysctl.conf
# Proteção contra IP spoofing
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1

# Proteção contra ataques Smurf
net.ipv4.icmp_echo_ignore_broadcasts = 1

# Proteção contra ataques SYN flood
net.ipv4.tcp_syncookies = 1

# Proteção contra ataques de negação de serviço (DoS)
net.ipv4.tcp_max_syn_backlog = 2048
net.ipv4.tcp_synack_retries = 2
net.ipv4.tcp_syn_retries = 5

# Proteção contra ataques de requisições maliciosas
net.ipv4.tcp_tw_reuse = 1

# Limitar taxa de novas conexões TCP
net.ipv4.tcp_max_syn_backlog = 2048
net.ipv4.tcp_synack_retries = 2
net.ipv4.tcp_syn_retries = 5

# Limitar taxa de pacotes ICMP
net.ipv4.icmp_ratelimit = 100

# Proteção contra ataques de fragmentação de IP
net.ipv4.ipfrag_low_thresh = 196608
net.ipv4.ipfrag_time = 60

# Limitações adicionais para prevenção de DoS
net.ipv4.tcp_rfc1337 = 1
net.ipv4.tcp_timestamps = 0
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.all.secure_redirects = 1
EOF

  sysctl -p > /dev/null 2>&1
  echo "✅ Parâmetros de rede configurados com sucesso!"
}

# Função para criar o serviço systemd que detecta a porta SSH e libera no firewall
criar_servico_systemd() {
  echo "🔧 Configurando serviço systemd..."
  
  # Remover serviço anterior se existir
  systemctl disable detect-ssh.service > /dev/null 2>&1
  rm -f /etc/systemd/system/detect-ssh.service
  rm -f /usr/local/bin/detect_ssh.sh
  
  cat <<EOF > /etc/systemd/system/detect-ssh.service
[Unit]
Description=Detectar e liberar porta SSH no firewall

[Service]
ExecStart=/usr/local/bin/detect_ssh.sh
Type=oneshot
RemainAfterExit=true

[Install]
WantedBy=multi-user.target
EOF

  cat <<EOF > /usr/local/bin/detect_ssh.sh
#!/bin/bash
PORTA_SSH=\$(grep -E "^Port " /etc/ssh/sshd_config | awk '{print \$2}')
if [ -z "\$PORTA_SSH" ]; then
  PORTA_SSH=22
fi
ufw allow \$PORTA_SSH > /dev/null 2>&1
EOF

  chmod +x /usr/local/bin/detect_ssh.sh
  systemctl enable detect-ssh.service > /dev/null 2>&1
  echo "✅ Serviço systemd para detectar e liberar porta SSH configurado com sucesso!"
}

# Função para alterar ou adicionar configuração no arquivo
update_config() {
    local file="$1"
    local param="$2"
    local value="$3"
    if grep -q "^[#]*\s*${param}\s*" "$file"; then
        sed -i "s/^[#]*\s*${param}.*/${param} ${value}/" "$file"
    else
        echo "${param} ${value}" >> "$file"
    fi
}

# Função para alterar o idioma do sistema
change_locale() {
    echo "Escolha um idioma da lista abaixo digitando o número correspondente:"
    echo "1. 🇺🇸 en_US.UTF-8 - Inglês (Estados Unidos)"
    echo "2. 🇪🇸 es_ES.UTF-8 - Espanhol (Espanha)"
    echo "3. 🇫🇷 fr_FR.UTF-8 - Francês (França)"
    echo "4. 🇩🇪 de_DE.UTF-8 - Alemão (Alemanha)"
    echo "5. 🇮🇹 it_IT.UTF-8 - Italiano (Itália)"
    echo "6. 🇧🇷 pt_BR.UTF-8 - Português (Brasil)"
    echo "7. 🇷🇺 ru_RU.UTF-8 - Russo (Rússia)"
    echo "8. 🇨🇳 zh_CN.UTF-8 - Chinês (China)"
    echo "9. 🇯🇵 ja_JP.UTF-8 - Japonês (Japão)"
    echo "10. 🇰🇷 ko_KR.UTF-8 - Coreano (Coreia)"
    echo "11. 🇸🇦 ar_SA.UTF-8 - Árabe (Arábia Saudita)"

    read -p "Digite o número do idioma escolhido: " lang_choice

    case $lang_choice in
        1) new_locale="en_US.UTF-8"; new_repo="http://deb.debian.org/debian/";;
        2) new_locale="es_ES.UTF-8"; new_repo="http://ftp.es.debian.org/debian/";;
        3) new_locale="fr_FR.UTF-8"; new_repo="http://ftp.fr.debian.org/debian/";;
        4) new_locale="de_DE.UTF-8"; new_repo="http://ftp.de.debian.org/debian/";;
        5) new_locale="it_IT.UTF-8"; new_repo="http://ftp.it.debian.org/debian/";;
        6) new_locale="pt_BR.UTF-8"; new_repo="http://ftp.br.debian.org/debian/";;
        7) new_locale="ru_RU.UTF-8"; new_repo="http://ftp.ru.debian.org/debian/";;
        8) new_locale="zh_CN.UTF-8"; new_repo="http://ftp.cn.debian.org/debian/";;
        9) new_locale="ja_JP.UTF-8"; new_repo="http://ftp.jp.debian.org/debian/";;
        10) new_locale="ko_KR.UTF-8"; new_repo="http://ftp.kr.debian.org/debian/";;
        11) new_locale="ar_SA.UTF-8"; new_repo="http://ftp.sa.debian.org/debian/";;
        *) echo "Escolha inválida. Usando en_US.UTF-8 por padrão."; new_locale="en_US.UTF-8"; new_repo="http://deb.debian.org/debian/";;
    esac

    echo "Configurando o idioma do sistema para $new_locale..."
    sed -i "/$new_locale/ s/^#//g" /etc/locale.gen
    locale-gen > /dev/null 2>&1
    update-locale LANG=$new_locale LANGUAGE=$new_locale LC_ALL=$new_locale
    echo "Idioma do sistema alterado para $new_locale com sucesso! 🎉"

    if ask "Deseja alterar o repositório de pacotes para o mais próximo baseado no idioma selecionado?"; then
        echo "Alterando repositório de pacotes para o mais próximo e ativando o componente non-free..."
        
        # Remove todos os repositórios existentes
        sed -i '/^deb .*debian.org\/debian/d' /etc/apt/sources.list
        sed -i '/^deb-src .*debian.org\/debian/d' /etc/apt/sources.list

        # Adiciona os novos repositórios ao sources.list
        cat <<EOF > /etc/apt/sources.list
deb $new_repo bullseye main contrib non-free
deb-src $new_repo bullseye main contrib non-free

deb $new_repo-security bullseye-security main contrib non-free
deb-src $new_repo-security bullseye-security main contrib non-free

deb $new_repo bullseye-updates main contrib non-free
deb-src $new_repo bullseye-updates main contrib non-free

deb $new_repo bullseye-backports main contrib non-free
deb-src $new_repo bullseye-backports main contrib non-free
EOF

        apt update > /dev/null 2>&1
        echo "Repositório de pacotes alterado para o mais próximo com sucesso e componente non-free ativado! 📦"
    fi
}

# Alterar senha do root
if ask "🔑 Deseja alterar a senha do root?"; then
    echo "Vamos alterar a senha do root. Por favor, digite a nova senha:"
    passwd root
    echo "Fazendo alterações na configuração do SSH..."
    update_config /etc/ssh/sshd_config "PermitRootLogin" "yes"
    update_config /etc/ssh/sshd_config "PasswordAuthentication" "yes"
    service ssh restart > /dev/null 2>&1
    if ask "🔄 Deseja aplicar a mesma senha do root para todos os outros usuários?"; then
        echo "Aplicando a mesma senha do root para todos os outros usuários..."
        for user in $(cut -f1 -d: /etc/passwd); do
            echo "$user:$(grep root /etc/shadow | cut -d: -f2)" | chpasswd -e
        done
    fi
fi

# Alterar porta do SSH
if ask "🔧 Deseja alterar a porta do SSH?"; then
    echo "Digite a nova porta do SSH:"
    read new_port
    echo "Alterando a porta do SSH para $new_port..."
    update_config /etc/ssh/sshd_config "Port" "$new_port"
    service ssh restart > /dev/null 2>&1
fi

# Aumentar o limite de timeout do SSH
if ask "⏳ Deseja aumentar o limite de timeout do SSH para 5 horas?"; then
    echo "Aumentando o limite de timeout do SSH para 5 horas..."
    update_config /etc/ssh/sshd_config "ClientAliveInterval" "290"
    update_config /etc/ssh/sshd_config "ClientAliveCountMax" "63"
    service ssh restart > /dev/null 2>&1
    echo "Limite de timeout do SSH aumentado para 5 horas com sucesso! ⏳"
fi

# Criar memória swap
if [ -z "$(swapon --show)" ]; then
    if ask "💾 Deseja criar uma memória swap?"; then
        echo "Digite o tamanho da memória swap (por exemplo, 4G para 4 Gigabytes, lembre-se de usar 'G' maiúsculo):"
        read swap_size
        swap_size=$(echo "$swap_size" | tr '[:lower:]' '[:upper:]')
        if [ -z "$swap_size" ];then
            swap_size="4G"
        fi
        echo "Criando memória swap de $swap_size..."
        fallocate -l $swap_size /swapfile
        chmod 600 /swapfile
        mkswap /swapfile > /dev/null 2>&1
        swapon /swapfile
        if grep -q '/swapfile' /etc/fstab; then
            sed -i 's|.*swapfile.*|/swapfile none swap sw 0 0|' /etc/fstab
        else
            echo '/swapfile none swap sw 0 0' >> /etc/fstab
        fi
        echo "Memória swap criada com sucesso! 💾"
    fi
else
    echo "Memória swap já existe. Pulando esta etapa."
fi

# Configurar adaptador de rede
if ask "🌐 Deseja otimizar o adaptador de rede para melhorar o desempenho?"; then
    echo "Configurando o adaptador de rede para melhor desempenho..."
    for iface in $(ls /sys/class/net/ | grep -v lo); do
        if [ ! -f "/etc/network/interfaces.d/$iface" ]; then
            touch "/etc/network/interfaces.d/$iface"
        fi
        ethtool -s $iface speed 1000 duplex full autoneg on > /dev/null 2>&1
        if ! grep -q "options $iface txqueuelen=1000" /etc/network/interfaces.d/$iface; then
            echo "options $iface txqueuelen=1000" >> /etc/network/interfaces.d/$iface
        fi
        ifconfig $iface txqueuelen 1000 > /dev/null 2>&1
        ethtool -G $iface rx 4096 tx 4096 > /dev/null 2>&1
        ethtool -K $iface gro on > /dev/null 2>&1
        ethtool -K $iface gso on > /dev/null 2>&1
        ethtool -K $iface tso on > /dev/null 2>&1
    done
    echo "Configuração de rede concluída! 🌐"
fi

# Ativar arquitetura 32 bits
if ask "🏗️ Deseja ativar a arquitetura 32 bits?"; then
    echo "Ativando arquitetura 32 bits..."
    dpkg --add-architecture i386
    apt update > /dev/null 2>&1
    apt install -y libc6:i386 libncurses5:i386 libstdc++6:i386 > /dev/null 2>&1
    echo "Arquitetura 32 bits configurada com sucesso! 🏗️"
fi

# Instalar Apache
apache_installed=false
if ask "🌐 Deseja instalar o Apache? Isso é necessário para instalar o MariaDB e o phpMyAdmin posteriormente."; then
    echo "Instalando dependências do Apache..."
    apt install -y apt-transport-https ca-certificates curl software-properties-common > /dev/null 2>&1
    echo "Instalando Apache..."
    apt install -y apache2 > /dev/null 2>&1
    systemctl start apache2 > /dev/null 2>&1
    systemctl enable apache2 > /dev/null 2>&1
    echo "Apache instalado com sucesso! 🌐"
    apache_installed=true
fi

# Instalar MariaDB
mariadb_installed=false
if $apache_installed && ask "🗄️ Deseja instalar o MariaDB?"; then
    echo "Instalando dependências do MariaDB..."
    apt install -y software-properties-common dirmngr > /dev/null 2>&1
    apt install -y mariadb-server mariadb-client > /dev/null 2>&1

    # Certifique-se de que mysql_secure_installation esteja disponível
    if ! command -v mysql_secure_installation &> /dev/null; then
        echo "Erro: mysql_secure_installation não encontrado, instalando MariaDB novamente."
        apt install -y mariadb-server mariadb-client > /dev/null 2>&1
    fi

    echo "Por favor, digite a senha do root para o MariaDB:"
    read -s mariadb_root_password

    echo "Configurando MariaDB..."
    mysql_secure_installation <<EOF | grep -v 'stty:'
Y
n
Y
Y
Y
Y
EOF

    echo "Aplicando senha de root ao MariaDB e ajustando configurações..."
    mysql -u root -e "SET PASSWORD FOR root@localhost = PASSWORD('$mariadb_root_password');" 2>/dev/null
    mysql -u root -p$mariadb_root_password -e "DELETE FROM mysql.user WHERE User='';" 2>/dev/null
    mysql -u root -p$mariadb_root_password -e "DROP DATABASE IF EXISTS test;" 2>/dev/null
    mysql -u root -p$mariadb_root_password -e "FLUSH PRIVILEGES;" 2>/dev/null

    # Verificar se o arquivo de configuração do MariaDB existe antes de modificá-lo
    config_file="/etc/mysql/mariadb.conf.d/50-server.cnf"
    if [ -f "$config_file" ]; then
        echo "Desativando o modo estrito no MariaDB..."
        if grep -q "^[#]*\s*sql_mode" "$config_file"; then
            sed -i "s/^[#]*\s*sql_mode.*/sql_mode = \"\"/" "$config_file"
        else
            if grep -q "\[mysqld\]" "$config_file"; then
                sed -i "/\[mysqld\]/a sql_mode = \"\"" "$config_file"
            else
                echo "[mysqld]" >> "$config_file"
                echo "sql_mode = \"\"" >> "$config_file"
            fi
        fi
        echo "MariaDB instalado e configurado com sucesso!"
        systemctl restart mariadb > /dev/null 2>&1
    else
        echo "Arquivo de configuração do MariaDB não encontrado: $config_file"
    fi

    mariadb_installed=true
fi

# Instalar phpMyAdmin
if $apache_installed && $mariadb_installed && ask "🌐 Deseja instalar o phpMyAdmin?"; then
    echo "Instalando dependências do phpMyAdmin..."
    apt install -y php libapache2-mod-php php-mysql php-json php-pear php-mbstring > /dev/null 2>&1
    echo "Instalando phpMyAdmin..."
    echo "phpmyadmin phpmyadmin/dbconfig-install boolean true" | debconf-set-selections
    echo "phpmyadmin phpmyadmin/app-password-confirm password $mariadb_root_password" | debconf-set-selections
    echo "phpmyadmin phpmyadmin/mysql/admin-pass password $mariadb_root_password" | debconf-set-selections
    echo "phpmyadmin phpmyadmin/mysql/app-pass password $mariadb_root_password" | debconf-set-selections
    echo "phpmyadmin phpmyadmin/reconfigure-webserver multiselect apache2" | debconf-set-selections
    apt install -y phpmyadmin > /dev/null 2>&1

    echo "Configurando phpMyAdmin..."
    phpenmod mbstring
    systemctl restart apache2 > /dev/null 2>&1

    echo "Configuração do phpMyAdmin concluída! 🌐"
    echo "Você pode acessar o phpMyAdmin com o usuário 'root' e a senha do MariaDB."
fi

# Instalar Certbot e configurar SSL
if $apache_installed && ask "🔐 Deseja instalar um certificado SSL gratuito com renovação automática?"; then
    echo "Instalando Certbot..."
    apt install -y certbot python3-certbot-apache > /dev/null 2>&1

    echo "Por favor, digite seu email para notificações de segurança e renovação do certificado:"
    read email

    echo "Por favor, digite seu domínio (exemplo: seudominio.com), IP numérico não é permitido:"
    read domain

    echo "Configurando Certbot para $domain..."
    certbot --apache -d $domain --email $email --agree-tos --no-eff-email

    echo "Configurando renovação automática do certificado SSL..."
    cat <<EOF > /etc/cron.d/certbot
SHELL=/bin/sh
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
0 3 * * * root certbot renew --quiet --deploy-hook "systemctl reload apache2"
EOF

    echo "Certificado SSL instalado e configurado com sucesso! 🔐"
fi

# Instalar e configurar Caching
if ask "⚡ Deseja instalar e configurar caching com Varnish?"; then
    echo "Instalando Varnish..."
    apt install -y varnish > /dev/null 2>&1

    echo "Configurando Varnish..."
    cat <<EOF > /etc/varnish/default.vcl
vcl 4.0;
backend default {
    .host = "127.0.0.1";
    .port = "8080";
}
EOF

    update_config /etc/default/varnish "DAEMON_OPTS" "-a :80 -T localhost:6082 -f /etc/varnish/default.vcl -S /etc/varnish/secret -s malloc,256m"
    
    echo "Alterando configuração do Apache para usar a porta 8080..."
    sed -i 's/:80/:8080/g' /etc/apache2/ports.conf
    sed -i 's/:80/:8080/g' /etc/apache2/sites-available/000-default.conf

    systemctl restart apache2 > /dev/null 2>&1
    systemctl restart varnish > /dev/null 2>&1

    echo "Varnish instalado e configurado com sucesso! ⚡"
    # Liberar portas usadas pelo caching no firewall
    ufw allow 6082/tcp
    ufw allow 80/tcp
fi

# Detectar e instalar drivers mais atualizados
if ask "🔧 Deseja detectar e instalar todos os drivers mais atualizados?"; then
    echo "Configurando repositórios para incluir 'non-free'..."
    if ! grep -q 'main contrib non-free' /etc/apt/sources.list; then
        sed -i 's/main/main contrib non-free/g' /etc/apt/sources.list
    fi
    apt update > /dev/null 2>&1

    echo "Instalando ferramentas de detecção de drivers..."
    apt install -y pciutils usbutils > /dev/null 2>&1

    echo "Detectando hardware e instalando drivers mais atualizados..."
    apt install -y firmware-linux-free firmware-linux-nonfree > /dev/null 2>&1
    apt install -y firmware-misc-nonfree > /dev/null 2>&1
    apt install -y firmware-realtek > /dev/null 2>&1
    apt install -y firmware-iwlwifi > /dev/null 2>&1
    apt install -y intel-microcode > /dev/null 2>&1

    echo "Drivers mais atualizados instalados com sucesso! 🔧"
fi

# Configurar sysctl para otimização
if ask "⚙️ Deseja configurar parâmetros sysctl para otimização?"; then
    echo "Configurando parâmetros sysctl para otimização..."
    cat <<EOF >> /etc/sysctl.conf

# Melhorias de desempenho
net.core.netdev_max_backlog = 5000
net.core.rmem_max = 16777216
net.core.somaxconn = 1024
net.core.wmem_max = 16777216
net.ipv4.tcp_max_syn_backlog = 20480
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216
vm.swappiness = 10
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5
EOF

    sysctl -p > /dev/null 2>&1
    echo "Parâmetros sysctl configurados com sucesso! ⚙️"
fi

# Desativar serviços não necessários
if ask "🔌 Deseja desativar serviços não necessários para liberar recursos?"; then
    echo "Desativando serviços não necessários..."
    systemctl disable cups-browsed > /dev/null 2>&1
    systemctl stop cups-browsed > /dev/null 2>&1
    systemctl mask cups-browsed > /dev/null 2>&1

    systemctl disable avahi-daemon > /dev/null 2>&1
    systemctl stop avahi-daemon > /dev/null 2>&1
    systemctl mask avahi-daemon > /dev/null 2>&1

    systemctl disable bluetooth > /dev/null 2>&1
    systemctl stop bluetooth > /dev/null 2>&1
    systemctl mask bluetooth > /dev/null 2>&1
    echo "Serviços não necessários desativados com sucesso! 🔌"
fi

# Configurar tuning automático com tuned
if ask "🛠️ Deseja configurar tuning automático com tuned?"; then
    echo "Instalando tuned..."
    apt install -y tuned > /dev/null 2>&1
    systemctl start tuned > /dev/null 2>&1
    systemctl enable tuned > /dev/null 2>&1

    echo "Configurando tuned para o perfil de desempenho..."
    tuned-adm profile throughput-performance
    echo "Tuning automático configurado com sucesso! 🛠️"
fi

# Configurar fail2ban
if ask "🛡️ Deseja configurar o fail2ban para proteção adicional?"; then
    configurar_fail2ban
fi

# Configurar ModSecurity
if ask "🔒 Deseja configurar o ModSecurity para proteção do servidor web?"; then
    configurar_modsecurity
fi

# Configurar sysctl para proteção
if ask "🔧 Deseja configurar parâmetros sysctl para proteção adicional?"; then
    configurar_sysctl_protecao
fi

# Configurar firewall
if ask "🔥 Deseja configurar o firewall para proteger todas as portas de jogos e serviços populares?"; then
    configurar_firewall
fi

# Configurar serviço systemd para detectar porta SSH
if ask "🔧 Deseja configurar um serviço para detectar e liberar automaticamente a porta SSH no firewall após reinicializações?"; then
    criar_servico_systemd
fi

# Alterar o idioma do sistema
if ask "🌍 Deseja alterar o idioma do sistema?"; then
    change_locale
fi

# Opção de reiniciar o servidor
if ask "🔄 Deseja reiniciar o servidor agora para aplicar todas as alterações?"; then
    echo "Reiniciando o servidor..."
    echo "Após reiniciar, acesse o servidor utilizando a nova porta SSH, se alterada."
    reboot
else
    echo "As alterações serão aplicadas na próxima reinicialização."
    echo "Após reiniciar, acesse o servidor utilizando a nova porta SSH, se alterada."
fi

echo "Configuração inicial do servidor concluída! Obrigado por usar o DoceSetup! 🍬"
