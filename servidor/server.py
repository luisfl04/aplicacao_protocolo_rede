import socket
import threading
import struct
import zlib
from utils.package import Package
from decouple import config


class Server:
    HEADER_FORMAT = config("HEADER_FORMAT")
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
    FLAG_SYN = config("FLAG_SYN")
    FLAG_ACK = config("FLAG_ACK")
    FLAG_CHECKSUM = config("FLAG_CHECKSUM")
    SERVER_ADDRESS = config("SERVER_ADDRESS")
    SERVER_PORT = int(config("SERVER_PORT"))
    clients_state = {} # Armazenará o estado dos clientes conectados
    clients_lock = threading.Lock() # 'Trava' para gerenciar o acesso ao dicionário 'clients_state'
    

    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print(f"adrees -> {self.SERVER_ADDRESS}") 
        self.start_server()

    def handle_packet(self, raw_data, client_address, server_socket):
        """
        Função executada por um processo isolado a cada pacote recebido de um cliente
        """

        print(
            f"Thread name: {threading.current_thread().name}\n" +
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
            checksum_calculated = zlib.crc32(header_for_check + package_sended.data) & 0xffff

            # Validando checksum:
            if checksum_calculated != package.checksum:
                print(f"[ERRO] Checksum inválido de {client_address}. Pacote descartado.")
                return
            
            print(f"[PACOTE RECEBIDO] -> {package_sended}")

        except Exception as e:
            print(f"[ERRO] Erro ao desempacotar pacote de {client_address}: {e}")
            return

        # Lógica de confirmação de recebimento de pacotes:
        with self.clients_lock:
            try:
                # Verificando se é um cliente novo
                if client_address not in self.clients_state:
                    if package_sended.flags & self.FLAG_SYN:
                        print(f"[CONEXÃO] Iniciando conexão para um novo cliente...\n IP:{client_address}")

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
        # 2. Vincular (Bind) o socket ao nosso endereço e porta
        try:
            self.server_socket.bind((self.SERVER_ADDRESS, self.SERVER_PORT))
            print(f"✅ Servidor UDP escutando em {self.SERVER_ADDRESS}:{self.SERVER_PORT}")
        except OSError as e:
            print(f"❌ Falha ao vincular socket: {e}. A porta já está em uso?")
            return

        # 3. Loop Principal (Apenas escuta)
        try:
            while True:
                # Espera pelo envio de um pacote:
                raw_data, client_address = self.server_socket.recvfrom(1024) 
                
                # Inicia o processo para lidar com o pcaote recebido:
                worker_thread = threading.Thread(
                    target=self.handle_packet, 
                    args=(raw_data, client_address, self.server_socket)
                )
                worker_thread.start() # Inicia a thread
                
        except KeyboardInterrupt:
            print("\n🚫 Servidor sendo desligado (Ctrl+C).")
        finally:
            self.server_socket.close()
            print("Socket do servidor fechado.")

if __name__ == "__main__":
    Server()