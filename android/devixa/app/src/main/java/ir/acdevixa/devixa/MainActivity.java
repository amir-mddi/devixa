package ir.acdevixa.devixa;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.webkit.CookieManager;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.widget.FrameLayout;
import android.widget.ProgressBar;
import android.widget.Toast;

import ir.acdevixa.devixa.config.AppConfig;
import ir.acdevixa.devixa.navigation.ExternalIntentRouter;
import ir.acdevixa.devixa.navigation.TrustedHostPolicy;
import ir.acdevixa.devixa.ui.ConnectionErrorView;
import ir.acdevixa.devixa.web.DevixaWebChromeClient;
import ir.acdevixa.devixa.web.DevixaWebViewClient;

public final class MainActivity extends Activity {
    private WebView webView;
    private ProgressBar progressBar;
    private ConnectionErrorView connectionErrorView;
    private ValueCallback<Uri[]> pendingFileCallback;
    private TrustedHostPolicy trustedHostPolicy;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        getWindow().setStatusBarColor(AppConfig.BACKGROUND_COLOR);
        getWindow().setNavigationBarColor(AppConfig.BACKGROUND_COLOR);

        trustedHostPolicy = new TrustedHostPolicy(
                AppConfig.TRUSTED_EXACT_HOSTS,
                AppConfig.TRUSTED_HOST_SUFFIXES
        );

        progressBar = createProgressBar();
        webView = createWebView();
        connectionErrorView = new ConnectionErrorView(this, this::retryCurrentPage);
        setContentView(createRoot());
        registerModernBackHandler();

