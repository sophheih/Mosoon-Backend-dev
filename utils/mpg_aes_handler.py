from Crypto.Cipher import AES


def create_mpg_aes_encrypt(mpg_data, hash_key, hash_iv):
    cipher = AES.new(hash_key, AES.MODE_CBC, hash_iv)
    return cipher.encrypt(add_padding(mpg_data)).hex()


def add_padding(data):
    text_length = len(data)
    amount_to_pad = 32 - (text_length % 32)
    if amount_to_pad == 0:
        amount_to_pad = 32
    pad = chr(amount_to_pad)
    return data + pad * amount_to_pad
