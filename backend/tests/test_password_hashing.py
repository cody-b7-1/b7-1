import os
import unittest

os.environ["JWT_SECRET_KEY"] = "dev-signing-key-with-at-least-32-bytes"

from app.auth.security import hash_password, verify_password


class PasswordHashingTests(unittest.TestCase):
    def test_hashes_and_verifies_password_with_argon2id(self) -> None:
        password = "password123!"

        password_hash = hash_password(password)

        self.assertTrue(password_hash.startswith("$argon2id$"))
        self.assertNotEqual(password_hash, password)
        self.assertTrue(verify_password(password, password_hash))
        self.assertFalse(verify_password("incorrect-password", password_hash))

    def test_password_hash_fits_database_column(self) -> None:
        password_hash = hash_password("password123!")

        self.assertLessEqual(len(password_hash), 255)


if __name__ == "__main__":
    unittest.main()
