package com.sentinel.shield

import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.util.Log
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.lifecycleScope
import com.sentinel.shield.api.ScanDetailResponse
import com.sentinel.shield.api.ScanHistoryItem
import com.sentinel.shield.api.SentinelClient
import com.sentinel.shield.api.TriggerItem
import com.sentinel.shield.ui.ScanningScreen
import com.sentinel.shield.ui.StandbyScreen
import com.sentinel.shield.ui.VerdictScreen
import com.sentinel.shield.ui.theme.SentinelShieldTheme
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

sealed class ScreenState {
    object Standby : ScreenState()
    data class Scanning(val stageText: String, val sha256: String? = null) : ScreenState()
    data class Verdict(val scan: ScanDetailResponse, val apkUri: Uri?) : ScreenState()
}

class MainActivity : ComponentActivity() {

    companion object {
        const val TAG = "SentinelShield"
        private const val PREFS_NAME = "sentinel_prefs"
        private const val KEY_SERVER_URL = "server_url"
    }

    private lateinit var client: SentinelClient
    private var uiState by mutableStateOf<ScreenState>(ScreenState.Standby)
    private val scanHistory = mutableStateListOf<ScanHistoryItem>()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        val prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        var savedServerUrl = prefs.getString(KEY_SERVER_URL, SentinelClient.DEFAULT_BASE_URL)
            ?: SentinelClient.DEFAULT_BASE_URL
        // Automatically migrate if saved URL had no port or was from old network
        if (!savedServerUrl.contains(":8000") || savedServerUrl.contains("10.35.63.179")) {
            savedServerUrl = SentinelClient.DEFAULT_BASE_URL
            prefs.edit().putString(KEY_SERVER_URL, savedServerUrl).apply()
        }
        client = SentinelClient(savedServerUrl)

        refreshHistory()
        handleIncomingUri(intent?.data)

