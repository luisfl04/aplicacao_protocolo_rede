import socket
import struct
import zlib
import time
from utils.package import Package
from decouple import config


class Client:
    
    # Configurações utilizadas pelo cliente:
    SERVER_ADDRESS = config("SERVER_ADDRESS")
    SERVER_PORT = int(config("SERVER_PORT"))
    SERVER_ADDRESS_COMPLETE = (SERVER_ADDRESS, SERVER_PORT)
    CLIENT_TIMEOUT = 5.0 
    FLAG_SYN = 1 << 0
    FLAG_ACK = 1 << 1
    FLAG_CHECKSUM = 1 << 2
    HEADER_FORMAT = config("HEADER_FORMAT")

    def __init__(self):
        # Iniciando cliente:
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_socket.settimeout(self.CLIENT_TIMEOUT) 
        self.start_client()


    def start_client(self):
        """
        Função principal do cliente, iniciando conexão com o servidor.
        """
        
        print(f"✅ Cliente iniciado. Tentando conectar com {self.SERVER_ADDRESS_COMPLETE}")
        
        try:  
            # Criamos um pacote com a flag SYN e um número de sequência inicial (ex: 1)
            # Em um protocolo real, o número de sequência seria aleatório.
            initial_seq = 1
            syn_packet = Package(sequence_number=initial_seq, flags=self.FLAG_SYN, data=b"Requisicao")
            raw_syn_bytes = syn_packet.pack_package()
            
            print(f"\n[ENVIO] Enviando SYN (SEQ={syn_packet.sequence_number}) para o servidor...")
        
            # Envia os bytes crus para o endereço do servidor
            self.client_socket.sendto(raw_syn_bytes, self.SERVER_ADDRESS_COMPLETE)
            
            # --- 3. Aguardar e Receber Resposta (SYN-ACK) ---
            print(f"[ESPERA] Aguardando SYN-ACK do servidor (Timeout: {self.CLIENT_TIMEOUT}s)...")
            
            # Esta chamada é BLOQUEANTE e espera até que o pacote chegue ou o timeout ocorra
            raw_response, server_address_received = self.client_socket.recvfrom(1024) 
            
            # --- 4. Processar Resposta ---
            result_package = Package()
            response_pkt = result_package.unpack_package(raw_response)
            
            # Verificação do Checksum (Reutilizando a lógica do servidor)
            header_for_check = struct.pack(self.HEADER_FORMAT, 
                                        response_pkt.sequence_number, 
                                        response_pkt.ack_number, 
                                        response_pkt.flags, 
                                        0) 
            checksum_calculated = zlib.crc32(header_for_check + response_pkt.data) & 0xffff

            if checksum_calculated != response_pkt.checksum:
                print(f"❌ Checksum inválido no SYN-ACK. Descartando pacote.")
                return

            # Verificação das Flags
            if (response_pkt.flags & self.FLAG_SYN) and (response_pkt.flags & self.FLAG_ACK):
                print("------------------------------------------------------------------")
                print(f"✅ SYN-ACK recebido com sucesso de {server_address_received}!")
                print(f"[PACOTE] SEQ={response_pkt.seq_num} ACK={response_pkt.ack_num}")
                
                # Verificação de ACK (Deve confirmar o nosso SEQ inicial + 1)
                if response_pkt.ack_number == initial_seq + 1:
                    print(f"✅ Confirmação (ACK) correta: {response_pkt.ack_num} (Esperado: {initial_seq + 1})")
                else:
                    print(f"❌ Confirmação (ACK) incorreta: Recebido {response_pkt.ack_num}, Esperado {initial_seq + 1}")
                
                print("------------------------------------------------------------------")
                
            else:
                print(f"❌ Resposta inválida. Flags recebidas: {response_pkt.flags}. Esperado SYN|ACK.")
                
        except socket.timeout:
            print(f"\n[TIMEOUT] Estouro de tempo ({self.CLIENT_TIMEOUT}s). O servidor não respondeu.")
            
        except Exception as e:
            print(f"\n[ERRO] Ocorreu um erro na comunicação: {e}")
            
        finally:
            self.client_socket.close()
            print("Socket do cliente fechado.")

if __name__ == "__main__":
    # Garantir que o servidor tenha tempo para iniciar
    time.sleep(1) 
    Client()