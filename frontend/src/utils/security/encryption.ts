/**
 * Encryption Utilities
 * Provides client-side encryption for sensitive data in the CBSC Dashboard
 */

import CryptoJS from 'crypto-js';

// Encryption configuration
const ENCRYPTION_CONFIG = {
  ALGORITHM: 'AES',
  KEY_SIZE: 256,
  ITERATIONS: 10000,
  IV_SIZE: 16,
  SALT_SIZE: 32
};

/**
 * Encryption class
 */
export class EncryptionUtil {
  private static instance: EncryptionUtil;
  private masterKey: string | null = null;

  private constructor() {}

  /**
   * Singleton instance getter
   */
  public static getInstance(): EncryptionUtil {
    if (!EncryptionUtil.instance) {
      EncryptionUtil.instance = new EncryptionUtil();
    }
    return EncryptionUtil.instance;
  }

  /**
   * Initialize with master key
   */
  public async initialize(password?: string): Promise<void> {
    if (password) {
      // Derive key from password
      this.masterKey = await this.deriveKey(password);
    } else {
      // Generate random key
      this.masterKey = this.generateKey();
    }
  }

  /**
   * Derive encryption key from password
   */
  private async deriveKey(password: string): Promise<string> {
    const salt = CryptoJS.lib.WordArray.random(ENCRYPTION_CONFIG.SALT_SIZE / 8);
    const key = CryptoJS.PBKDF2(password, salt, {
      keySize: ENCRYPTION_CONFIG.KEY_SIZE / 32,
      iterations: ENCRYPTION_CONFIG.ITERATIONS
    });

    // Store salt for key derivation
    sessionStorage.setItem('_enc_salt', salt.toString());

    return key.toString();
  }

  /**
   * Generate random encryption key
   */
  private generateKey(): string {
    return CryptoJS.lib.WordArray.random(ENCRYPTION_CONFIG.KEY_SIZE / 8).toString();
  }

  /**
   * Get current encryption key
   */
  public getKey(): string | null {
    return this.masterKey;
  }

  /**
   * Encrypt data
   */
  public encrypt(data: string): string {
    if (!this.masterKey) {
      throw new Error('Encryption not initialized');
    }

    try {
      const encrypted = CryptoJS.AES.encrypt(data, this.masterKey).toString();
      return this.encodeBase64(encrypted);
    } catch (error) {
      throw new Error(`Encryption failed: ${error}`);
    }
  }

  /**
   * Decrypt data
   */
  public decrypt(encryptedData: string): string {
    if (!this.masterKey) {
      throw new Error('Encryption not initialized');
    }

    try {
      const decoded = this.decodeBase64(encryptedData);
      const decrypted = CryptoJS.AES.decrypt(decoded, this.masterKey);
      return decrypted.toString(CryptoJS.enc.Utf8);
    } catch (error) {
      throw new Error(`Decryption failed: ${error}`);
    }
  }

  /**
   * Encrypt object
   */
  public encryptObject(obj: any): string {
    const jsonString = JSON.stringify(obj);
    return this.encrypt(jsonString);
  }

  /**
   * Decrypt object
   */
  public decryptObject<T = any>(encryptedData: string): T {
    const decryptedString = this.decrypt(encryptedData);
    return JSON.parse(decryptedString) as T;
  }

  /**
   * Encrypt with password (one-time, doesn't store key)
   */
  public encryptWithPassword(data: string, password: string): string {
    const salt = CryptoJS.lib.WordArray.random(ENCRYPTION_CONFIG.SALT_SIZE / 8);
    const key = CryptoJS.PBKDF2(password, salt, {
      keySize: ENCRYPTION_CONFIG.KEY_SIZE / 32,
      iterations: ENCRYPTION_CONFIG.ITERATIONS
    });

    const iv = CryptoJS.lib.WordArray.random(ENCRYPTION_CONFIG.IV_SIZE / 8);
    const encrypted = CryptoJS.AES.encrypt(data, key, { iv });

    // Combine salt, iv, and encrypted data
    const combined = salt.toString() + iv.toString() + encrypted.toString();
    return this.encodeBase64(combined);
  }

