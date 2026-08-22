package com.sentinel.shield

import android.net.Uri
import android.os.Bundle
import android.util.Log
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import com.sentinel.shield.ui.theme.SentinelShieldTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        logIncomingApk(intent?.data)

        setContent {
            SentinelShieldTheme {
                Scaffold(modifier = Modifier.fillMaxSize()) { innerPadding ->
                    Greeting(
                        name = "Android",
                        modifier = Modifier.padding(innerPadding)
                    )
                }
            }
        }
    }
    private fun logIncomingApk(uri: Uri?) {
        if (uri == null) {
            Log.d("Sentinel", "launched from launcher icon (no uri)")
            return
        }
        Log.d("Sentinel", "intercepted URI: $uri")
        try {
            contentResolver.openInputStream(uri)?.use { stream ->
                val bytes = stream.readBytes()
                Log.d("Sentinel", "read ${bytes.size} bytes, zip magic=${bytes.take(2).map { it.toInt() }}")
            }
        } catch (e: Exception) {
            Log.e("Sentinel", "failed reading stream: ${e.message}")
        }
    }
}

@Composable
fun Greeting(name: String, modifier: Modifier = Modifier) {
    Text(
        text = "Hello $name!",
        modifier = modifier
    )
}

@Preview(showBackground = true)
@Composable
fun GreetingPreview() {
    SentinelShieldTheme {
        Greeting("Android")
    }
}