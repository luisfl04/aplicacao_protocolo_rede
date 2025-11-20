import socket
import struct
import zlib
import time
from  package import Package
from decouple import config
import logging


class Client:
    
    # Configurações utilizadas pelo cliente:
    SERVER_ADDRESS = config("SERVER_ADDRESS")
    SERVER_PORT = int(config("SERVER_PORT"))
    SERVER_ADDRESS_COMPLETE = (SERVER_ADDRESS, SERVER_PORT)
    CLIENT_TIMEOUT = 5.0 
    FLAG_SYN = 1 << 0
    FLAG_ACK = 1 << 1
    FLAG_FINALIZACAO = 1 << 2
    FLAG_ERRO = 1 << 3  
    HEADER_FORMAT = config("HEADER_FORMAT")
    sequence_number = 0
    mode_descart = False 
    state_connection = False

    def __init__(self):
        # Iniciando cliente:
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_socket.settimeout(self.CLIENT_TIMEOUT)
        self.properties_client = {
            "ack_number": None,
            "sequence_number": self.sequence_number,
            "state_connection": self.state_connection,
            "mode_descart": self.mode_descart,
            "time_out": self.CLIENT_TIMEOUT,
            "server_address": self.SERVER_ADDRESS_COMPLETE
        } 


    def set_listening_state(self) -> bool:
        try:
            if self.mode_descart:
                self.mode_descart = False
                return self.mode_descart
            self.mode_descart = True
            return self.mode_descart
        except Exception as e:
            raise Exception(str(e))

    def start_connection(self) -> bool:
        """
        Função que implementa o primeiro envio de pacote ao servidor, iniciando a conexão
        """
        
        print(f"✅ Cliente iniciado. Tentando conectar com {self.SERVER_ADDRESS_COMPLETE}")
        
        try:  
            # Criando pacote de handshake:
            self.sequence_number +=1
            pacote_conexao = Package(sequence_number=self.sequence_number, flags=self.FLAG_SYN, data=b"Handshake de conexao")
            raw_bytes = pacote_conexao.pack_package()
            
            # Enviando pacote ao servidor:
            print(f"\n[ENVIO] Enviando pacote de handshake para o servidor...")
            self.client_socket.sendto(raw_bytes, self.SERVER_ADDRESS_COMPLETE)
            print(f"[ESPERA] Aguardando SYN-ACK do servidor (Timeout: {self.CLIENT_TIMEOUT}s)...")
            raw_response, server_address_received = self.client_socket.recvfrom(1024) 
            print("Pacote de resposta de handshake recebido")        
            response_package = pacote_conexao.unpack_package(raw_response)
            
            # Calculando checksum:
            header_for_check = struct.pack(self.HEADER_FORMAT, 
                                        response_package.sequence_number, 
                                        response_package.ack_number, 
                                        response_package.flags, 
                                        0) 
            checksum_calculated = zlib.crc32(header_for_check + response_package.data) & 0xffff
            
            # Verificando estado do pacote recebido e retornando resultado
            if checksum_calculated != response_package.checksum:
                return False, "Erro ao se conectar ao servidor. Um checksum inválido foi recebido, tente novamente."
            
            if (response_package.flags & self.FLAG_SYN) and (response_package.flags & self.FLAG_ACK):
                if response_package.ack_number == self.sequence_number + 1:
                    self.properties_client.update(
                        ack_number=response_package.ack_number,
                        state_connection=True
                    )
                    return True, str(response_package.data)
                else:
                    return False, "Confirmação de ACK incorreta, Numero de ACK inválido oriúndo do servidor, tente novamente."    
            else:
                return False, "Flags incorretas recebidas do servidor, tente novamente"
                        
        except socket.timeout:
            return False, "TimeOut estourado na tentativa de conexão, tente novamente."
            
        except Exception as e:
            logging.error(f"Exceção ao iniciar conexão com servidor. Log: {e}")
            return False, "Erro interno na comunicação com servidor, tente novamente."

    def set_properties_client(self, properties: dict):
        try:
            self.properties_client = properties
        except Exception as e:
            pass

    def enviar_pacote_manipulado(self):
        try:
            self.sequence_number+=1
            pacote = Package(sequence_number=self.sequence_number, flags=self.FLAG_SYN, data=b"Texto inicial")
            header_pacote = struct.pack(   
                self.HEADER_FORMAT,
                pacote.sequence_number,
                pacote.ack_number,
                pacote.flags,
                pacote.checksum
            )
            pacote.checksum = zlib.crc32(header_pacote + pacote.data) & 0xffff
            header_with_checksum = struct.pack(self.HEADER_FORMAT, 
                                            pacote.sequence_number, 
                                            pacote.ack_number, 
                                            pacote.flags, 
                                            pacote.checksum)
            pacote.data = b"Texto inicial -> Manipulado!"
            raw_bytes = header_with_checksum + pacote.data
            self.client_socket.sendto(raw_bytes, self.SERVER_ADDRESS_COMPLETE) 
            raw_response, server_address_received = self.client_socket.recvfrom(1024)

            if self.mode_descart:
                print("Descartando pacote recebido\nReenviando pacote..")
                time.sleep(3)
                self.enviar_pacote_manipulado()

            pacote_recebido = pacote.unpack_package(raw_response)
            if (pacote_recebido.flags & self.FLAG_SYN) and (pacote_recebido.flags & self.FLAG_ACK):
                raise Exception(f"Flags do pacote incorretas. Flag: {pacote_recebido.flags}")
            
            print("Negação de confirmação recebida, reenviando pacote para o servidor...")
            time.sleep(5)
            self.enviar_pacote_manipulado()
        except TimeoutError:
            print("Não há respostas do servidor, enviando pacote novamente...")
            self.enviar_pacote_manipulado()
        except Exception as e:
            print(f"Exceção ao enviar pacote manipulado: {e}")


if __name__ == "__main__":
    # Garantir que o servidor tenha tempo para iniciar
    time.sleep(1) 
    Client()