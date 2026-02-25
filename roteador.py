# -*- coding: utf-8 -*-

import csv
import json
import threading
import time
from argparse import ArgumentParser

import requests
from flask import Flask, jsonify, request

class Router:
    """
    Representa um roteador que executa o algoritmo de Vetor de Distância.
    """

    def __init__(self, my_address, neighbors, my_network, update_interval=1):
        """
        Inicializa o roteador.

        :param my_address: O endereço (ip:porta) deste roteador.
        :param neighbors: Um dicionário contendo os vizinhos diretos e o custo do link.
                          Ex: {'127.0.0.1:5001': 5, '127.0.0.1:5002': 10}
        :param my_network: A rede que este roteador administra diretamente.
                           Ex: '10.0.1.0/24'
        :param update_interval: O intervalo em segundos para enviar atualizações, o tempo que o roteador espera 
                                antes de enviar atualizações para os vizinhos.        """
        self.my_address = my_address
        self.neighbors = neighbors
        self.my_network = my_network
        self.update_interval = update_interval

        # TODO: Este é o local para criar e inicializar sua tabela de roteamento.
        #
        # 1. Crie a estrutura de dados para a tabela de roteamento. Um dicionário é
        #    uma ótima escolha, onde as chaves são as redes de destino (ex: '10.0.1.0/24')
        #    e os valores são outro dicionário contendo 'cost' e 'next_hop'.
        #    Ex: {'10.0.1.0/24': {'cost': 0, 'next_hop': '10.0.1.0/24'}}
        #
        # 2. Adicione a rota para a rede que este roteador administra diretamente
        #    (a rede em 'self.my_network'). O custo para uma rede diretamente
        #    conectada é 0, e o 'next_hop' pode ser a própria rede ou o endereço do roteador.
        #
        # 3. Adicione as rotas para seus vizinhos diretos, usando o dicionário
        #    'self.neighbors'. Para cada vizinho, o 'cost' é o custo do link direto
        #    e o 'next_hop' é o endereço do próprio vizinho.
        self.routing_table = {}
        self.routing_table[self.my_network] = {
            'cost': 0,
            'next_hop': self.my_address
        }
        
        for neighbor, cost in self.neighbors.items():
            self.routing_table[neighbor] = {
                'cost': cost,
                'next_hop': neighbor
            }

        print("Tabela de roteamento inicial:")
        print(json.dumps(self.routing_table, indent=4))

        # Inicia o processo de atualização periódica em uma thread separada
        self._start_periodic_updates()

    def ip_to_int(self, ip):
        a, b, c, d = map(int, ip.split("."))
        return (a << 24) | (b << 16) | (c << 8) | d


    def int_to_ip(self, value):
        return ".".join([
            str((value >> 24) & 255),
            str((value >> 16) & 255),
            str((value >> 8) & 255),
            str(value & 255)
        ])


    def split_network(self, network):
        ip, prefix = network.split("/")
        return ip, int(prefix)


    def try_aggregate(self, net1, net2, info1, info2):

        if info1["next_hop"] != info2["next_hop"]:
            return None

        ip1, p1 = self.split_network(net1)
        ip2, p2 = self.split_network(net2)

        if p1 != p2:
            return None

        int1 = self.ip_to_int(ip1)
        int2 = self.ip_to_int(ip2)

        if int1 > int2:
            int1, int2 = int2, int1

        size = 1 << (32 - p1)

        if abs(int1 - int2) != size:
            return None

        new_prefix = p1 - 1
        mask = (~0 << (32 - new_prefix)) & 0xFFFFFFFF

        new_net_int = int1 & mask
        if (int1 & mask) != new_net_int or (int2 & mask) != new_net_int:
            return None
        new_network = f"{self.int_to_ip(new_net_int)}/{new_prefix}"

        new_cost = max(info1["cost"], info2["cost"])

        return new_network, new_cost, info1["next_hop"]

    def _start_periodic_updates(self):
        """Inicia uma thread para enviar atualizações periodicamente."""
        thread = threading.Thread(target=self._periodic_update_loop)
        thread.daemon = True
        thread.start()

    def _periodic_update_loop(self):
        """Loop que envia atualizações de roteamento em intervalos regulares."""
        while True:
            time.sleep(self.update_interval)
            print(f"[{time.ctime()}] Enviando atualizações periódicas para os vizinhos...")
            try:
                self.send_updates_to_neighbors()
            except Exception as e:
                print(f"Erro durante a atualização periódida: {e}")

    #Optei por deixar a lógica para a sumarização para redes não contiguas separada
    def summarize_table(self, table): 
        tabela = dict(table)
        mudou = True 

        while mudou: 
            mudou = False 
            
            grupos ={}
            for rede, info in tabela.items(): 
                if "/" not in rede: continue 

                next_hop = info["next_hop"]
                grupos.setdefault(next_hop, []).append((rede, info))

            for next_hop, redes_info in grupos.items():
                redes_info.sort(key=lambda x: self.ip_to_int(self.split_network(x[0])[0]))
                i = 0
                while i < len(redes_info) - 1:
                    net1, info1 = redes_info[i]
                    net2, info2 = redes_info[i + 1]

                    resultado = self.try_aggregate(net1, net2, info1, info2)

                    if resultado:
                        nova_rede, novo_custo, _ = resultado

                        _, prefix = self.split_network(nova_rede)
                        if prefix < 8:
                            i += 1
                            continue

                        del tabela[net1]
                        del tabela[net2]

                        tabela[nova_rede] = {
                            "cost": novo_custo,
                            "next_hop": next_hop
                        }

                        mudou = True
                        break
                    else:
                        i += 1

                if mudou:
                    break

        return tabela
        #     for i in range(len(redes)):
        #         for j in range(i + 1, len(redes)):
        #             net1 = redes[i]
        #             net2 = redes[j]
                
        #             if net1 not in tabela or net2 not in tabela: continue 

        #             if "/" not in net1 or "/" not in net2: continue 

        #             info1 = tabela[net1]
        #             info2 = tabela[net2]

        #             resultado = self.try_aggregate(net1, net2, info1, info2)

        #             if resultado: 
        #                 nova_rede, novo_custo, next_hop = resultado 

        #                 _, prefix = self.split_network(nova_rede)
        #                 if prefix < 8: continue 

        #                 del tabela[net1]
        #                 del tabela[net2]

        #                 tabela[nova_rede] = {
        #                     "cost": novo_custo,
        #                     "next_hop": next_hop
        #                 }

        #                 mudou = True 
        #                 break 
        #         if mudou: break 
        # return tabela

    def send_updates_to_neighbors(self):
        """
        Envia a tabela de roteamento (potencialmente sumarizada) para todos os vizinhos.
        """
        # TODO: O código abaixo envia a tabela de roteamento *diretamente*.
        #
        # ESTE TRECHO DEVE SER CHAMAADO APOS A SUMARIZAÇÃO.
        #
        # dica:
        # 1. CRIE UMA CÓPIA da `self.routing_table` NÃO ALTERE ESTA VALOR.
        # 2. IMPLEMENTE A LÓGICA DE SUMARIZAÇÃO nesta cópia.
        # 3. ENVIE A CÓPIA SUMARIZADA no payload, em vez da tabela original.
        
        tabela_para_enviar = dict(self.routing_table)

        tabela_para_enviar = self.summarize_table(tabela_para_enviar)

        for neighbor_address in self.neighbors:

            tabela_filtrada = {}

            for network, info in tabela_para_enviar.items():
                if info["next_hop"] == neighbor_address:
                    continue
                tabela_filtrada[network] = info

            payload = {
                "sender_address": self.my_address,
                "routing_table": tabela_filtrada
            }

            url = f'http://{neighbor_address}/receive_update'

            try:
                print(f"Enviando tabela para {neighbor_address}")
                requests.post(url, json=payload, timeout=5)
            except requests.exceptions.RequestException as e:
                print(f"Não foi possível conectar ao vizinho {neighbor_address}. Erro: {e}")

