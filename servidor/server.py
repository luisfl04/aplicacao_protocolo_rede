import socket
import threading
import struct
import zlib
from utils.package import Package
from decouple import config


class Server:
    HEADER_FORMAT = config("HEADER_FORMAT")
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
    FLAG_SYN = 1 << 0
    FLAG_ACK = 1 << 1
    FLAG_CHECKSUM = 1 << 2
    SERVER_ADDRESS = config("SERVER_ADDRESS")
    SERVER_PORT = int(config("SERVER_PORT"))
    clients_state = {} # Armazenará o estado dos clientes conectados
    clients_lock = threading.Lock() # 'Trava' para gerenciar o acesso ao dicionário 'clients_state'
    

    def __init__(self):
        self.start_menu()

    def start_menu(self):
        try:
            escolha_menu = None
            mensagem_menu = """
              ---------------------------------------- MENU SERVIDOR UDP ----------------------------------------
              - Escolha uma das opções abaixo:
              1 - Entrar em modo de escuta(Permitir recebimento de pacotes)
              2 - Exibir clientes conectados   
              0 - Fechar servidor 
            """

            while escolha_menu != 0:
                print(mensagem_menu)
                escolha_menu = int(input("Digite sua escolha -> "))
                validacao = self.validar_entrada_usuario(entrada=escolha_menu)
               
                while not validacao:
                    print("\nEntrada inválida. Digite novamente uma opção correta.")
                    escolha_menu = int(input("Digite aqui -> "))
                    validacao = self.validar_entrada_usuario(entrada=escolha_menu)

                match escolha_menu:
                    case 1:
                        self.start_server()
                    case 2:
                        self.exibir_clientes_conectados()
                    case 0:
                        self.fechar_conexao()
                        break                        
        except Exception as e:
            pass

    def exibir_clientes_conectados(self):
        if self.clients_state == {}:
            print("\n--------------------------------------\nNão há clientes conectados\n--------------------------------------")


    def fechar_conexao(self):
        print("Encerrando servidor...")
        self.server_socket.close()

    def validar_entrada_usuario(self, entrada) -> bool:
        try:
            if type(entrada) != int:
                return False
            elif entrada < 0 or entrada > 2:
                return False
            return True
        
        except Exception as e:
            print(f"Exceção ao validar a entrada do usuário\nlog: {e}")
            return False


    def handle_packet(self, raw_data, client_address):
        """
        Função executada por um processo isolado a cada pacote recebido de um cliente
        """

        print(
            f"Pacote Recebido!\n" +
            f"Tamanho do pacote recebido: {len(raw_data)}\n" + 
            f"Endereço IP do cliente: {client_address}"
        )

        # Manipulando pacote recebido e calculando checksum:
        try:
            # desempacotando:
            package = Package()
            package_sended = package.unpack_package(raw_data)
            
            # Obtendo um checksum para validação:
            header_for_check = struct.pack('!IIHH', package_sended.sequence_number, package_sended.ack_number, package_sended.flags, 0)
            checksum_calculated = zlib.crc32(header_for_check + package_sended.data) &0xffff 

            # Validando checksum:
            if checksum_calculated != package_sended.checksum:
                print(f"[ERRO] Checksum inválido de {client_address}. Pacote descartado.")
                return
            
        except Exception as e:
            print(f"[ERRO] Erro ao desempacotar pacote de {client_address}: {e}")
            return

        # Lógica de confirmação de recebimento de pacotes:
        with self.clients_lock:
            try:
                # Verificando se é um cliente novo
                if client_address not in self.clients_state:
                    if package_sended.flags & self.FLAG_SYN:
                        print(f"[CONEXÃO] Iniciando conexão para um novo cliente...\n IP:{str(client_address)}")

                        # Inicializa o estado para este novo cliente:
                        self.clients_state[client_address] = {
                            'expected_number_sequence': package_sended.sequence_number + 1,
                            'state': 'CONNECTED' ,
                            'last_ack_sended': package_sended.ack_number
                        }

                        # Preparando pacote de confirmação para envio:
                        ack_package = Package(sequence_number=0, 
                                        ack_number=package_sended.sequence_number + 1,
                                        flags=(self.FLAG_SYN | self.FLAG_ACK), data=b"Pacote de confirmacao")
                        
                        self.server_socket.sendto(ack_package.pack_package(), client_address)
                        print(f"[RESPOSTA] Enviando SYN-ACK para {client_address}")
                        return
                    else:
                        # Pacote não-SYN de um cliente desconhecido. Descartar.
                        print(f"[AVISO] Pacote de {client_address} (desconhecido) sem flag de sincronização. Descartado.")
                        return
                
                else:
                    client = self.clients_state[client_address]

                    # Verificando número de sequência do pacote:
                    if package_sended.sequence_number != client['expected_number_sequence']:
                        print(f"[EERO] Pacote do cliente {client_address} enviado fora de sequência. Pacote descartado.")
                        return

                    ack_package = Package(sequence_number=client['last_ack_sended'] + 1, 
                                        ack_num=package.sequence_number + 1,
                                        flags=(self.FLAG_SYN | self.FLAG_ACK),
                                        data=b"Pacote de confirmacao"
                                        )
                    
                    print(f"[RESPOSTA] Enviando SYN-ACK para {client_address}")
                    self.server_socket.sendto(ack_package.pack_package(), client_address)
                    print("ACK enviado, processo finalizado.")
                    return
            except Exception as e:
                print(f"[ERRO] Exceção ao confirmar o envio de pacote do cliente {client_address}\nLog: {e}")

    def start_server(self):
        """
        Função principal que inicia o servidor (Thread Principal).
        """        
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.server_socket.bind((self.SERVER_ADDRESS, self.SERVER_PORT))
            print(f"\n---------------------------------------\nServidor UDP iniciado!\nEscutando em {self.SERVER_ADDRESS}:{self.SERVER_PORT}")
        except OSError as e:
            print(f"Falha ao vincular socket do servidor: {e}")
            return

        try:
            while True:
                print("Pronto para receber pacotes...")
                raw_data, client_address = self.server_socket.recvfrom(1024)                
                worker_thread = threading.Thread(
                    target=self.handle_packet, 
                    args=(raw_data, client_address)
                )
                worker_thread.start()
                
        except KeyboardInterrupt:
            print("\n🚫 Servidor sendo desligado (Ctrl+C).")

if __name__ == "__main__":
    Server()