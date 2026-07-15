package ir.acdevixa.devixa.web;

import android.graphics.Bitmap;
import android.net.Uri;
import android.net.http.SslError;
import android.webkit.SslErrorHandler;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import java.util.Objects;

import ir.acdevixa.devixa.navigation.ExternalIntentRouter;
import ir.acdevixa.devixa.navigation.TrustedHostPolicy;

public final class DevixaWebViewClient extends WebViewClient {
    public interface PageStateDelegate {
        void onLoading();

        void onReady();

        void onError();
    }

    private final TrustedHostPolicy trustedHostPolicy;
    private final ExternalIntentRouter externalIntentRouter;
    private final PageStateDelegate pageStateDelegate;

    public DevixaWebViewClient(
            TrustedHostPolicy trustedHostPolicy,
            ExternalIntentRouter externalIntentRouter,
            PageStateDelegate pageStateDelegate
    ) {
        this.trustedHostPolicy = Objects.requireNonNull(trustedHostPolicy);
        this.externalIntentRouter = Objects.requireNonNull(externalIntentRouter);
        this.pageStateDelegate = Objects.requireNonNull(pageStateDelegate);
    }

    @Override
    public void onPageStarted(WebView view, String url, Bitmap favicon) {
        pageStateDelegate.onLoading();
    }

    @Override
    public void onPageCommitVisible(WebView view, String url) {
        pageStateDelegate.onReady();
    }

    @Override
    public void onPageFinished(WebView view, String url) {
        pageStateDelegate.onReady();
    }

    @Override
    public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
        return route(request.getUrl());
    }

    @SuppressWarnings("deprecation")
    @Override
    public boolean shouldOverrideUrlLoading(WebView view, String url) {
        return route(Uri.parse(url));
    }

    @Override
    public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
        if (request.isForMainFrame()) {
            pageStateDelegate.onError();
        }
    }

    @Override
    public void onReceivedHttpError(
            WebView view,
            WebResourceRequest request,
            WebResourceResponse errorResponse
    ) {
        if (request.isForMainFrame() && errorResponse.getStatusCode() >= 500) {
            pageStateDelegate.onError();
        }
    }

    @Override
    public void onReceivedSslError(WebView view, SslErrorHandler handler, SslError error) {
        handler.cancel();
        pageStateDelegate.onError();
    }

    private boolean route(Uri uri) {
        if (trustedHostPolicy.shouldLoadInsideApp(uri)) {
            return false;
        }

        externalIntentRouter.open(uri);
        return true;
    }
}