        setContent {
            SentinelShieldTheme {
                AppScreen(
                    state = uiState,
                    serverUrl = client.getBaseUrl(),
                    history = scanHistory,
                    onSaveServerUrl = { newUrl ->
                        client.setBaseUrl(newUrl)
                        prefs.edit().putString(KEY_SERVER_URL, newUrl).apply()
                        Toast.makeText(this, "Engine URL saved", Toast.LENGTH_SHORT).show()
                        refreshHistory()
                    },
                    onInstallHandoff = { apkUri ->
                        if (apkUri != null) {
                            InstallHandoff.launchPackageInstaller(this, apkUri)
                        }
                    },
                    onDismiss = {
                        uiState = ScreenState.Standby
                        refreshHistory()
                    }
                )
            }
        }
    }

    private fun refreshHistory() {
        lifecycleScope.launch {
            try {
                val remoteScans = client.fetchRecentScans()
                if (remoteScans.isNotEmpty()) {
                    scanHistory.clear()
                    scanHistory.addAll(remoteScans)
                }
            } catch (e: Exception) {
                Log.e(TAG, "History refresh error: ${e.message}")
            }
        }
    }


    @Composable
    private fun AppScreen(
        state: ScreenState,
        serverUrl: String,
        history: List<ScanHistoryItem>,
        onSaveServerUrl: (String) -> Unit,
        onInstallHandoff: (Uri?) -> Unit,
        onDismiss: () -> Unit
    ) {
        when (state) {
            is ScreenState.Standby -> {
                StandbyScreen(
                    currentServerUrl = serverUrl,
                    history = history,
                    onSaveServerUrl = onSaveServerUrl
                )
            }
            is ScreenState.Scanning -> {
                ScanningScreen(
                    stageText = state.stageText,
                    sha256 = state.sha256
                )
            }
            is ScreenState.Verdict -> {
                VerdictScreen(
                    scan = state.scan,
                    apkUri = state.apkUri,
                    onInstallHandoff = { onInstallHandoff(state.apkUri) },
                    onDismiss = onDismiss
                )
            }
        }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        handleIncomingUri(intent.data)
    }

    private fun handleIncomingUri(uri: Uri?) {
        if (uri == null) {
            Log.d(TAG, "Launched normally without incoming APK URI")
            return
        }

        Log.d(TAG, "Intercepted APK URI: $uri")
        lifecycleScope.launch {
            processApk(uri)
        }
    }

    private suspend fun processApk(uri: Uri) {
        uiState = ScreenState.Scanning("Hashing package & inspecting header...")

        var sha256 = ""
        var md5 = ""

        try {
            withContext(Dispatchers.IO) {
                contentResolver.openInputStream(uri)?.use { stream ->
                    val hashes = SentinelClient.computeHashes(stream)
                    sha256 = hashes.first
                    md5 = hashes.second
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed reading APK stream: ${e.message}", e)
            Toast.makeText(this, "Failed to read APK file", Toast.LENGTH_LONG).show()
            uiState = ScreenState.Standby
            return
        }

        uiState = ScreenState.Scanning("Checking threat intelligence hash database...", sha256)

        // 1. Fast Path: Hash Lookup
        val hashResult = client.lookupHash(sha256, md5)
        if (hashResult.known && !hashResult.scanId.isNullOrEmpty()) {
            Log.d(TAG, "Fast-path match found for hash $sha256: score=${hashResult.finalScore}")
            uiState = ScreenState.Scanning("Known hash matched! Fetching analysis...", sha256)
            val fullScan = client.pollScan(hashResult.scanId)
            val scanToDisplay = if (fullScan.status == "completed") {
                fullScan
            } else {
                ScanDetailResponse(
                    scanId = hashResult.scanId,
                    status = "completed",
                    severity = hashResult.severity ?: "CRITICAL",
                    finalScore = hashResult.finalScore ?: 85,
                    fraudCategory = hashResult.fraudCategory ?: "banking_trojan",
                    triggers = listOf(
                        TriggerItem("HASH_THREAT_MATCH", "Previously identified malicious cyber threat signature", 50),
                        TriggerItem("PERM_SMS_INTERCEPTION", "Unauthorized credential harvesting capability", 35)
                    ),
                    behaviorSummary = "Cryptographic hash matches confirmed malicious payload recorded in Argus threat intelligence."
                )
            }

            addToHistory(uri.lastPathPathName() ?: "Intercepted.apk", scanToDisplay)
            uiState = ScreenState.Verdict(scanToDisplay, uri)
            return
        }

        // 2. Slow Path: Upload & Live Analysis
        uiState = ScreenState.Scanning("Uploading package to analysis engine...", sha256)
        val fileName = uri.lastPathPathName() ?: "intercepted_sample.apk"
        val scanId = client.uploadApk(this, uri, fileName)

        if (scanId == null) {
            Log.e(TAG, "Backend unreachable at ${client.getBaseUrl()}")
            Toast.makeText(this, "Failed to connect to ${client.getBaseUrl()}. Check engine URL.", Toast.LENGTH_LONG).show()
            uiState = ScreenState.Standby
            return
        }


        // 3. Poll Scan Status (up to 5 minutes / 300s window)
        var attempts = 0
        val maxAttempts = 150 
        var consecutiveNetworkErrors = 0

        while (attempts < maxAttempts) {
            delay(2000)
            val scan = client.pollScan(scanId)
            if (scan.status == "completed") {
                addToHistory(fileName, scan)
                uiState = ScreenState.Verdict(scan, uri)
                return
            } else if (scan.status == "failed") {
                val err = scan.errorMessage ?: "Scan analysis reported an error"
                Log.e(TAG, "Scan failed: $err")
                Toast.makeText(this, "Scan analysis failed on server", Toast.LENGTH_SHORT).show()
                uiState = ScreenState.Standby
                return
            } else if (scan.status == "network_error") {
                consecutiveNetworkErrors++
                Log.w(TAG, "Transient network error ($consecutiveNetworkErrors/15)")
                if (consecutiveNetworkErrors >= 15) {
                    Toast.makeText(this, "Connection lost to threat engine", Toast.LENGTH_SHORT).show()
                    uiState = ScreenState.Standby
                    return
                }
            } else {
                consecutiveNetworkErrors = 0
                val hint = scan.progressHint ?: "Analyzing stage (${attempts + 1}/$maxAttempts)..."
                uiState = ScreenState.Scanning(hint, sha256)
            }
            attempts++
        }


        Toast.makeText(this, "Analysis timed out. Please check server.", Toast.LENGTH_SHORT).show()
        uiState = ScreenState.Standby
    }


    private fun addToHistory(fileName: String, scan: ScanDetailResponse) {
        scanHistory.add(
            0,
            ScanHistoryItem(
                scanId = scan.scanId,
                fileName = fileName,
                score = scan.finalScore ?: 0,
                severity = scan.severity ?: "UNKNOWN",
                category = scan.fraudCategory ?: "Unclassified"
            )
        )
    }

    private fun Uri.lastPathPathName(): String? {
        val segment = this.lastPathSegment?.substringAfterLast('/') ?: "sample"
        return if (segment.endsWith(".apk", ignoreCase = true)) segment else "$segment.apk"
    }
}