package com.sentinel.shield.api

import android.content.Context
import android.net.Uri
import android.util.Log
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.io.ByteArrayOutputStream
import java.io.InputStream
import java.io.OutputStream
import java.io.OutputStreamWriter
import java.io.PrintWriter
import java.net.HttpURLConnection
import java.net.URL
import java.security.MessageDigest

class SentinelClient(private var baseUrl: String = DEFAULT_BASE_URL) {

    companion object {
        const val TAG = "SentinelClient"
        var DEFAULT_BASE_URL = "http://192.168.0.247:8000" // 10.0.2.2 for Android Emulator, LAN IP:PORT for physical device
        const val CONNECT_TIMEOUT_MS = 15_000
        const val READ_TIMEOUT_MS = 60_000

        fun computeHashes(inputStream: InputStream): Pair<String, String> {
            val sha256Digest = MessageDigest.getInstance("SHA-256")
            val md5Digest = MessageDigest.getInstance("MD5")
            val buffer = ByteArray(8192)
            var bytesRead: Int
            while (inputStream.read(buffer).also { bytesRead = it } != -1) {
                sha256Digest.update(buffer, 0, bytesRead)
                md5Digest.update(buffer, 0, bytesRead)
            }
            val sha256 = sha256Digest.digest().joinToString("") { "%02x".format(it) }
            val md5 = md5Digest.digest().joinToString("") { "%02x".format(it) }
            return Pair(sha256, md5)
        }
    }

    fun setBaseUrl(url: String) {
        baseUrl = url.trimEnd('/')
    }

    fun getBaseUrl(): String = baseUrl

    suspend fun lookupHash(sha256: String, md5: String? = null): HashLookupResponse = withContext(Dispatchers.IO) {
        val url = URL("$baseUrl/api/lookup/hash")
        val conn = (url.openConnection() as HttpURLConnection).apply {
            requestMethod = "POST"
            connectTimeout = CONNECT_TIMEOUT_MS
            readTimeout = READ_TIMEOUT_MS
            setRequestProperty("Content-Type", "application/json; charset=UTF-8")
            doOutput = true
        }

        try {
            val payload = HashLookupRequest(sha256, md5).toJson()
            conn.outputStream.use { os ->
                os.write(payload.toByteArray(Charsets.UTF_8))
                os.flush()
            }

            val responseCode = conn.responseCode
            if (responseCode in 200..299) {
                val responseStr = conn.inputStream.bufferedReader().use { it.readText() }
                Log.d(TAG, "Hash lookup response: $responseStr")
                HashLookupResponse.fromJson(responseStr)
            } else {
                Log.w(TAG, "Hash lookup non-200 code: $responseCode")
                HashLookupResponse(known = false)
            }
        } catch (e: Exception) {
            Log.e(TAG, "Hash lookup failed: ${e.message}", e)
            HashLookupResponse(known = false)
        } finally {
            conn.disconnect()
        }
    }

    suspend fun uploadApk(context: Context, uri: Uri, fileName: String = "upload.apk"): String? = withContext(Dispatchers.IO) {
        val boundary = "===SentinelBoundary" + System.currentTimeMillis() + "==="
        val lineEnd = "\r\n"
        val twoHyphens = "--"

        val url = URL("$baseUrl/api/scan")
        val conn = (url.openConnection() as HttpURLConnection).apply {
            requestMethod = "POST"
            connectTimeout = CONNECT_TIMEOUT_MS
            readTimeout = READ_TIMEOUT_MS
            doInput = true
            doOutput = true
            useCaches = false
            setRequestProperty("Content-Type", "multipart/form-data; boundary=$boundary")
        }

        try {
            val outputStream: OutputStream = conn.outputStream
            val writer = PrintWriter(OutputStreamWriter(outputStream, "UTF-8"), true)

            // Header for file parameter
            writer.append(twoHyphens).append(boundary).append(lineEnd)
            writer.append("Content-Disposition: form-data; name=\"file\"; filename=\"$fileName\"").append(lineEnd)
            writer.append("Content-Type: application/vnd.android.package-archive").append(lineEnd)
            writer.append("Content-Transfer-Encoding: binary").append(lineEnd)
            writer.append(lineEnd).flush()

            // Stream APK content directly
            context.contentResolver.openInputStream(uri)?.use { inputStream ->
                val buffer = ByteArray(8192)
                var bytesRead: Int
                while (inputStream.read(buffer).also { bytesRead = it } != -1) {
                    outputStream.write(buffer, 0, bytesRead)
                }
                outputStream.flush()
            }

            writer.append(lineEnd).flush()
            writer.append(twoHyphens).append(boundary).append(twoHyphens).append(lineEnd).flush()
            writer.close()

            val responseCode = conn.responseCode
            if (responseCode in 200..299) {
                val responseStr = conn.inputStream.bufferedReader().use { it.readText() }
                Log.d(TAG, "Upload response: $responseStr")
                val json = JSONObject(responseStr)
                if (json.has("scan_id") && !json.isNull("scan_id")) json.getString("scan_id") else null
            } else {
                val errStr = conn.errorStream?.bufferedReader()?.use { it.readText() } ?: ""
                Log.e(TAG, "Upload error ($responseCode): $errStr")
                null
            }
        } catch (e: Exception) {
            Log.e(TAG, "Upload exception: ${e.message}", e)
            null
        } finally {
            conn.disconnect()
        }
    }

    suspend fun pollScan(scanId: String): ScanDetailResponse = withContext(Dispatchers.IO) {
        val url = URL("$baseUrl/api/scan/$scanId")
        val conn = (url.openConnection() as HttpURLConnection).apply {
            requestMethod = "GET"
            connectTimeout = CONNECT_TIMEOUT_MS
            readTimeout = READ_TIMEOUT_MS
        }

        try {
            val responseCode = conn.responseCode
            if (responseCode in 200..299) {
                val responseStr = conn.inputStream.bufferedReader().use { it.readText() }
                ScanDetailResponse.fromJson(responseStr)
            } else {
                val err = conn.errorStream?.bufferedReader()?.use { it.readText() } ?: "HTTP $responseCode"
                ScanDetailResponse(scanId = scanId, status = "failed", errorMessage = err)
            }
        } catch (e: Exception) {
            ScanDetailResponse(scanId = scanId, status = "failed", errorMessage = e.message)
        } finally {
            conn.disconnect()
        }
    }
}