        if (savedInstanceState == null || webView.restoreState(savedInstanceState) == null) {
            loadInitialUri(getIntent());
        }
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        loadInitialUri(intent);
    }

    @SuppressWarnings("deprecation")
    @Override
    public void onBackPressed() {
        if (!handleBackNavigation()) {
            super.onBackPressed();
        }
    }

    @Override
    protected void onSaveInstanceState(Bundle outState) {
        if (webView != null) {
            webView.saveState(outState);
        }
        super.onSaveInstanceState(outState);
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (webView != null) {
            webView.onResume();
            webView.resumeTimers();
        }
    }

    @Override
    protected void onPause() {
        CookieManager.getInstance().flush();
        if (webView != null) {
            webView.onPause();
            webView.pauseTimers();
        }
        super.onPause();
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        if (requestCode == AppConfig.FILE_CHOOSER_REQUEST_CODE) {
            if (pendingFileCallback != null) {
                pendingFileCallback.onReceiveValue(
                        WebChromeClient.FileChooserParams.parseResult(resultCode, data)
                );
                pendingFileCallback = null;
            }
            return;
        }
        super.onActivityResult(requestCode, resultCode, data);
    }

    @Override
    protected void onDestroy() {
        if (pendingFileCallback != null) {
            pendingFileCallback.onReceiveValue(null);
            pendingFileCallback = null;
        }
        if (webView != null) {
            webView.stopLoading();
            webView.loadUrl("about:blank");
            webView.clearHistory();
            webView.removeAllViews();
            webView.setWebChromeClient(null);
            webView.setWebViewClient(null);
            webView.destroy();
            webView = null;
        }
        super.onDestroy();
    }

    private FrameLayout createRoot() {
        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(AppConfig.BACKGROUND_COLOR);
        root.addView(webView, matchParentParams());
        root.addView(connectionErrorView, matchParentParams());
        root.addView(progressBar);
        return root;
    }

    private FrameLayout.LayoutParams matchParentParams() {
        return new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT
        );
    }

    private ProgressBar createProgressBar() {
        ProgressBar bar = new ProgressBar(
                this,
                null,
                android.R.attr.progressBarStyleHorizontal
        );
        bar.setMax(100);
        bar.setIndeterminate(false);
        bar.setProgress(0);
        bar.setProgressTintList(android.content.res.ColorStateList.valueOf(AppConfig.ACCENT_COLOR));
        bar.setBackgroundTintList(android.content.res.ColorStateList.valueOf(Color.TRANSPARENT));

        FrameLayout.LayoutParams params = new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                dpToPx(3)
        );
        params.gravity = Gravity.TOP;
        bar.setLayoutParams(params);
        return bar;
    }

    private WebView createWebView() {
        WebView view = new WebView(this);
        WebSettings settings = view.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setLoadWithOverviewMode(true);
        settings.setUseWideViewPort(true);
        settings.setSupportZoom(false);
        settings.setBuiltInZoomControls(false);
        settings.setDisplayZoomControls(false);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(false);
        settings.setAllowFileAccessFromFileURLs(false);
        settings.setAllowUniversalAccessFromFileURLs(false);
        settings.setJavaScriptCanOpenWindowsAutomatically(false);
        settings.setSupportMultipleWindows(false);
        settings.setGeolocationEnabled(false);
        settings.setMediaPlaybackRequiresUserGesture(true);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        settings.setCacheMode(WebSettings.LOAD_DEFAULT);
        settings.setDefaultTextEncodingName("UTF-8");
        settings.setTextZoom(100);
        settings.setUserAgentString(settings.getUserAgentString() + AppConfig.userAgentSuffix());

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            settings.setSafeBrowsingEnabled(true);
        }

        CookieManager cookieManager = CookieManager.getInstance();
        cookieManager.setAcceptCookie(true);
        // OAuth providers may require third-party cookies during authentication.
        cookieManager.setAcceptThirdPartyCookies(view, true);

        WebView.setWebContentsDebuggingEnabled(BuildConfig.DEBUG);

        ExternalIntentRouter externalIntentRouter = new ExternalIntentRouter(this);
        view.setWebViewClient(new DevixaWebViewClient(
                trustedHostPolicy,
                externalIntentRouter,
                new DevixaWebViewClient.PageStateDelegate() {
                    @Override
                    public void onLoading() {
                        showLoading();
                    }

                    @Override
                    public void onReady() {
                        showContent();
                    }

                    @Override
                    public void onError() {
                        showConnectionError();
                    }
                }
        ));
        view.setWebChromeClient(new DevixaWebChromeClient(
                this::openFileChooser,
                this::updateProgress
        ));
        view.setDownloadListener((url, userAgent, contentDisposition, mimeType, length) ->
                externalIntentRouter.open(Uri.parse(url))
        );
        return view;
    }

    private void registerModernBackHandler() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            getOnBackInvokedDispatcher().registerOnBackInvokedCallback(
                    android.window.OnBackInvokedDispatcher.PRIORITY_DEFAULT,
                    () -> {
                        if (!handleBackNavigation()) {
                            finish();
                        }
                    }
            );
        }
    }

    private boolean handleBackNavigation() {
        if (connectionErrorView != null && connectionErrorView.getVisibility() == View.VISIBLE) {
            showContent();
            return true;
        }
        if (webView != null && webView.canGoBack()) {
            webView.goBack();
            return true;
        }
        return false;
    }

    private boolean openFileChooser(
            ValueCallback<Uri[]> callback,
            WebChromeClient.FileChooserParams params
    ) {
        if (pendingFileCallback != null) {
            pendingFileCallback.onReceiveValue(null);
        }
        pendingFileCallback = callback;

        try {
            Intent chooserIntent = params.createIntent();
            chooserIntent.addCategory(Intent.CATEGORY_OPENABLE);
            startActivityForResult(
                    chooserIntent,
                    AppConfig.FILE_CHOOSER_REQUEST_CODE
            );
            return true;
        } catch (RuntimeException exception) {
            pendingFileCallback.onReceiveValue(null);
            pendingFileCallback = null;
            Toast.makeText(this, R.string.file_picker_error, Toast.LENGTH_SHORT).show();
            return false;
        }
    }

    private void loadInitialUri(Intent intent) {
        Uri requestedUri = intent == null ? null : intent.getData();
        Uri uri = trustedHostPolicy.shouldLoadInsideApp(requestedUri)
                ? requestedUri
                : AppConfig.HOME_URI;
        showLoading();
        webView.loadUrl(uri.toString());
    }

    private void retryCurrentPage() {
        showLoading();
        String currentUrl = webView.getUrl();
        if (currentUrl == null || currentUrl.trim().isEmpty() || "about:blank".equals(currentUrl)) {
            webView.loadUrl(AppConfig.HOME_URI.toString());
        } else {
            webView.reload();
        }
    }

    private void showLoading() {
        connectionErrorView.setVisibility(View.GONE);
        webView.setVisibility(View.VISIBLE);
        progressBar.setVisibility(View.VISIBLE);
    }

    private void showContent() {
        connectionErrorView.setVisibility(View.GONE);
        webView.setVisibility(View.VISIBLE);
        progressBar.setVisibility(View.GONE);
    }

    private void showConnectionError() {
        progressBar.setVisibility(View.GONE);
        webView.setVisibility(View.INVISIBLE);
        connectionErrorView.setVisibility(View.VISIBLE);
    }

    private void updateProgress(int progress) {
        progressBar.setProgress(progress);
        progressBar.setVisibility(progress >= 100 ? View.GONE : View.VISIBLE);
    }

    private int dpToPx(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }
}
