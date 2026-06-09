package com.aliqr;

import android.Manifest;
import android.app.Activity;
import android.app.AlertDialog;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.ImageFormat;
import android.hardware.Camera;
import android.os.Bundle;
import android.os.Handler;
import android.os.Vibrator;
import android.view.SurfaceHolder;
import android.view.SurfaceView;
import android.view.View;
import android.widget.ImageView;
import android.widget.TextView;
import android.widget.Toast;

import com.google.zxing.BarcodeFormat;
import com.google.zxing.BinaryBitmap;
import com.google.zxing.DecodeHintType;
import com.google.zxing.MultiFormatReader;
import com.google.zxing.NotFoundException;
import com.google.zxing.PlanarYUVLuminanceSource;
import com.google.zxing.Result;
import com.google.zxing.common.GlobalHistogramBinarizer;
import com.google.zxing.common.HybridBinarizer;

import java.io.IOException;
import java.util.Arrays;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;

@SuppressWarnings("deprecation")
public class MainActivity extends Activity implements SurfaceHolder.Callback, Camera.PreviewCallback {

    private static final int CAMERA_PERMISSION_REQUEST = 100;
    private static final long AUTOFOCUS_INTERVAL = 2000;

    private SurfaceView surfaceView;
    private SurfaceHolder surfaceHolder;
    private Camera camera;
    private TextView tvStatus;
    private ImageView btnFlash;
    private MultiFormatReader reader;
    private AdManager adManager;  // Reklam yöneticisi
    private boolean flashOn = false;
    private volatile boolean scanning = true;
    private boolean surfaceReady = false;
    private Handler handler = new Handler();
    private int previewWidth, previewHeight;

    private final Runnable autofocusRunnable = new Runnable() {
        @Override
        public void run() {
            if (camera != null && scanning) {
                try { camera.autoFocus(null); } catch (Exception ignored) {}
            }
            handler.postDelayed(this, AUTOFOCUS_INTERVAL);
        }
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        surfaceView = (SurfaceView) findViewById(R.id.camera_preview);
        tvStatus = (TextView) findViewById(R.id.tv_status);
        btnFlash = (ImageView) findViewById(R.id.btn_flash);

        Map<DecodeHintType, Object> hints = new EnumMap<>(DecodeHintType.class);
        hints.put(DecodeHintType.TRY_HARDER, Boolean.TRUE);
        hints.put(DecodeHintType.POSSIBLE_FORMATS, Arrays.asList(
            BarcodeFormat.QR_CODE, BarcodeFormat.DATA_MATRIX,
            BarcodeFormat.AZTEC, BarcodeFormat.PDF_417,
            BarcodeFormat.CODE_128, BarcodeFormat.EAN_13
        ));
        reader = new MultiFormatReader();
        reader.setHints(hints);

        // Reklamı başlat
        adManager = new AdManager(this);
        adManager.initialize();

        surfaceHolder = surfaceView.getHolder();
        surfaceHolder.addCallback(this);
        surfaceHolder.setType(SurfaceHolder.SURFACE_TYPE_PUSH_BUFFERS);

        btnFlash.setOnClickListener(v -> toggleFlash());

        checkCameraPermission();
    }

