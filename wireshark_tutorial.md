# Relatório de Análise de Tráfego de Rede com Wireshark

Este documento descreve como instalar o Wireshark e, principalmente, **como utilizá-lo para analisar um arquivo de captura de tráfego (`.pcap`)**. 

## 1. Instalação do Wireshark

Para analisar o arquivo de captura, você precisará do Wireshark instalado em seu computador. O Tshark (linha de comando) não é estritamente necessário para esta análise baseada na interface gráfica, mas é instalado junto.

### 1.1. Windows

1.  **Download:** Acesse o site oficial [www.wireshark.org](https://www.wireshark.org/) e baixe o instalador para Windows.
2.  **Instalação:** Execute o instalador. Siga as instruções, garantindo que o **Npcap** (driver de captura, necessário mesmo que não vá capturar agora) seja instalado quando solicitado.

### 1.2. Linux (Debian/Ubuntu)

1.  **Abra o Terminal.**
2.  **Atualize os Pacotes:**
    ```bash
    sudo apt update
    ```
3.  **Instale o Wireshark:**
    ```bash
    sudo apt install wireshark
    ```
4.  **Permissões (Opcional, mas recomendado para futuras capturas):** Durante a instalação, se perguntado se usuários não-root devem poder capturar pacotes, selecione **"Sim"**. Adicione seu usuário ao grupo `wireshark`:
    ```bash
    sudo usermod -aG wireshark $USER
    ```
    Lembre-se de fazer **logout e login novamente** para a mudança de grupo ter efeito.

---


## 2. Captura de Tráfego

Agora, capture o tráfego gerado pela seu conjunto de roteador.

> **⚠️ ATENÇÃO:** Arquivos de captura (`.pcap`, `.pcapng`) podem conter dados sensíveis. Manuseie-os com cuidado, armazene-os de forma segura e descarte-os adequadamente após a análise. Não compartilhe capturas brutas publicamente se houver risco de exposição de dados.

> **⚠️ ATENÇÃO:** Essa etapa (apenas a captura) deve ser realizada em casa (ou em um equipamento de uso pessoal), e não do laboratorio (LCC), em razão do risco de segurança de capturar o trafego nas maquinas do laboratorio.


**Passos:**

1.  **Identifique a Interface Correta:** Antes de capturar, descubra qual interface de rede será usada para a comunicação entre seu cliente e servidor.
    *   Se cliente e servidor rodam na **mesma máquina**, a interface provavelmente será a de **Loopback** (nome pode variar: `lo`, `lo0`, `Loopback Pseudo-Interface 1`).
    *   Se rodam em **máquinas diferentes** na mesma rede local, será sua interface de rede principal (Wi-Fi ou Ethernet).
    *   Use o comando `tshark -D` (ou veja na tela inicial do Wireshark) para listar as interfaces e seus números/nomes.
    ```bash
    # Exemplo no Linux
    tshark -D

    # Exemplo no Windows (Prompt ou PowerShell)
    tshark -D
    ```

2.  **Inicie a Captura (usando Tshark):** Abra um terminal ou prompt de comando (pode precisar de `sudo` no Linux ou "Executar como Administrador" no Windows para capturar em interfaces reais, mas geralmente não para loopback).
    ```bash
    # Exemplo Captura (substitua <interface> pelo nome ou número correto)
    # Salvar no arquivo 'captura_roteador.pcapng'
    sudo tshark -i <interface> -w captura_roteador.pcapng
    ```
    *   **Alternativa:** Você pode usar a interface gráfica do Wireshark. Selecione a interface correta e clique no botão azul de "Start" (barbatana de tubarão).

3.  **Execute o cenário:**
    *   Execute seus **roteadores**.


4.  **Pare a Captura:**
    *   Se estiver usando `tshark` no terminal, volte para ele e pressione `Ctrl + C`.
    *   Se estiver usando a interface gráfica do Wireshark, clique no botão vermelho "Stop".

5.  **Salve o Arquivo (se usando Wireshark GUI):** Se usou a interface gráfica, vá em `File -> Save As...` e salve a captura com um nome descritivo (ex: `ftcp_capture.pcap`). 

O arquivo `.pcap` gerado contém agora os pacotes trocados durante a execução do seu protocolo FTCP e está pronto para a análise detalhada na próxima seção.


## 3. Tutorial: Análise Básica com Wireshark (Usando o Arquivo Fornecido)

Nesta seção, vamos aprender os fundamentos do Wireshark analisando tráfegos DHCP e DNS presentes no arquivo de captura fornecido.

**Arquivo de Captura:** Baixe o arquivo `.pcap` necessário para esta análise disponiveis nesse repositorio, 
[pcap/exemplos](pcaps/exemplos/) 

**Passos Iniciais:**

1.  **Abra o Wireshark:** Inicie a aplicação Wireshark.
2.  **Abra o Arquivo de Captura:** Vá ao menu `File -> Open...` (ou `Arquivo -> Abrir...`) e selecione o arquivo `.pcap` que você baixou.
3.  **Interface Principal:** Familiarize-se com as três áreas principais da interface do Wireshark, conforme ilustrado na imagem abaixo:
    *   **A) Painel de Lista de Pacotes:** Mostra um resumo de cada pacote capturado (número, tempo, origem, destino, protocolo, informações básicas).
    *   **B) Painel de Detalhes do Pacote:** Exibe as informações decodificadas do pacote selecionado na lista, organizadas por camadas (Frame, Ethernet, IP, TCP/UDP, Protocolo de Aplicação). Você pode expandir/recolher cada camada clicando nas setas.
    *   **C) Painel de Bytes do Pacote:** Mostra o conteúdo bruto do pacote selecionado em hexadecimal e ASCII.

    ![Interface Principal do Wireshark](img/dhcp.png) 


