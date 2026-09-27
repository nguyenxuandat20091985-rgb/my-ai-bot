package vn.facebookad.app;

import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import androidx.appcompat.app.AppCompatActivity;

public class MainActivity extends AppCompatActivity {
    private static final String APP_URL =
            "https://nguyenxuandat20091985-rgb.github.io/my-ai-bot/facebook-ad/";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        openWebApp();
        finish();
    }

    private void openWebApp() {
        Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(APP_URL));
        startActivity(intent);
    }
}
