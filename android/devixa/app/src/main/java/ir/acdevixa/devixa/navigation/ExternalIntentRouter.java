package ir.acdevixa.devixa.navigation;

import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.net.Uri;
import android.widget.Toast;

import java.util.Arrays;
import java.util.Collections;
import java.util.HashSet;
import java.util.Locale;
import java.util.Set;

import ir.acdevixa.devixa.R;

public final class ExternalIntentRouter {
    private static final Set<String> ALLOWED_SCHEMES = Collections.unmodifiableSet(
            new HashSet<>(Arrays.asList(
                    "http",
                    "https",
                    "mailto",
                    "tel",
                    "sms",
                    "tg"
            ))
    );

    private final Activity activity;

    public ExternalIntentRouter(Activity activity) {
        this.activity = activity;
    }

    public void open(Uri uri) {
        if (uri == null || uri.getScheme() == null) {
            showError();
            return;
        }

        String scheme = uri.getScheme().toLowerCase(Locale.ROOT);
        if (!ALLOWED_SCHEMES.contains(scheme)) {
            showError();
            return;
        }

        Intent intent = new Intent(Intent.ACTION_VIEW, uri)
                .addCategory(Intent.CATEGORY_BROWSABLE);

        try {
            activity.startActivity(intent);
        } catch (ActivityNotFoundException | SecurityException exception) {
            showError();
        }
    }

    private void showError() {
        Toast.makeText(activity, R.string.external_link_error, Toast.LENGTH_SHORT).show();
    }
}
