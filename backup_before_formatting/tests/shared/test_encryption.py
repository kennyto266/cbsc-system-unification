"""
測試加密管理系統
"""

import os
import tempfile

import pytest
from shared.encryption.encryption_manager import (
    AES256EncryptionManager,
    decrypt_data,
    encrypt_data,
    generate_token,
    get_encryption_manager,
    hash_sensitive_data,
)


class TestAES256EncryptionManager:
    """AES - 256 加密管理器測試"""

    def test_encryption_manager_init(self):
        """測試加密管理器初始化"""
        manager = AES256EncryptionManager(password="test_password_123")
        assert manager.password == "test_password_123"
        assert manager.salt_length == 16
        assert manager.nonce_length == 12

    def test_encrypt_decrypt_string(self):
        """測試字符串加密和解密"""
        manager = AES256EncryptionManager(password="test_key_456")
        original_text = "這是一個測試文本，Hello World!"

        encrypted = manager.encrypt(original_text)
        assert encrypted != original_text
        assert isinstance(encrypted, str)

        decrypted = manager.decrypt(encrypted)
        assert decrypted == original_text

    def test_encrypt_decrypt_dict(self):
        """測試字典加密和解密"""
        manager = AES256EncryptionManager(password="test_key_789")
        original_data = {
            "username": "test_user",
            "email": "test@example.com",
            "api_keys": {
                "yahoo": "sk - 12345",
                "alpha_vantage": "av - 67890",
            },
        }

        encrypted = manager.encrypt(original_data)
        decrypted = manager.decrypt(encrypted)
        assert decrypted == original_data

    def test_encrypt_decrypt_list(self):
        """測試列表加密和解密"""
        manager = AES256EncryptionManager(password="test_list_key")
        original_data = [1, 2, 3, "a", "b", "c", {"nested": "value"}]

        encrypted = manager.encrypt(original_data)
        decrypted = manager.decrypt(encrypted)
        assert decrypted == original_data

    def test_encrypt_decrypt_numbers(self):
        """測試數字加密和解密"""
        manager = AES256EncryptionManager(password="test_number_key")
        original_data = {
            "integer": 42,
            "float": 3.14159,
            "negative": -100,
            "zero": 0,
        }

        encrypted = manager.encrypt(original_data)
        decrypted = manager.decrypt(encrypted)
        assert decrypted["integer"] == 42
        assert abs(decrypted["float"] - 3.14159) < 0.00001

    def test_different_passwords(self):
        """測試不同密碼的密文不同"""
        manager1 = AES256EncryptionManager(password="password1")
        manager2 = AES256EncryptionManager(password="password2")

        text = "測試文本"
        encrypted1 = manager1.encrypt(text)
        encrypted2 = manager2.encrypt(text)

        assert encrypted1 != encrypted2

    def test_hash_data(self):
        """測試數據哈希"""
        manager = AES256EncryptionManager()
        text1 = "相同的文本"
        text2 = "相同的文本"
        text3 = "不同的文本"

        hash1 = manager.hash_data(text1)
        hash2 = manager.hash_data(text2)
        hash3 = manager.hash_data(text3)

        assert hash1 == hash2
        assert hash1 != hash3
        assert len(hash1) == 64  # SHA - 256 輸出長度

    def test_generate_token(self):
        """測試生成安全令牌"""
        manager = AES256EncryptionManager()
        token1 = manager.generate_secure_token()
        token2 = manager.generate_secure_token(64)

        assert token1 != token2
        assert len(token1) > 0
        assert len(token2) > 0

    def test_file_encryption_decryption(self):
        """測試文件加密和解密"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 創建測試文件
            original_file = os.path.join(tmpdir, "test.txt")
            with open(original_file, "w", encoding="utf - 8") as f:
                f.write("這是測試文件內容\n包含多行文本\n和特殊字符：!@#$%")

            # 加密文件
            manager = AES256EncryptionManager(password="file_key")
            encrypted_file = manager.encrypt_file(original_file)

            assert os.path.exists(encrypted_file)
            assert encrypted_file.endswith(".encrypted")

            # 解密文件
            decrypted_file = manager.decrypt_file(encrypted_file)

            assert os.path.exists(decrypted_file)

            # 驗證內容 - 以二進制模式讀取，因為內容可能是 bytes
            try:
                with open(decrypted_file, "r", encoding="utf - 8") as f:
                    content = f.read()
                assert "這是測試文件內容" in content
                assert "包含多行文本" in content
            except UnicodeDecodeError:
                # 如果是 bytes，以二進制模式讀取
                with open(decrypted_file, "rb") as f:
                    content = f.read().decode("utf - 8")
                assert "這是測試文件內容" in content
                assert "包含多行文本" in content

    def test_invalid_decrypt(self):
        """測試無效解密"""
        manager = AES256EncryptionManager(password="test_key")

        # 嘗試解密無效數據
        with pytest.raises(Exception):
            manager.decrypt("invalid_base64_data")

        # 嘗試解密不完整的數據
        with pytest.raises(Exception):
            manager.decrypt("dGVzdA==")  # 只有 "test"

    def test_singleton_pattern(self):
        """測試單例模式"""
        manager1 = get_encryption_manager("password1")
        manager2 = get_encryption_manager("password2")

        # 由於是單例，密碼不會改變
        assert manager1.password == manager2.password


class TestConvenienceFunctions:
    """便捷函數測試"""

    def test_encrypt_data_function(self):
        """測試便捷加密函數"""
        data = "測試數據"
        encrypted = encrypt_data(data)
        decrypted = decrypt_data(encrypted)
        assert decrypted == data

    def test_hash_sensitive_data_function(self):
        """測試便捷哈希函數"""
        data1 = "敏感數據1"
        data2 = "敏感數據1"
        data3 = "敏感數據2"

        hash1 = hash_sensitive_data(data1)
        hash2 = hash_sensitive_data(data2)
        hash3 = hash_sensitive_data(data3)

        assert hash1 == hash2
        assert hash1 != hash3

    def test_generate_token_function(self):
        """測試便捷令牌生成函數"""
        token1 = generate_token()
        token2 = generate_token(16)

        assert token1 != token2
        assert isinstance(token1, str)
        assert len(token1) > 0


class TestSecurityProperties:
    """安全性測試"""

    def test_encryption_randomness(self):
        """測試加密的隨機性"""
        manager = AES256EncryptionManager(password="test_random")
        text = "相同的明文"

        # 同一明文每次加密結果都不同
        encrypted1 = manager.encrypt(text)
        encrypted2 = manager.encrypt(text)

        assert encrypted1 != encrypted2

    def test_password_complexity(self):
        """測試密碼複雜度"""
        manager1 = AES256EncryptionManager(password="123")
        manager2 = AES256EncryptionManager(
            password="very_long_and_complex_password_123456789"
        )

        text = "測試"
        encrypted1 = manager1.encrypt(text)
        encrypted2 = manager2.encrypt(text)

        # 不同的密碼應該產生不同的密文
        assert encrypted1 != encrypted2

    def test_empty_and_none_values(self):
        """測試空值和None值"""
        manager = AES256EncryptionManager(password="test_none")

        # 空字符串
        assert manager.encrypt("") != ""
        assert manager.decrypt(manager.encrypt("")) == ""

        # 空字典
        assert manager.encrypt({}) is not None
        assert manager.decrypt(manager.encrypt({})) == {}

        # 空列表
        assert manager.encrypt([]) is not None
        assert manager.decrypt(manager.encrypt([])) == []