  /**
   * Decrypt with password
   */
  public decryptWithPassword(encryptedData: string, password: string): string {
    const combined = this.decodeBase64(encryptedData);

    // Extract salt, iv, and encrypted data
    const salt = CryptoJS.enc.Hex.parse(combined.substr(0, 64));
    const iv = CryptoJS.enc.Hex.parse(combined.substr(64, 32));
    const encrypted = combined.substr(96);

    const key = CryptoJS.PBKDF2(password, salt, {
      keySize: ENCRYPTION_CONFIG.KEY_SIZE / 32,
      iterations: ENCRYPTION_CONFIG.ITERATIONS
    });

    const decrypted = CryptoJS.AES.decrypt(encrypted, key, { iv });
    return decrypted.toString(CryptoJS.enc.Utf8);
  }

  /**
   * Generate secure hash
   */
  public hash(data: string, salt?: string): string {
    const dataToHash = salt ? data + salt : data;
    return CryptoJS.SHA256(dataToHash).toString();
  }

  /**
   * Verify hash
   */
  public verifyHash(data: string, hash: string, salt?: string): boolean {
    const computedHash = this.hash(data, salt);
    return computedHash === hash;
  }

  /**
   * Generate random token
   */
  public generateToken(length: number = 32): string {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let token = '';

    for (let i = 0; i < length; i++) {
      const randomIndex = Math.floor(Math.random() * chars.length);
      token += chars[randomIndex];
    }

    return token;
  }

  /**
   * Generate secure random number
   */
  public secureRandom(min: number, max: number): number {
    const range = max - min + 1;
    const bytes = Math.ceil(Math.log2(range) / 8);
    const randomValues = new Uint8Array(bytes);
    crypto.getRandomValues(randomValues);

    let randomValue = 0;
    for (let i = 0; i < bytes; i++) {
      randomValue = randomValue * 256 + randomValues[i];
    }

    return min + (randomValue % range);
  }

  /**
   * Encode base64 URL-safe
   */
  private encodeBase64(data: string): string {
    return btoa(data)
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=/g, '');
  }

  /**
   * Decode base64 URL-safe
   */
  private decodeBase64(data: string): string {
    // Add padding
    data += '='.repeat((4 - data.length % 4) % 4);
    // Replace URL-safe characters
    data = data.replace(/-/g, '+').replace(/_/g, '/');
    return atob(data);
  }

  /**
   * Secure storage helpers
   */
  public setSecureItem(key: string, value: string): void {
    const encrypted = this.encrypt(value);
    localStorage.setItem(key, encrypted);
  }

  public getSecureItem(key: string): string | null {
    const encrypted = localStorage.getItem(key);
    if (!encrypted) return null;

    try {
      return this.decrypt(encrypted);
    } catch {
      return null;
    }
  }

  public removeSecureItem(key: string): void {
    localStorage.removeItem(key);
  }

  /**
   * Session secure storage helpers
   */
  public setSecureSessionItem(key: string, value: string): void {
    const encrypted = this.encrypt(value);
    sessionStorage.setItem(key, encrypted);
  }

  public getSecureSessionItem(key: string): string | null {
    const encrypted = sessionStorage.getItem(key);
    if (!encrypted) return null;

    try {
      return this.decrypt(encrypted);
    } catch {
      return null;
    }
  }

  public removeSecureSessionItem(key: string): void {
    sessionStorage.removeItem(key);
  }

  /**
   * Generate key pair for asymmetric encryption (simplified)
   */
  public async generateKeyPair(): Promise<{ publicKey: string; privateKey: string }> {
    // Note: This is a simplified implementation
    // In production, use Web Crypto API for proper asymmetric encryption
    const privateKey = this.generateKey();
    const publicKey = this.hash(privateKey).substring(0, 64);

    return { publicKey, privateKey };
  }

  /**
   * Wipe sensitive data from memory
   */
  public wipe(): void {
    this.masterKey = null;
    sessionStorage.removeItem('_enc_salt');

    // Force garbage collection if available
    if ((window as any).gc) {
      (window as any).gc();
    }
  }
}

// Export singleton instance
export const encryption = EncryptionUtil.getInstance();

// Convenience functions
export const encrypt = (data: string): string => encryption.encrypt(data);
export const decrypt = (encryptedData: string): string => encryption.decrypt(encryptedData);
export const encryptObject = (obj: any): string => encryption.encryptObject(obj);
export const decryptObject = <T = any>(encryptedData: string): T => encryption.decryptObject<T>(encryptedData);
export const secureHash = (data: string, salt?: string): string => encryption.hash(data, salt);
export const generateToken = (length?: number): string => encryption.generateToken(length);