4.  **Filtros de Exibição:** A barra de filtro (geralmente acima do Painel de Lista de Pacotes) é uma das ferramentas mais poderosas. Ela permite que você mostre apenas os pacotes que correspondem a um critério específico (sem modificar o arquivo original). Digite sua expressão de filtro e pressione Enter para aplicá-la. Para limpar o filtro, clique no 'X' à direita da barra.

**Análise Guiada (DHCP e HTTP):**

### 3.1 Análise HTTP (Obtenção de Endereço IP)

Os nossos roteadores estão utilizando protocolos das camadas superiores (para viabilizar o laboratorio). Especificamente, o protocolo de aplicação `http`. E por isso vamos observar as menssagem dos nossos roteadoers dentro desse protocolo. Nesse repositorio, você pode acessar um exemplo de trafego [http](./pcaps/socks-http-example.pcap) na pasta [pcaps](./pcaps/) desse repositotio.

1.  **Aplique o Filtro:** No campo de filtro de exibição, digite `http` e pressione Enter. (DHCP usa a mesma base do protocolo BOOTP, por isso este filtro funciona).
2.  **Observe os Pacotes:** observe as menssagem https trocadas.

  ![Interface Principal do Wireshark](img/http.png)

**Análise Guiada (DHCP e DNS):**

### 3.1 Análise DHCP (Obtenção de Endereço IP)

Como visto o protocolo DHCP (Dynamic Host Configuration Protocol) é usado para que um dispositivo obtenha automaticamente um endereço IP e outras configurações de rede. Abra o um exemplo de trafego [dhcp](./pcaps/dhcp.pcap) na pasta [pcaps](./pcaps/) desse repositotio.

1.  **Aplique o Filtro:** No campo de filtro de exibição, digite `bootp` e pressione Enter. (DHCP usa a mesma base do protocolo BOOTP, por isso este filtro funciona).
2.  **Observe os Pacotes:** Você deverá ver uma sequência de pacotes DHCP. As quatro mensagens principais são: **Discover**, **Offer**, **Request**, e **ACK** (ou Acknowledgment). Veja como eles aparecem na coluna "Info" do Painel de Lista de Pacotes.

  ![Interface Principal do Wireshark](img/dhcp.png) 

3.  **Examine os Detalhes:**
    *   **Selecione** um pacote **DHCP Offer**. No Painel de Detalhes (B), expanda a seção "Bootstrap Protocol" ou "Dynamic Host Configuration Protocol". Procure por informações como o endereço IP oferecido ("Your (client) IP address" ou opções específicas).
    *   **Selecione** um pacote **DHCP ACK**. Examine os detalhes da mesma forma. Confirme o endereço IP final atribuído e outras opções (como máscara de sub-rede, gateway, servidor DNS) se estiverem presentes.
    *   Note as portas UDP usadas (geralmente 67 para o servidor e 68 para o cliente) na seção "User Datagram Protocol".

---

## 4. Materiais de Apoio Adicionais

Para aprofundar seus conhecimentos em Wireshark:

*   **Guia Oficial do Usuário:** [Wireshark User's Guide](https://www.wireshark.org/docs/wsug_html_chunked/)
*   **Wiki do Wireshark (Filtros):** [wiki.wireshark.org/DisplayFilters](https://wiki.wireshark.org/DisplayFilters)
* **[What is a PCAP file? ](https://www.endace.com/learn/what-is-a-pcap-file)**
*   **Vídeos Tutoriais:** Busque no YouTube por "Wireshark tutorial", "Wireshark display filters", "Wireshark TCP analysis".
    *  [Tutorial Wireshark para Iniciantes (YouTube)](https://www.youtube.com/watch?v=4rQ3evV600Y)
