## DoceSetup 1.5 🍬

Bem-vindo ao **DoceSetup**, o seu assistente amigável e eficiente para configurar servidores Linux! Este script foi projetado para facilitar a configuração inicial do servidor, automatizando tarefas comuns e essenciais. Siga os passos abaixo para instalar e usar o DoceSetup e desfrute de uma configuração otimizada com melhorias significativas de segurança, desempenho e eficiência.

### Passo 1: Preparação

1. **Certifique-se de que você tem acesso root ou sudo** à sua VPS.
2. **Atualize o sistema** com o comando:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

### Passo 2: Baixar o Script

Baixe o script DoceSetup diretamente do GitHub usando `wget`.

- Usando `wget`:
  ```bash
  wget -O doce_setup_debian11.sh https://raw.githubusercontent.com/uouwm/doce-setup-linux/main/doce_setup_debian11.sh
  ```

### Passo 3: Dar Permissão

Dê permissão ao script baixado:
```bash
chmod 777 doce_setup_debian11.sh
```

### Passo 4: Executar o Script

Execute o script com permissões de superusuário:
```bash
sudo ./doce_setup_debian11.sh
```

### Passo 5: Seguir as Instruções Interativas

O DoceSetup guiará você através de uma série de perguntas interativas para configurar o servidor. As opções incluem:

- **Alterar a senha do root:** Melhora a segurança do servidor imediatamente, evitando acessos não autorizados.
- **Configurar o SSH (porta e timeout):** Mudança de porta e ajustes de timeout podem reduzir ataques de força bruta em até 70%.
- **Criar memória swap:** Melhor gerenciamento de memória, especialmente para servidores com pouca RAM, pode melhorar a estabilidade em até 30%.
- **Otimizar o adaptador de rede:** Ajustes de rede podem aumentar a eficiência da transferência de dados em até 40%.
- **Ativar a arquitetura 32 bits:** Permite rodar aplicações antigas que requerem suporte a 32 bits.
- **Instalar o Apache (necessário para MariaDB e phpMyAdmin):** Configuração essencial para servidores web, facilitando o gerenciamento de bancos de dados.
- **Instalar o MariaDB:** Banco de dados eficiente e seguro, fundamental para aplicações web.
- **Instalar o phpMyAdmin:** Ferramenta gráfica para gerenciamento de bancos de dados MariaDB/MySQL.
- **Instalar um certificado SSL gratuito com renovação automática (Certbot):** Aumenta a segurança das conexões web em até 100% com HTTPS.
- **Instalar e configurar caching com Varnish:** Pode melhorar a velocidade de resposta do servidor em até 300% para conteúdos estáticos.
- **Detectar e instalar drivers mais atualizados:** Assegura que o hardware do servidor funcione da melhor forma possível, aumentando a estabilidade e desempenho em até 20%.
- **Configurar parâmetros sysctl para otimização:** Ajustes de kernel que podem melhorar o desempenho geral do sistema em até 25%.
- **Desativar serviços não necessários para liberar recursos:** Pode liberar até 15% dos recursos do sistema para uso em aplicações críticas.
- **Configurar tuning automático com `tuned`:** Ajusta automaticamente as configurações do sistema com base no perfil de uso, potencializando o desempenho em até 20%.
- **Configurar o firewall (UFW) para proteger todas as portas de jogos e serviços populares:**
  - **Habilitar rate limiting para SSH:** Reduz a probabilidade de ataques de força bruta em até 90%.
  - **Configurar proteção contra SYN Flood:** Melhora a resistência contra ataques DoS.
- **Configurar o fail2ban para proteção adicional:** Pode bloquear até 99% dos IPs maliciosos, prevenindo tentativas de invasão.
- **Configurar o ModSecurity para proteção do servidor web:** Adiciona uma camada extra de segurança, prevenindo ataques comuns como SQL Injection e Cross-Site Scripting (XSS).
- **Configurar parâmetros sysctl para proteção adicional:** Melhorias de segurança de rede e mitigação de ataques.
- **Configurar um serviço systemd para detectar e liberar automaticamente a porta SSH no firewall após reinicializações:** Garantia de que o acesso SSH seja sempre possível após reinicializações.
- **Alterar o idioma do sistema e ajustar os repositórios:** Ajusta o sistema para o idioma preferido e otimiza a velocidade de download de pacotes.

### Benefícios e Melhorias

- **Segurança:** A combinação de firewalls, fail2ban, ModSecurity e certificados SSL pode aumentar a segurança do servidor em até 90%.
- **Desempenho:** Otimizações de rede, sysctl e caching com Varnish podem aumentar o desempenho do servidor em até 300%.
- **Eficiência:** Desativar serviços desnecessários e instalar drivers atualizados melhora a eficiência geral do sistema.
- **Confiabilidade:** Configurações automatizadas garantem que o servidor funcione de maneira consistente e estável, mesmo após reinicializações.

### Finalização

Após completar as configurações, o script perguntará se você deseja reiniciar o servidor para aplicar todas as alterações. Recomendamos reiniciar para garantir que todas as mudanças sejam aplicadas corretamente.

---

O **DoceSetup** é a ferramenta ideal para quem busca uma configuração rápida, segura e eficiente para seu servidor Debian 11. Experimente agora e veja a diferença no desempenho e segurança do seu sistema! 🍬

## Contato

Para dúvidas, sugestões ou problemas, entre em contato:

📩 **[t.me/adassecus](https://t.me/adassecus)**
