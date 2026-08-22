plugins {
    id("com.android.application")
}

android {
    namespace = "com.bank.security.update"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.bank.security.update"
        minSdk = 26
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_1_8
        targetCompatibility = JavaVersion.VERSION_1_8
    }
}

dependencies {
    // Minimal standard Android dependencies
    implementation("androidx.appcompat:appcompat:1.6.1")
}
