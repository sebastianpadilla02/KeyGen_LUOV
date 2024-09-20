import os

from keygen_copy import KG

def lectura_params():
    op = 0

    while op < 1 or op > 3:
        op = int(input("Ingrese el número del nivel de seguridad que quiere implmentar en su llave\n \t1. LUOV-7-57-197 \n \t2. LUOV-7-83-283\n \t3. LUOV-7-110-374\nIngresa la opción: "))
        if(op < 1 and op > 3):
            print('Ingrese una opción válida')

    #params = [r, m, v, SHAKE]
    if op == 1:
        params = [7, 57, 197, 128]
    elif op == 2:
        params = [7, 83, 283, 256]
    elif op == 3:
        params = [7, 110, 374, 256]

    return(params)

def generar_semilla_privada():
    private_seed = os.urandom(32)
    return private_seed

if __name__ == "__main__":
    params = lectura_params()
    private_seed = generar_semilla_privada()
    llaves = KG(params, private_seed)
    public_key, private_key = llaves.public_key, private_seed
    print(f'public key: {public_key}')
    print(f'private key: {private_key}')
    
