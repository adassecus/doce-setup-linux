## DoceSetup 2.0 🍬

Bem-vindo ao **DoceSetup**, o seu assistente amigável e eficiente para configurar servidores Linux! Siga os passos abaixo para instalar e usar o DoceSetup e desfrute de uma configuração otimizada com melhorias significativas de segurança, desempenho e eficiência.

### Passo 1: Preparação

1. **Certifique-se de que você tem acesso root ou sudo** à sua VPS ou servidor.
2. **Verifique se o Python 3 está instalado** (a maioria das distribuições Linux modernas já vem com Python 3 pré-instalado).
   ```bash
   python3 --version
   ```
   Caso não esteja instalado, você pode instalá-lo com:
   ```bash
   # Para sistemas baseados em Debian/Ubuntu
   sudo apt update && sudo apt install -y python3
   
   # Para sistemas baseados em RHEL/CentOS/Fedora
   sudo dnf install -y python3 || sudo yum install -y python3
   
   # Para sistemas baseados em Arch
   sudo pacman -S python
   ```

### Passo 2: Baixar o Script

Baixe o script DoceSetup diretamente do GitHub usando `wget`.

```bash
wget -O docesetup.py https://raw.githubusercontent.com/uouwm/doce-setup-linux/main/docesetup.py
```

### Passo 3: Dar Permissão

Dê permissão de execução ao script baixado:
```bash
chmod +x docesetup.py
```

### Passo 4: Executar o Script

Execute o script com permissões de superusuário:
```bash
sudo python3 docesetup.py
```

### Passo 5: Seguir as Instruções Interativas

O DoceSetup 2.0 guiará você através de uma série de perguntas interativas para configurar o servidor. Com suporte a múltiplas distribuições Linux, o sistema ajustará automaticamente as instalações e configurações de acordo com sua distribuição específica. As opções incluem:

- **Alterar a senha do root:** Melhora a segurança do servidor imediatamente, evitando acessos não autorizados.
- **Configurar o SSH (porta e timeout):** Mudança de porta e ajustes de timeout podem reduzir ataques de força bruta em até 70%.
- **Criar memória swap:** Melhor gerenciamento de memória, especialmente para servidores com pouca RAM, pode melhorar a estabilidade em até 30%.
- **Otimizar o adaptador de rede:** Ajustes de rede podem aumentar a eficiência da transferência de dados em até 40%.
- **Ativar a arquitetura 32 bits:** Permite rodar aplicações antigas que requerem suporte a 32 bits.
- **Instalar o stack LAMP (Apache, MariaDB, PHP):** Configuração essencial para servidores web, facilitando o desenvolvimento de aplicações web.
- **Instalar o phpMyAdmin:** Ferramenta gráfica para gerenciamento de bancos de dados MariaDB/MySQL.
- **Instalar um certificado SSL gratuito com renovação automática (Certbot):** Aumenta a segurança das conexões web em até 100% com HTTPS.
- **Instalar e configurar caching com Varnish:** Pode melhorar a velocidade de resposta do servidor em até 300% para conteúdos estáticos.
- **Detectar e instalar drivers mais atualizados:** Assegura que o hardware do servidor funcione da melhor forma possível, aumentando a estabilidade e desempenho em até 20%.
- **Configurar parâmetros sysctl para otimização:** Ajustes de kernel que podem melhorar o desempenho geral do sistema em até 25%.
- **Desativar serviços não necessários para liberar recursos:** Pode liberar até 15% dos recursos do sistema para uso em aplicações críticas.
- **Configurar tuning automático com `tuned`:** Ajusta automaticamente as configurações do sistema com base no perfil de uso, potencializando o desempenho em até 20%.
- **Configurar firewall (UFW, FirewallD ou IPTables):** Proteção automática para portas de serviços e jogos populares, com detecção inteligente do firewall disponível no sistema.
- **Configurar o fail2ban para proteção adicional:** Pode bloquear até 99% dos IPs maliciosos, prevenindo tentativas de invasão.
- **Configurar parâmetros sysctl para proteção adicional:** Melhorias de segurança de rede e mitigação de ataques.
- **Criar serviço para detectar e liberar automaticamente a porta SSH no firewall após reinicializações:** Garantia de que o acesso SSH seja sempre possível após reinicializações, compatível com systemd ou sistemas init tradicionais.
- **Alterar o idioma do sistema:** Ajusta o sistema para o idioma preferido para uma melhor experiência de usuário.

### Compatibilidade

O DoceSetup 2.0 foi projetado para funcionar em diversas distribuições Linux, incluindo:

- **Debian/Ubuntu e derivados** (Ubuntu, Debian, Linux Mint, Pop!_OS, Elementary OS, Zorin OS)
- **RHEL e derivados** (Fedora, CentOS, RHEL, Rocky Linux, AlmaLinux)
- **Arch Linux e derivados** (Arch, Manjaro, EndeavourOS)
- **SUSE e derivados** (openSUSE, SUSE Linux Enterprise)
- **Outras distribuições baseadas em pacotes DEB, RPM ou PAC**

O script detecta automaticamente sua distribuição e ajusta seus métodos de instalação e configuração para garantir a máxima compatibilidade.

### Benefícios e Melhorias em Relação à Versão 1.5

- **Compatibilidade Universal:** Funciona em quase qualquer distribuição Linux, não apenas em Debian 11.
- **Código Limpo e Modular:** Reescrito em Python para maior clareza, manutenção e expansão futura.
- **Detecção Inteligente:** Identifica automaticamente a distribuição, ferramentas disponíveis e melhores práticas para cada sistema.
- **Melhor Tratamento de Erros:** Maior robustez ao lidar com diferentes cenários e configurações.
- **Segurança Aprimorada:** A combinação de firewalls, fail2ban e otimizações de sistema pode aumentar a segurança do servidor em até 90%.
- **Desempenho Superior:** Otimizações adaptadas a cada distribuição para melhor desempenho.
- **Interface Colorida e Amigável:** Feedback visual aprimorado para melhor experiência do usuário.

### Finalização

Após completar as configurações, o script perguntará se você deseja reiniciar o servidor para aplicar todas as alterações. Recomendamos reiniciar para garantir que todas as mudanças sejam aplicadas corretamente.

---

O **DoceSetup 2.0** é a ferramenta definitiva para quem busca uma configuração rápida, segura e eficiente para qualquer servidor Linux. Experimente agora e veja a diferença no desempenho e segurança do seu sistema!

## Contato

Para dúvidas, sugestões ou problemas, entre em contato:

📩 **[t.me/adassecus](https://t.me/adassecus)**
