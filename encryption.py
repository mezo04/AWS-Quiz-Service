from config import settings
import logging

logger = logging.getLogger(__name__)


class CryptoHandler:
    def __init__(self, password: str):
        """
        Initialize the CryptoHandler with a password.
        The password will be used as the key for XOR encryption.
        """
        self.key = password.encode('utf-8')
    
    def _xor(self, data: bytes, key: bytes) -> bytes:
        """
        Perform XOR operation on data using the key.
        Repeats the key if it's shorter than the data.
        """
        return bytes([d ^ k for d, k in zip(data, (key * (len(data) // len(key) + 1))[:len(data)])])
    
    def encrypt(self, message: str) -> bytes:
        """
        Encrypt the message using XOR with the key.
        Returns the encrypted data as bytes.
        """
        data = message.encode('utf-8')
        encrypted = self._xor(data, self.key)
        return encrypted
    
    def decrypt(self, encrypted: bytes) -> str:
        """
        Decrypt the encrypted data using XOR with the key.
        Returns the original message as a string.
        """
        decrypted = self._xor(encrypted, self.key)
        return decrypted.decode('utf-8')

crypto_instance = CryptoHandler(settings.ENCRYPTION_KEY)

# Example usage (can be removed or commented out)
# if __name__ == "__main__":
#     original_message = "Hello, this is a secret message!"
#     encrypted = crypto_instance.encrypt(original_message)
#     print(f"Encrypted: {encrypted}")
    
#     decrypted = crypto_instance.decrypt(encrypted)
#     print(f"Decrypted: {decrypted}")
    
#     assert decrypted == original_message, "Decryption failed!"
#     print("Encryption and decryption successful.")