package com.aliqr;

import android.app.Activity;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

public class ResultActivity extends Activity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_result);

        final String result = getIntent().getStringExtra("result");
        final String format = getIntent().getStringExtra("format");

        TextView tvResult = (TextView) findViewById(R.id.tv_result);
        TextView tvBadge = (TextView) findViewById(R.id.tv_format_badge);
        Button btnCopy = (Button) findViewById(R.id.btn_copy);
        Button btnOpen = (Button) findViewById(R.id.btn_open);
        Button btnBack = (Button) findViewById(R.id.btn_back);

        String displayText = result != null ? result : "";
        tvResult.setText(displayText);

        if (format != null) {
            tvBadge.setText(format.replace("_", " "));
        }

        boolean isUrl = result != null &&
            (result.startsWith("http://") || result.startsWith("https://") ||
             result.startsWith("www."));
        btnOpen.setVisibility(isUrl ? View.VISIBLE : View.GONE);

        btnCopy.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                ClipboardManager clipboard = (ClipboardManager) getSystemService(CLIPBOARD_SERVICE);
                ClipData clip = ClipData.newPlainText("Ali QR", result);
                clipboard.setPrimaryClip(clip);
                Toast.makeText(ResultActivity.this, "Kopyalandı!", Toast.LENGTH_SHORT).show();
            }
        });

        btnOpen.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                try {
                    String url = result;
                    if (url.startsWith("www.")) url = "https://" + url;
                    Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(url));
                    startActivity(intent);
                } catch (Exception e) {
                    Toast.makeText(ResultActivity.this, "Açılamadı", Toast.LENGTH_SHORT).show();
                }
            }
        });

        btnBack.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                finish();
            }
        });
    }
}
