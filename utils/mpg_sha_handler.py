import hashlib


def create_mpg_sha_encrypt(mpg_data_aes, hash_key, hash_iv):
    mpg_data_aes = "HashKey=" + hash_key + "&" + mpg_data_aes + "&HashIV=" + hash_iv
    mpg_data_aes = mpg_data_aes.encode("utf8")

    shavalue = hashlib.sha256()
    shavalue.update(mpg_data_aes)

    return shavalue.hexdigest().upper()
