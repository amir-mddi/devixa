package ir.acdevixa.devixa.ui;

import android.content.Context;
import android.graphics.Color;
import android.graphics.Typeface;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

import ir.acdevixa.devixa.R;
import ir.acdevixa.devixa.config.AppConfig;

public final class ConnectionErrorView extends LinearLayout {
    public ConnectionErrorView(Context context, Runnable retryAction) {
        super(context);
        setOrientation(VERTICAL);
        setGravity(Gravity.CENTER);
        setPadding(dp(28), dp(28), dp(28), dp(28));
        setBackgroundColor(AppConfig.BACKGROUND_COLOR);
        setVisibility(View.GONE);
        setLayoutDirection(View.LAYOUT_DIRECTION_RTL);

        TextView title = new TextView(context);
        title.setText(R.string.connection_error_title);
        title.setTextColor(Color.WHITE);
        title.setTextSize(22);
        title.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        title.setGravity(Gravity.CENTER);
        addView(title, matchWrap(dp(12)));

        TextView description = new TextView(context);
        description.setText(R.string.connection_error);
        description.setTextColor(0xFFCBD5E1);
        description.setTextSize(15);
        description.setGravity(Gravity.CENTER);
        description.setLineSpacing(0, 1.35f);
        addView(description, matchWrap(dp(24)));

        Button retryButton = new Button(context);
        retryButton.setText(R.string.retry);
        retryButton.setTextColor(Color.WHITE);
        retryButton.setTextSize(15);
        retryButton.setAllCaps(false);
        retryButton.setBackgroundTintList(android.content.res.ColorStateList.valueOf(AppConfig.ACCENT_COLOR));
        retryButton.setMinHeight(dp(48));
        retryButton.setOnClickListener(ignored -> retryAction.run());
        LayoutParams buttonParams = new LayoutParams(dp(180), dp(52));
        addView(retryButton, buttonParams);
    }

    private LayoutParams matchWrap(int bottomMargin) {
        LayoutParams params = new LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.WRAP_CONTENT);
        params.bottomMargin = bottomMargin;
        return params;
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }
}
