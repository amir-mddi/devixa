package ir.acdevixa.devixa.config;

import android.net.Uri;

import java.util.Arrays;
import java.util.Collections;
import java.util.HashSet;
import java.util.Set;

import ir.acdevixa.devixa.BuildConfig;

public final class AppConfig {
    public static final Uri HOME_URI = Uri.parse("https://acdevixa.ir/");
    public static final int FILE_CHOOSER_REQUEST_CODE = 1001;
    public static final int BACKGROUND_COLOR = 0xFF070B14;
    public static final int ACCENT_COLOR = 0xFF5B4CF6;

    public static final Set<String> TRUSTED_EXACT_HOSTS = immutableSet(
            "acdevixa.ir",
            "www.acdevixa.ir",
            "github.com",
            "accounts.google.com",
            "google.com"
    );

    public static final Set<String> TRUSTED_HOST_SUFFIXES = immutableSet(
            ".acdevixa.ir",
            ".github.com",
            ".google.com",
            ".googleusercontent.com"
    );

    private AppConfig() {
        throw new IllegalStateException("Utility class");
    }

    public static String userAgentSuffix() {
        return " DevixaAndroid/" + BuildConfig.VERSION_NAME;
    }

    private static Set<String> immutableSet(String... values) {
        return Collections.unmodifiableSet(new HashSet<>(Arrays.asList(values)));
    }
}