    private void checkCameraPermission() {
        if (checkSelfPermission(Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.CAMERA}, CAMERA_PERMISSION_REQUEST);
        }
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        if (requestCode == CAMERA_PERMISSION_REQUEST) {
            if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                if (surfaceReady) startCamera();
            } else {
                new AlertDialog.Builder(this)
                    .setTitle("Kamera İzni Gerekli")
                    .setMessage("Ali QR, QR kod okuyabilmek için kamera iznine ihtiyaç duyuyor.")
                    .setPositiveButton("İzin Ver", (d, w) -> checkCameraPermission())
                    .setNegativeButton("İptal", null)
                    .show();
            }
        }
    }

    private void startCamera() {
        if (camera != null) return;
        try {
            camera = Camera.open();
            Camera.Parameters params = camera.getParameters();

            List<String> focusModes = params.getSupportedFocusModes();
            if (focusModes != null) {
                if (focusModes.contains(Camera.Parameters.FOCUS_MODE_CONTINUOUS_PICTURE))
                    params.setFocusMode(Camera.Parameters.FOCUS_MODE_CONTINUOUS_PICTURE);
                else if (focusModes.contains(Camera.Parameters.FOCUS_MODE_AUTO)) {
                    params.setFocusMode(Camera.Parameters.FOCUS_MODE_AUTO);
                    handler.postDelayed(autofocusRunnable, AUTOFOCUS_INTERVAL);
                }
            }

            params.setPreviewFormat(ImageFormat.NV21);
            Camera.Size bestSize = getBestPreviewSize(params);
            if (bestSize != null) {
                params.setPreviewSize(bestSize.width, bestSize.height);
                previewWidth = bestSize.width;
                previewHeight = bestSize.height;
            }

            List<String> sceneModes = params.getSupportedSceneModes();
            if (sceneModes != null && sceneModes.contains(Camera.Parameters.SCENE_MODE_BARCODE))
                params.setSceneMode(Camera.Parameters.SCENE_MODE_BARCODE);

            camera.setParameters(params);
            camera.setDisplayOrientation(90);
            camera.setPreviewCallback(this);

            try {
                camera.setPreviewDisplay(surfaceHolder);
                camera.startPreview();
            } catch (IOException e) {
                releaseCamera();
            }
        } catch (Exception e) {
            Toast.makeText(this, "Kamera açılamadı", Toast.LENGTH_SHORT).show();
        }
    }

    private Camera.Size getBestPreviewSize(Camera.Parameters params) {
        List<Camera.Size> sizes = params.getSupportedPreviewSizes();
        Camera.Size best = null;
        for (Camera.Size size : sizes) {
            if (size.width >= 640 && size.width <= 1280) {
                if (best == null || size.width > best.width) best = size;
            }
        }
        if (best == null && !sizes.isEmpty()) best = sizes.get(0);
        return best;
    }

    private void toggleFlash() {
        if (camera == null) return;
        try {
            Camera.Parameters params = camera.getParameters();
            List<String> flashModes = params.getSupportedFlashModes();
            if (flashModes == null || !flashModes.contains(Camera.Parameters.FLASH_MODE_TORCH)) return;
            flashOn = !flashOn;
            params.setFlashMode(flashOn ? Camera.Parameters.FLASH_MODE_TORCH : Camera.Parameters.FLASH_MODE_OFF);
            camera.setParameters(params);
        } catch (Exception ignored) {}
    }

    @Override
    public void onPreviewFrame(byte[] data, Camera camera) {
        if (!scanning || data == null) return;
        try {
            Result result = tryDecode(data, previewWidth, previewHeight);
            if (result == null) {
                byte[] rotated = rotateYUV90(data, previewWidth, previewHeight);
                result = tryDecode(rotated, previewHeight, previewWidth);
            }
            if (result != null) {
                scanning = false;
                final String text = result.getText();
                final String format = result.getBarcodeFormat().toString();

                Vibrator v = (Vibrator) getSystemService(VIBRATOR_SERVICE);
                if (v != null) v.vibrate(150);

                handler.post(() -> {
                    // Önce reklam göster, sonra sonuç ekranına geç
                    adManager.showAdIfReady(() -> {
                        Intent intent = new Intent(MainActivity.this, ResultActivity.class);
                        intent.putExtra("result", text);
                        intent.putExtra("format", format);
                        startActivity(intent);
                    });
                });
            }
        } catch (Exception ignored) {}
    }

    private Result tryDecode(byte[] data, int width, int height) {
        PlanarYUVLuminanceSource source = new PlanarYUVLuminanceSource(
            data, width, height, 0, 0, width, height, false);
        try {
            Result r = reader.decodeWithState(new BinaryBitmap(new HybridBinarizer(source)));
            if (r != null) return r;
        } catch (NotFoundException ignored) {
        } finally { reader.reset(); }
        try {
            Result r = reader.decodeWithState(new BinaryBitmap(new GlobalHistogramBinarizer(source)));
            if (r != null) return r;
        } catch (NotFoundException ignored) {
        } finally { reader.reset(); }
        return null;
    }

    private byte[] rotateYUV90(byte[] data, int width, int height) {
        byte[] output = new byte[data.length];
        int ySize = width * height;
        for (int y = 0; y < height; y++)
            for (int x = 0; x < width; x++)
                output[x * height + (height - y - 1)] = data[y * width + x];
        int uvW = width / 2, uvH = height / 2;
        for (int y = 0; y < uvH; y++) {
            for (int x = 0; x < uvW; x++) {
                int s = ySize + y * width + x * 2;
                int d = ySize + x * height + (uvH - y - 1) * 2;
                if (s + 1 < data.length && d + 1 < output.length) {
                    output[d] = data[s];
                    output[d + 1] = data[s + 1];
                }
            }
        }
        return output;
    }

    @Override
    protected void onResume() {
        super.onResume();
        scanning = true;
        if (surfaceReady && checkSelfPermission(Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED)
            startCamera();
    }

    @Override
    protected void onPause() {
        super.onPause();
        handler.removeCallbacks(autofocusRunnable);
        releaseCamera();
    }

    private void releaseCamera() {
        if (camera != null) {
            camera.setPreviewCallback(null);
            camera.stopPreview();
            camera.release();
            camera = null;
        }
    }

    @Override public void surfaceCreated(SurfaceHolder h) {
        surfaceReady = true;
        if (checkSelfPermission(Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED)
            startCamera();
        else checkCameraPermission();
    }
    @Override public void surfaceChanged(SurfaceHolder h, int f, int w, int hh) {
        if (camera != null) {
            try { camera.stopPreview(); camera.setPreviewDisplay(h); camera.startPreview(); }
            catch (IOException ignored) {}
        }
    }
    @Override public void surfaceDestroyed(SurfaceHolder h) { surfaceReady = false; releaseCamera(); }
}
