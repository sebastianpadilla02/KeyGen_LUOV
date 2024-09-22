import hashlib
import numpy as np

class KG:

    def __init__(self, params: list, private_seed: bytes) -> bytes:
        self.r = params[0]
        self.m = params[1]
        self.v = params[2]
        self.SHAKE = params[3]
        self.n = self.v + self.m
        self.KeyGen(private_seed)
        self.public_key

    def KeyGen(self, private_seed: bytes):
        private_sponge = self.InitializeAndAbsorb(private_seed)
        #public_seed = self.SqueezePublicSeed(private_sponge)
        public_seed, T = self.SqueezeT(private_sponge)
        #print(T)
        self.SHAKE = 128
        #public_sponge = self.InitializeAndAbsorb(public_seed)
        C, L, Q1 = self.SqueezePublicMap(public_seed)
        Q2 = self.FindQ2(Q1, T)
        self.public_key = self.FindPublicKey(Q2, public_seed)

    def InitializeAndAbsorb(self, seed: bytes) -> hashlib:
        if(self.SHAKE == 128):
            shake = hashlib.shake_128()
        else:
            shake = hashlib.shake_256()
        
        shake.update(seed)

        return shake

    # def SqueezePublicSeed(self, private_sponge: hashlib) -> bytes:
    #     return private_sponge.digest(32)  # Obtener 32 bytes (256 bits) de la esponja

    def SqueezeT(self, private_sponge: hashlib):
        T = np.zeros((self.v, self.m), dtype = int)

        # Calcular el número de bytes necesarios para generar una matriz de v x m bits
        num_bytes = ((self.m + 7) // 8) * self.v  # Redondear al mayor(función techo) para asegurarse de tener suficientes bits
        
        random_bytes = private_sponge.digest(32 + num_bytes)  # Exprimir los bytes necesarios
        #print(f'Tamaño de bytes generados por shake: {len(random_bytes)}')

        public_seed = random_bytes[:32]  # Los primeros 32 bytes son la semilla pública

        print(f'Semilla publica: {public_seed} y su tamaño {len(public_seed)}')

        random_bytes_for_T = random_bytes[32:]  # Los bytes restantes son para la matriz T
        #print(f'num de bits restantes {len(random_bytes_for_T)}')
        #print(random_bytes_for_T)

        # Extraemos los bits correspondientes a cada fila de la matriz T
        for i in range(self.v):
            # Encontrar los bytes correspondientes a la fila i
            start_byte_index = (i * (self.m + 7)) // 8  # Inicio del rango de bytes para la fila i
            end_byte_index = ((i + 1) * (self.m + 7)) // 8  # Final del rango de bytes para la fila i
            #print(f'start: {start_byte_index}, end: {end_byte_index}')
            byte_chunk = random_bytes_for_T[start_byte_index:end_byte_index]  # Obtener los bytes correspondientes
            # print(f'{byte_chunk} de tamaño: {len(byte_chunk)}')
            # for k in byte_chunk:
            #     print(bytes([k]))
        
            # Tomar todos los bytes excepto el último
            all_but_last = byte_chunk[:-1]

            #print(f'Todos menos el ultimo: {all_but_last} y longitud {len(all_but_last)}')
            # Tomar el último byte
            last_byte = bytes([byte_chunk[-1]])
            
            # print(f'Tipos: Todos:{type(all_but_last)}, Ultimo: {type(last_byte)}')

            # print(f'ultimo: {last_byte} y longitud {len(last_byte)}')

            bits = ''.join(f'{byte:08b}' for byte in all_but_last)  # Convertir los bytes a bits

            bits_faltantes = self.m % 8
            last_byte_bits = '' + f'{last_byte[0]:08b}'
            #print(f'Last byte bits: {last_byte_bits} y bits faltantes: {bits_faltantes}')
            if bits_faltantes > 0:
                # Tomar los n últimos bits del string
                last_byte_bits = last_byte_bits[-bits_faltantes:]

            # print(f'last_byte_bits cambiado: {last_byte_bits}')
            # print(bits)
            bits += last_byte_bits

            #print(f'bits: {bits} de tamaño{len(bits)}')
            
            # Verificación: asegúrate de que los bits son suficientes
            if len(bits) < self.m:
                raise ValueError(f"No hay suficientes bits para llenar la fila {i}: se esperaban {self.m} bits pero se encontraron {len(bits)}")
            
            # Asignar los primeros m bits a la fila i de la matriz T
            for j in range(self.m):
                #print(f'j: {j} y bits[j]: {int(bits[j])}')
                T[i, j] = int(bits[j])  # Asignar el bit correspondiente
            
            #print(T[i])
        return public_seed, T

    def G(self, public_seed: bytes, index: int, num_bytes: int) -> bytes:
        # Concatenar el public_seed con el índice
        seed_with_index = public_seed + bytes([index])

        # Inicializar SHAKE128 (se debe inicializar cada vez)
        shake = hashlib.shake_128()
        shake.update(seed_with_index)

        # Generar el número de bytes necesario
        return shake.digest(num_bytes)


    # def squeeze_bits(self, shake, num_bits):
    #     """Función para exprimir una cantidad específica de bits de la esponja."""
    #     num_bytes = (num_bits + 7) // 8  # Calcular cuántos bytes se necesitan
    #     random_bytes = shake.digest(num_bytes)
    #     bits = ''.join(f'{byte:08b}' for byte in random_bytes)
    #     return bits[:num_bits]

    def SqueezePublicMap(self, public_seed):
        q1_size = self.v * (self.v + 1) // 2 + self.v * self.m

        # Inicializamos las matrices C, L y Q1
        C = np.zeros((self.m, 1), dtype=int)
        L = np.zeros((self.m, self.n), dtype=int)
        Q1 = np.zeros((self.m, q1_size), dtype=int)

        # El número de bytes necesarios para cada bloque de 16 filas
        num_bytes_per_block = 2 * (1 + self.n + (self.v*(self.v+1))//2 + self.v * self.m)

        for i in range((self.m + 15)//16):

            G_output = self.G(public_seed, i, num_bytes_per_block)

            #Generar la matriz C
            # Tomar los primeros 2 bytes
            first_2_bytes = G_output[:2]

            bits = ''.join(f'{byte:08b}' for byte in first_2_bytes)

            if(self.m % 16 != 0) and (i == (self.m + 15)//16 - 1):
                bytes_needed = ((self.m % 16) + 7)//8
                bits_added = 0
                pos = 0
                if(bytes_needed == 2):
                    for l in range(16*i, 16*i + 8):
                        C[l, 0] = bits[bits_added]
                        bits_added += 1
                    
                    pos = l + 1

                bits_restantes = self.m % 16 - bits_added
                #print(f'bits_restantes: {bits_restantes}')
                bits_menos_significativos = bits[-bits_restantes:]
                #print(bits_menos_significativos)
                #print(f'pos: {pos}')
                for h in range(bits_restantes):
                    C[pos, 0] = bits_menos_significativos[h]
                    pos += 1
            else:
                bits_added = 0
                for c in range(16*i, 16*i + 16):
                    C[c, 0] = bits[bits_added]
                    bits_added += 1
            
            #Generar la matriz L
            bytes_for_L = G_output[2:2 + 2 * self.n]

            bits_L = ''.join(f'{byte:08b}' for byte in bytes_for_L)

            if(self.m % 16 != 0) and (i == (self.m + 15)//16 - 1):
                bytes_needed = ((self.m % 16) + 7)//8
                bits_added = 0
                column = 0
                #Pa que recuerdes, mejor haz toda la columna entera y ya luego vas cambiando la fila
                for cont_bits in range(0, len(bits_L), 16):
                    bits_2_bytes = bits_L[cont_bits:cont_bits+16]
                    #print(bits_2_bytes)
                    bits_added = 0
                    pos = 0
                    if(bytes_needed == 2):
                        for l in range(16*i, 16*i + 8):
                            L[l, column] = bits_2_bytes[bits_added]
                            bits_added += 1
                        
                        pos = l + 1

                    bits_restantes = self.m % 16 - bits_added

                    bits_menos_significativos = bits_2_bytes[-bits_added:]

                    for h in range(bits_restantes):
                        L[pos, column] = bits_menos_significativos[h]
                        pos += 1

                    column += 1
            else:
                bits_added = 0
                
                for j in range(self.n):
                    for c in range(16*i, 16*i + 16):
                        L[c, j] = bits_L[bits_added]
                        bits_added += 1
            
            #Generar la matriz Q1
            
        
        # # Generar la matriz Q1, que tiene m filas y (v*(v+1)/2 + v*m) columnas (m * [v*(v+1)/2 + v*m] bits)
        
        # bits_Q1 = self.squeeze_bits(public_sponge, self.m * q1_size)
        # Q1 = np.array([int(bits_Q1[i]) for i in range(self.m * q1_size)]).reshape((self.m, q1_size))
        
        return C, L, Q1

    def findPk1(self, k, Q1):
        Pk_1 = np.zeros((self.v, self.v), dtype = int)
        column = 0
        for i in range(self.v):
            for j in range(i, self.v):
                Pk_1[i,j] = Q1[k, column]
                column += 1
            column = column + self.m
        
        return Pk_1

    def findPk2(self, k, Q1):
        Pk_2 = np.zeros((self.v, self.m), dtype = int)
        column = 0
        for i in range(self.v):
            column = column + self.v - i
            for j in range(self.m):
                Pk_2[i,j] = Q1[k, column]
                column += 1
        
        return Pk_2


    def FindQ2(self, Q1, T):
        D2 = self.m * (self.m + 1) // 2
        Q2 = np.zeros((self.m,D2), dtype = int) 
        for k in range(self.m):
            Pk_1 = self.findPk1(k, Q1)
            Pk_2 = self.findPk2(k, Q1)
            term1 = -np.dot(T.T, np.dot(Pk_1, T))
            term2 = np.dot(T.T, Pk_2)
            Pk_3 = term1 + term2

            #Asegurar que Pk3 sea skew-simétrica
            Pk_3 = (Pk_3 - Pk_3.T) / 2

            column = 0
            for i in range(self.m):
                Q2[k, column] = Pk_3[i, i]
                column += 1
                for j in range(i+1, self.m):
                    Q2[k, column] = Pk_3[i, j] + Pk_3[j, i]
                    column += 1
        
        return Q2
    
    def bit_string_to_bytes(self, bit_string):
        # Asegúrate de que la longitud del bit_string sea un múltiplo de 8
        bit_string = bit_string.zfill(len(bit_string) + (8 - len(bit_string) % 8))  # Completar con ceros si no es múltiplo de 8
        
        # Dividir el bit_string en bloques de 8 bits y convertirlos en enteros
        byte_list = [int(bit_string[i:i+8], 2) for i in range(0, len(bit_string), 8)]
        
        # Convertir la lista de enteros a un objeto bytes
        return bytes(byte_list)


    def FindPublicKey(self, Q2, public_seed):
        D2 = self.m * (self.m + 1) // 2
        concat_bits = ''.join(f'{byte:08b}' for byte in public_seed)
        for j in range(D2):
            for i in range(self.m):
                concat_bits += str(Q2[i, j])

        pk = self.bit_string_to_bytes(concat_bits)

        return pk

