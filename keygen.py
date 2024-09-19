import hashlib
import numpy as np

class KG:

    def __init__(self, params: list, private_seed: bytes) -> bytes:
        self.r = params[0]
        self.m = params[1]
        self.v = params[2]
        self.SHAKE = params[3]
        self.KeyGen(private_seed)

    def KeyGen(self, private_seed):
        private_sponge = self.InitializeAndAbsorb(private_seed, self.SHAKE)
        public_seed = self.SqueezePublicSeed(private_sponge)
        print(public_seed)
        T = self.SqueezeT(private_sponge, self.v, self.m)
        print(T)
        public_sponge = self.InitializeAndAbsorb(public_seed, self.SHAKE)
        C, L, Q1 = self.SqueezePublicMap(public_sponge, n = self.v + self.m, v = self.v, m = self.m)
        Q2 = self.FindQ2(Q1, T, m = self.m)

    def InitializeAndAbsorb(self, seed, type):
        if(type == 128):
            shake = hashlib.shake_128()
        else:
            shake = hashlib.shake_256()
        
        shake.update(seed)

        return shake

    def SqueezePublicSeed(self, private_sponge):
        return private_sponge.digest(32)  # Obtener 32 bytes (256 bits) de la esponja

    def SqueezeT(self, private_sponge, v, m):
        T = np.zeros((v,m), dtype = int)
        # Calcular el número de bytes necesarios para generar una matriz de v x m bits
        num_bytes = (v * m + 7) // 8  # Redondear al mayor(función techo) para asegurarse de tener suficientes bits
        random_bytes = private_sponge.digest(num_bytes)  # Exprimir los bytes necesarios
        bits = ''.join(f'{byte:08b}' for byte in random_bytes)  # Convertir los bytes a bits
        
        for i in range(v):
            for j in range(m):
                T[i, j] = int(bits[i * m + j])  # Asignar los bits a la matriz T
        return T

    def squeeze_bits(self, shake, num_bits):
        """Función para exprimir una cantidad específica de bits de la esponja."""
        num_bytes = (num_bits + 7) // 8  # Calcular cuántos bytes se necesitan
        random_bytes = shake.digest(num_bytes)
        bits = ''.join(f'{byte:08b}' for byte in random_bytes)
        return bits[:num_bits]

    def SqueezePublicMap(self, public_sponge, n, v, m):
        # Generar la matriz C, que tiene m filas y 1 columna (m * 1 bits)
        bits_C = self.squeeze_bits(public_sponge, m * 1)
        C = np.array([int(bits_C[i]) for i in range(m)]).reshape((m, 1))
        
        # Generar la matriz L, que tiene m filas y n columnas (m * n bits)
        bits_L = self.squeeze_bits(public_sponge, m * n)
        L = np.array([int(bits_L[i]) for i in range(m * n)]).reshape((m, n))
        
        # Generar la matriz Q1, que tiene m filas y (v*(v+1)/2 + v*m) columnas (m * [v*(v+1)/2 + v*m] bits)
        q1_size = v * (v + 1) // 2 + v * m
        bits_Q1 = self.squeeze_bits(public_sponge, m * q1_size)
        Q1 = np.array([int(bits_Q1[i]) for i in range(m * q1_size)]).reshape((m, q1_size))
        
        return C, L, Q1

    #def findPk1(k, Q1):


    # def FindQ2(self, Q1, T, m):
    #     Q2 = np.zeros((m,D2), dtype = int) # type: ignore
    #     for k in range(m):
    #         Pk_1 = findPk1(k, Q1)

    #     return Q2
