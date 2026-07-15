package ir.acdevixa.devixa.web;

import android.net.Uri;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebView;

import java.util.Objects;

public final class DevixaWebChromeClient extends WebChromeClient {
    public interface FileChooserDelegate {
        boolean open(ValueCallback<Uri[]> callback, FileChooserParams params);
    }

    public interface ProgressDelegate {
        void onProgressChanged(int progress);
    }

    private final FileChooserDelegate fileChooserDelegate;
    private final ProgressDelegate progressDelegate;

    public DevixaWebChromeClient(
            FileChooserDelegate fileChooserDelegate,
            ProgressDelegate progressDelegate
    ) {
        this.fileChooserDelegate = Objects.requireNonNull(fileChooserDelegate);
        this.progressDelegate = Objects.requireNonNull(progressDelegate);
    }

    @Override
    public void onProgressChanged(WebView view, int newProgress) {
        progressDelegate.onProgressChanged(newProgress);
    }

    @Override
    public boolean onShowFileChooser(
            WebView webView,
            ValueCallback<Uri[]> filePathCallback,
            FileChooserParams fileChooserParams
    ) {
        return fileChooserDelegate.open(filePathCallback, fileChooserParams);
    }
}
