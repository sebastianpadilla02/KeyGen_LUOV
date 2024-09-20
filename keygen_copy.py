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
        self.SHAKE = 128
        public_sponge = self.InitializeAndAbsorb(public_seed)
        C, L, Q1 = self.SqueezePublicMap(public_sponge)
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
        num_bytes = (self.v * self.m + 7) // 8  # Redondear al mayor(función techo) para asegurarse de tener suficientes bits
        
        random_bytes = private_sponge.digest(32 + num_bytes)  # Exprimir los bytes necesarios
        public_seed = random_bytes[:32]  # Los primeros 32 bytes son la semilla pública
        print(public_seed)
        random_bytes = random_bytes[32:]  # Los bytes restantes son para la matriz T

        bits = ''.join(f'{byte:08b}' for byte in random_bytes)  # Convertir los bytes a bits
        
        # Verificar que tenemos suficientes bits
        assert len(bits) >= self.v * self.m, "Error: no hay suficientes bits para llenar la matriz T."

        for i in range(self.v):
            for j in range(self.m):
                T[i, j] = int(bits[i * self.m + j])  # Asignar los bits a la matriz T
        return public_seed, T

    def squeeze_bits(self, shake, num_bits):
        """Función para exprimir una cantidad específica de bits de la esponja."""
        num_bytes = (num_bits + 7) // 8  # Calcular cuántos bytes se necesitan
        random_bytes = shake.digest(num_bytes)
        bits = ''.join(f'{byte:08b}' for byte in random_bytes)
        return bits[:num_bits]

    def SqueezePublicMap(self, public_sponge):
        # Generar la matriz C, que tiene m filas y 1 columna (m * 1 bits)
        bits_C = self.squeeze_bits(public_sponge, self.m * 1)
        C = np.array([int(bits_C[i]) for i in range(self.m)]).reshape((self.m, 1))
        
        # Generar la matriz L, que tiene m filas y n columnas (m * n bits)
        bits_L = self.squeeze_bits(public_sponge, self.m * self.n)
        L = np.array([int(bits_L[i]) for i in range(self.m * self.n)]).reshape((self.m, self.n))
        
        # Generar la matriz Q1, que tiene m filas y (v*(v+1)/2 + v*m) columnas (m * [v*(v+1)/2 + v*m] bits)
        q1_size = self.v * (self.v + 1) // 2 + self.v * self.m
        bits_Q1 = self.squeeze_bits(public_sponge, self.m * q1_size)
        Q1 = np.array([int(bits_Q1[i]) for i in range(self.m * q1_size)]).reshape((self.m, q1_size))
        
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

