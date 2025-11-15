import struct # Para criação do pacote
import zlib # Para checksum
import logging



class Packet:
    def __init__(self, sequence_number=0, ack_number=0, flags=0, data=b''):
        self.sequence_number = sequence_number
        self.ack_number = ack_number
        self.flags = flags
        self.checksum = 0
        self.data = data
    
    def get_package_properties(self) -> dict | None:
        """
        Retorna as propiedades necessesárias pra criar o pacote
        """
        try:    
            HEADER_FORMAT = '!IIHH'
            HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
            FLAG_SYN = 1 << 0  
            FLAG_ACK = 1 << 1  
            FLAG_CHECKSUM = 1 << 2
            propiedades = {
                "header_format": HEADER_FORMAT,
                "header_size": HEADER_SIZE,
                "flag_syncronizate": FLAG_SYN,
                "flag_ack": FLAG_ACK,
                "flag_checksum": FLAG_CHECKSUM
            }
            return propiedades
        except Exception as e:
            logging.error(f"Erro ao obter propiedades do pacote: {e}")
            return None

    def pack_package(self) -> bytes | None:
        """
            Função usada para empacotar o pacote, fazendo a junção do cabeçalho com os dados
        """

        try:
            # Empacotando versão inicial do cabeçalho:
            propiedades = self.get_package_properties()
            header = struct.pack(   
                propiedades.get("header_format"),
                self.sequence_number,
                self.ack_number,
                self.flags,
                self.checksum
            )

            # Calculando um checksum limitado de 16 bytes:
            self.checksum = zlib.crc32(header + self.data) & 0xffff

            # Empacotando novamente o cabeçalho com o checksum: 
            header_with_checksum = struct.pack(propiedades.get("header_format"), 
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
            # Obtendo propriedades do pacote:
            propiedades = self.get_package_properties()

            # Filtrando cabeçalho e dados:
            header_data = raw_data[:propiedades.get("header_size")]
            data = raw_data[propiedades.get("header_size"):]
            
            # Desempacotando o cabeçalho:
            sequence_number, ack_number, flags, checksum_received = struct.unpack(propiedades.get("header_format"), header_data)
            
            # Criando o objeto packet e armazenando o checksum:
            packet = Packet(sequence_number, ack_number, flags, data)
            packet.checksum = checksum_received
            
            return packet
        except Exception as e:
            logging.error(f"Erro ao desempacotar pacote: {e}")
            return None

    def __str__(self):
        """ Representação em string para fácil depuração (debug). """    
        return (f"[Packet: SEQ={self.seq_num} ACK={self.ack_num} "
                f"Flags={'|'.join(flag_str)} Checksum={self.checksum} "
                f"DataLen={len(self.data)}]")