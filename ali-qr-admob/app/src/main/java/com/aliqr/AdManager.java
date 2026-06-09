package com.aliqr;

import android.app.Activity;
import android.content.Context;

import com.google.android.gms.ads.AdError;
import com.google.android.gms.ads.AdRequest;
import com.google.android.gms.ads.FullScreenContentCallback;
import com.google.android.gms.ads.LoadAdError;
import com.google.android.gms.ads.MobileAds;
import com.google.android.gms.ads.interstitial.InterstitialAd;
import com.google.android.gms.ads.interstitial.InterstitialAdLoadCallback;

/**
 * ADIM 2: Aşağıdaki AD_UNIT_ID'yi kendi değerinle değiştir
 *
 * admob.google.com > Uygulamalar > Uygulama > Reklam Birimleri
 * "Geçiş Reklamı" (Interstitial) oluştur > Ad Unit ID kopyala
 *
 * Test ID (şu an aktif): ca-app-pub-3940256099942544/1033173712
 * Gerçek ID formatı:     ca-app-pub-XXXXXXXXXXXXXXXX/YYYYYYYYYY
 */
public class AdManager {

    // ============================================================
    // BURAYA KEND AD UNIT ID'NI YAZ
    // Test için bu ID'yi bırakabilirsin, canlıya geçince değiştir
    private static final String AD_UNIT_ID = "ca-app-pub-3940256099942544/1033173712";
    // ============================================================

    private InterstitialAd interstitialAd;
    private final Activity activity;
    private boolean initialized = false;

    public AdManager(Activity activity) {
        this.activity = activity;
    }

    public void initialize() {
        MobileAds.initialize(activity, initializationStatus -> {
            initialized = true;
            loadAd();
        });
    }

    public void loadAd() {
        AdRequest adRequest = new AdRequest.Builder().build();
        InterstitialAd.load(activity, AD_UNIT_ID, adRequest, new InterstitialAdLoadCallback() {
            @Override
            public void onAdLoaded(InterstitialAd ad) {
                interstitialAd = ad;
                setupCallbacks();
            }

            @Override
            public void onAdFailedToLoad(LoadAdError error) {
                interstitialAd = null;
            }
        });
    }

    private void setupCallbacks() {
        if (interstitialAd == null) return;
        interstitialAd.setFullScreenContentCallback(new FullScreenContentCallback() {
            @Override
            public void onAdDismissedFullScreenContent() {
                interstitialAd = null;
                loadAd(); // Bir sonraki QR için hemen yükle
            }

            @Override
            public void onAdFailedToShowFullScreenContent(AdError error) {
                interstitialAd = null;
                loadAd();
            }
        });
    }

    /** Her QR okuma sonrasında çağır. Reklam hazırsa gösterir. */
    public void showAdIfReady(Runnable onFinished) {
        if (interstitialAd != null) {
            interstitialAd.setFullScreenContentCallback(new FullScreenContentCallback() {
                @Override
                public void onAdDismissedFullScreenContent() {
                    interstitialAd = null;
                    loadAd();
                    if (onFinished != null) onFinished.run();
                }

                @Override
                public void onAdFailedToShowFullScreenContent(AdError error) {
                    interstitialAd = null;
                    loadAd();
                    if (onFinished != null) onFinished.run();
                }
            });
            interstitialAd.show(activity);
        } else {
            // Reklam henüz hazır değilse direkt geç
            if (onFinished != null) onFinished.run();
            loadAd();
        }
    }

    public boolean isAdReady() {
        return interstitialAd != null;
    }
}
