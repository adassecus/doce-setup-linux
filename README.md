## DoceSetup 🍬

Bem-vindo ao **DoceSetup**, o seu assistente amigável e eficiente para configurar servidores Linux! Este script foi projetado para facilitar a configuração inicial do servidor, automatizando tarefas comuns e essenciais. Siga os passos abaixo para instalar e usar o DoceSetup.

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
  wget -O doce_setup.sh https://raw.githubusercontent.com/uouwm/doce-setup-linux/main/doce_setup.sh
  ```

### Passo 3: Dar Permissão

Dê permissão ao script baixado:
```bash
chmod 777 doce_setup.sh
```

### Passo 4: Executar o Script

Execute o script com permissões de superusuário:
```bash
sudo ./doce_setup.sh
```

### Passo 5: Seguir as Instruções Interativas

O DoceSetup guiará você através de uma série de perguntas interativas para configurar o servidor. As opções incluem:

- Alterar a senha do root
- Configurar o SSH (porta e timeout)
- Criar memória swap
- Otimizar o adaptador de rede
- Ativar a arquitetura 32 bits
- Instalar o Apache (necessário para MariaDB e phpMyAdmin)
- Instalar o MariaDB
- Instalar o phpMyAdmin
- Alterar o idioma do sistema e ajustar os repositórios

### Finalização

Após completar as configurações, o script perguntará se você deseja reiniciar o servidor para aplicar todas as alterações. Recomendamos reiniciar para garantir que todas as mudanças sejam aplicadas corretamente.
