package com.sentinel.shield

import android.content.Context
import android.content.Intent
import android.net.Uri
import android.util.Log
import android.widget.Toast

object InstallHandoff {
    private const val TAG = "InstallHandoff"

    fun launchPackageInstaller(context: Context, apkUri: Uri): Boolean {
        return try {
            val installIntent = Intent(Intent.ACTION_VIEW).apply {
                setDataAndType(apkUri, "application/vnd.android.package-archive")
                flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_GRANT_READ_URI_PERMISSION
            }
            context.startActivity(installIntent)
            Log.d(TAG, "Successfully handed off $apkUri to PackageInstaller")
            true
        } catch (e: Exception) {
            Log.e(TAG, "Failed to launch package installer: ${e.message}", e)
            Toast.makeText(context, "Installer failed: ${e.message}", Toast.LENGTH_LONG).show()
            false
        }
    }
}
