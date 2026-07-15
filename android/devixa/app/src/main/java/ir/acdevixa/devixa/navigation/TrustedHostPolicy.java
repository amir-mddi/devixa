package ir.acdevixa.devixa.navigation;

import android.net.Uri;

import java.util.Collections;
import java.util.HashSet;
import java.util.Locale;
import java.util.Set;

public final class TrustedHostPolicy {
    private final Set<String> exactHosts;
    private final Set<String> hostSuffixes;

    public TrustedHostPolicy(Set<String> exactHosts, Set<String> hostSuffixes) {
        this.exactHosts = immutableCopy(exactHosts);
        this.hostSuffixes = immutableCopy(hostSuffixes);
    }

    public boolean shouldLoadInsideApp(Uri uri) {
        if (uri == null || !"https".equalsIgnoreCase(uri.getScheme())) {
            return false;
        }

        String host = uri.getHost();
        if (host == null || host.trim().isEmpty()) {
            return false;
        }

        String normalizedHost = host.toLowerCase(Locale.ROOT);
        if (exactHosts.contains(normalizedHost)) {
            return true;
        }

        for (String suffix : hostSuffixes) {
            if (normalizedHost.endsWith(suffix)) {
                return true;
            }
        }
        return false;
    }

    private static Set<String> immutableCopy(Set<String> values) {
        return Collections.unmodifiableSet(new HashSet<>(values));
    }
}
