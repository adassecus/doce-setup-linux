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
    update_config /etc/ssh/sshd_config "ClientAliveInterval" "18000"
    update_config /etc/ssh/sshd_config "ClientAliveCountMax" "3"
    service ssh restart > /dev/null 2>&1
fi

# Criar memória swap
if [ -z "$(swapon --show)" ]; then
    if ask "💾 Deseja criar uma memória swap?"; then
        echo "Digite o tamanho da memória swap (por exemplo, 4G para 4 Gigabytes, lembre-se de usar 'G' maiúsculo):"
        read swap_size
        swap_size=$(echo "$swap_size" | tr '[:lower:]' '[:upper:]')
        if [ -z "$swap_size" ]; then
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
    mysql_secure_installation <<EOF | grep -v 'Enter current password for root' > /dev/null 2>&1
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
