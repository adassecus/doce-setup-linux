# 🍬 DoceSetup 2.0

O DoceSetup é um script de configuração simplificado para seu servidor Linux.

## Funcionalidades

- **Acesso Root SSH**: Configure acesso SSH para o usuário root e defina uma senha
- **Timeout SSH**: Desative o timeout do SSH para sessões longas (5 horas)
- **Memória Swap**: Crie e configure memória swap com diferentes opções de tamanho
- **Arquitetura 32 bits**: Ative suporte a aplicativos de 32 bits no seu sistema
- **Certificado SSL**: Configure certificados SSL gratuitos (com domínio ou autossignados)
- **Serviços Desnecessários**: Desative serviços não utilizados para liberar recursos

## Requisitos

- Qualquer distribuição Linux recente (Debian, Ubuntu, Fedora, CentOS, Arch, etc.)
- Privilégios de root (sudo)
- Python 3.6 ou superior

## Instalação e Uso

### 1) Baixe o script:

```bash
wget -O docesetup.py https://raw.githubusercontent.com/adassecus/doce-setup-linux/main/docesetup.py
```

### 2) Torne o script executável:

```bash
chmod +x docesetup.py
```

### 3) Execute o script como root:

```bash
sudo python3 docesetup.py
```

## Interface

Na primeira execução, o script tentará instalar a biblioteca Python `rich` para fornecer a interface.

Se preferir, você pode instalar manualmente a biblioteca `rich` antes de executar o script:

```bash
pip install rich tqdm
```

## Tutorial Rápido

1. Execute o script como root
2. Selecione a opção desejada no menu principal
3. Siga as instruções na tela para cada configuração
4. Para aplicar todas as configurações de uma vez, selecione a opção "Executar Todas as Configurações"
5. Reinicie o sistema quando solicitado para aplicar todas as alterações

## Distribuições Suportadas

- **Debian/Ubuntu**: Debian, Ubuntu, Linux Mint, Pop!_OS, Elementary OS, Zorin OS
- **RHEL/Fedora**: Fedora, CentOS, RHEL, Rocky Linux, AlmaLinux
- **Arch Linux**: Arch, Manjaro, EndeavourOS
- **SUSE**: openSUSE, SUSE Linux Enterprise
- **Outras distribuições baseadas em pacotes DEB, RPM ou PAC**

## Segurança

O DoceSetup segue boas práticas de segurança:
- Todos os scripts são executados localmente em seu sistema
- Código-fonte aberto e auditável
- Sem conexões externas para além das necessárias para instalação de pacotes
- Certificados SSL configuram-se de acordo com os padrões de segurança

## Contato e Suporte

Para dúvidas, sugestões ou problemas, entre em contato:

📩 **[t.me/adassecus](https://t.me/adassecus)**
