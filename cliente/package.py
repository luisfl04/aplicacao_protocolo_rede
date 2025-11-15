import struct # Para criação do pacote
import zlib # Para checksum
import logging
from decouple import config

class Package:
    HEADER_FORMAT = config("HEADER_FORMAT")
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
    FLAG_SYN = config("FLAG_SYN") 
    FLAG_ACK = config("FLAG_ACK")  
    FLAG_CHECKSUM = config("FLAG_CHECKSUM")

    def __init__(self, sequence_number=0, ack_number=0, flags=0, data=b''):
        self.sequence_number = sequence_number
        self.ack_number = ack_number
        self.flags = flags
        self.checksum = 0
        self.data = data
    
    def pack_package(self) -> bytes | None:
        """
            Função usada para empacotar o pacote, fazendo a junção do cabeçalho com os dados
        """

        try:
            # Empacotando versão inicial do cabeçalho:
            propriedades = self.get_package_properties()
            header = struct.pack(   
                self.HEADER_FORMAT,
                self.sequence_number,
                self.ack_number,
                self.flags,
                self.checksum
            )

            # Calculando um checksum limitado de 16 bytes:
            self.checksum = zlib.crc32(header + self.data) & 0xffff

            # Empacotando novamente o cabeçalho com o checksum: 
            header_with_checksum = struct.pack(self.HEADER_FORMAT, 
                                            self.sequence_number, 
                                            self.ack_number, 
                                            self.flags, 
                                            self.checksum)
            
            # retornando o pacote(Header + data)  
            return header_with_checksum + self.data
        except Exception as e:
            logging.error(f"Erro ao empacotar informações do pacote: {e}")
            return None
        
        
        # 3. Re-empacota o cabeçalho, agora com o checksum correto

    def unpack_package(self, raw_data) -> object | None:
        """ 
            Desempacota bytes crus em um objeto Packet.
        """

        try:
            # Filtrando cabeçalho e dados:
            header_data = raw_data[:self.HEADER_SIZE]
            data = raw_data[self.HEADER_SIZE:]
            
            # Desempacotando o cabeçalho:
            sequence_number, ack_number, flags, checksum_received = struct.unpack(self.HEADER_FORMAT, header_data)
            
            # Criando o objeto packet e armazenando o checksum:
            packet = Package(sequence_number, ack_number, flags, data)
            packet.checksum = checksum_received
            
            return packet
        except Exception as e:
            logging.error(f"Erro ao desempacotar pacote: {e}")
            return None

    def __str__(self):
        """ Representação em string para fácil depuração (debug). """
        flag_str = []
        if self.flags & self.FLAG_SYN: flag_str.append("SYN")
        if self.flags & self.FLAG_ACK: flag_str.append("ACK")
        if self.flags & self.FLAG_CHECKSUM: flag_str.append("FIN")
        if not flag_str: flag_str.append("DATA")
        
        return (f"[Packet: SEQ={self.sequence_number} ACK={self.ack_number} "
                f"Flags={'|'.join(flag_str)} Checksum={self.checksum} "
                f"DataLen={len(self.data)}]")