# --- API Endpoints ---
# Instância do Flask e do Roteador (serão inicializadas no main)
app = Flask(__name__)
router_instance = None

@app.route('/routes', methods=['GET'])
def get_routes():
    """Endpoint para visualizar a tabela de roteamento atual."""
    # TODO: Aluno! Este endpoint está parcialmente implementado para ajudar na depuração.
    # Você pode mantê-lo como está ou customizá-lo se desejar.
    # - mantenha o routing_table como parte da resposta JSON.
    if router_instance:
        return jsonify({
            "vizinhos" : router_instance.neighbors,
            "my_network": router_instance.my_network,
            "my_address": router_instance.my_address,
            "update_interval": router_instance.update_interval,
            "routing_table": router_instance.routing_table # Exibe a tabela de roteamento atual (a ser implementada)
        }), 200
    return jsonify({"error": "Roteador não inicializado"}), 500

@app.route('/receive_update', methods=['POST'])
def receive_update():
    """Endpoint que recebe atualizações de roteamento de um vizinho."""
    if not request.json:
        return jsonify({"error": "Invalid request"}), 400

    update_data = request.json
    sender_address = update_data.get("sender_address")
    sender_table = update_data.get("routing_table")

    if not sender_address or not isinstance(sender_table, dict):
        return jsonify({"error": "Missing sender_address or routing_table"}), 400

    print(f"Recebida atualização de {sender_address}:")
    print(json.dumps(sender_table, indent=4))

    # TODO: Implemente a lógica de Bellman-Ford aqui.
    #
    # 1. Verifique se o remetente é um vizinho conhecido.

    if sender_address not in router_instance.neighbors:
        return jsonify({"status": "ignored"}), 200 

    # 2. Obtenha o custo do link direto para este vizinho a partir de `router_instance.neighbors`.
    direct_cost = router_instance.neighbors[sender_address]
    tabela_alterada = False 

    # 3. Itere sobre cada rota (`network`, `info`) na `sender_table` recebida.
    for network, info in sender_table.items(): 

        if network == router_instance.my_network:
            continue 

        neighbor_cost = info.get("cost")
        if neighbor_cost is None: 
            continue
        
    # 4. Calcule o novo custo para chegar à `network`:
    #    novo_custo = custo_do_link_direto + info['cost']
        novo_custo = direct_cost + neighbor_cost

    # 5. Verifique sua própria tabela de roteamento:
    #    a. Se você não conhece a `network`, adicione-a à sua tabela com o
    #       `novo_custo` e o `next_hop` sendo o `sender_address`.
    #    b. Se você já conhece a `network`, verifique se o `novo_custo` é menor
    #       que o custo que você já tem. Se for, atualize sua tabela com o
    #       novo custo e o novo `next_hop`.
    #    c. (Opcional, mas importante para robustez): Se o `next_hop` para uma rota
    #       for o `sender_address`, você deve sempre atualizar o custo, mesmo que
    #       seja maior (isso ajuda a propagar notícias de links quebrados).
    #
        if network not in router_instance.routing_table:
            router_instance.routing_table[network] = {
                "cost": novo_custo,
                "next_hop": sender_address
            }
            tabela_alterada = True

        else: 
            custo_atual = router_instance.routing_table[network]["cost"]
            next_hop_atual = router_instance.routing_table[network]["next_hop"]

            if novo_custo < custo_atual: 
                router_instance.routing_table[network] = {
                    "cost": novo_custo,
                    "next_hop": sender_address
                }
                tabela_alterada = True 

            elif next_hop_atual == sender_address: 
                router_instance.routing_table[network]["cost"] = novo_custo
                tabela_alterada = True

    # 6. Mantenha um registro se sua tabela mudou ou não. Se mudou, talvez seja
    #    uma boa ideia imprimir a nova tabela no console.
    if tabela_alterada: 
        print("Tabela de roteamento atualizada")
        print(json.dumps(router_instance.routing_table, indent=4))

    return jsonify({"status": "success", "message": "Update received"}), 200

if __name__ == '__main__':
    parser = ArgumentParser(description="Simulador de Roteador com Vetor de Distância")
    parser.add_argument('-p', '--port', type=int, default=5000, help="Porta para executar o roteador.")
    parser.add_argument('-f', '--file', type=str, required=True, help="Arquivo CSV de configuração de vizinhos.")
    parser.add_argument('--network', type=str, required=True, help="Rede administrada por este roteador (ex: 10.0.1.0/24).")
    parser.add_argument('--interval', type=int, default=10, help="Intervalo de atualização periódica em segundos.")
    args = parser.parse_args()

    # Leitura do arquivo de configuração de vizinhos
    neighbors_config = {}
    try:
        with open(args.file, mode='r') as infile:
            reader = csv.DictReader(infile)
            for row in reader:
                neighbors_config[row['vizinho']] = int(row['custo'])
    except FileNotFoundError:
        print(f"Erro: Arquivo de configuração '{args.file}' não encontrado.")
        exit(1)
    except (KeyError, ValueError) as e:
        print(f"Erro no formato do arquivo CSV: {e}. Verifique as colunas 'vizinho' e 'custo'.")
        exit(1)

    my_full_address = f"127.0.0.1:{args.port}"
    print("--- Iniciando Roteador ---")
    print(f"Endereço: {my_full_address}")
    print(f"Rede Local: {args.network}")
    print(f"Vizinhos Diretos: {neighbors_config}")
    print(f"Intervalo de Atualização: {args.interval}s")
    print("--------------------------")

    router_instance = Router(
        my_address=my_full_address,
        neighbors=neighbors_config,
        my_network=args.network,
        update_interval=args.interval
    )

    # Inicia o servidor Flask
    app.run(host='0.0.0.0', port=args.port, debug=False)