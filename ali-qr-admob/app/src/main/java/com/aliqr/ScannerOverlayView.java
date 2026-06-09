package com.aliqr;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.LinearGradient;
import android.graphics.Paint;
import android.graphics.PorterDuff;
import android.graphics.PorterDuffXfermode;
import android.graphics.RectF;
import android.graphics.Shader;
import android.os.Handler;
import android.util.AttributeSet;
import android.view.View;

public class ScannerOverlayView extends View {

    private static final int CORNER_COLOR = 0xFF00D4FF;
    private static final int OVERLAY_COLOR = 0xBB000000;

    private Paint overlayPaint;
    private Paint holePaint;
    private Paint cornerPaint;
    private Paint linePaint;
    private Paint dotPaint;

    private RectF scanRect;
    private float lineY;
    private boolean lineGoingDown = true;
    private float lineAlpha = 1f;
    private Handler handler = new Handler();
    private float pulseScale = 1f;
    private boolean pulseGrowing = true;

    private final Runnable animRunnable = new Runnable() {
        @Override
        public void run() {
            // Scan line animation
            float speed = 5f;
            if (lineGoingDown) {
                lineY += speed;
                if (scanRect != null && lineY >= scanRect.bottom - 2) lineGoingDown = false;
            } else {
                lineY -= speed;
                if (scanRect != null && lineY <= scanRect.top + 2) lineGoingDown = true;
            }

            // Pulse animation on corners
            float pulseSpeed = 0.015f;
            if (pulseGrowing) {
                pulseScale += pulseSpeed;
                if (pulseScale >= 1.12f) pulseGrowing = false;
            } else {
                pulseScale -= pulseSpeed;
                if (pulseScale <= 0.92f) pulseGrowing = true;
            }

            invalidate();
            handler.postDelayed(this, 14);
        }
    };

    public ScannerOverlayView(Context context) {
        super(context);
        init();
    }

    public ScannerOverlayView(Context context, AttributeSet attrs) {
        super(context, attrs);
        init();
        setLayerType(LAYER_TYPE_SOFTWARE, null);
    }

    private void init() {
        overlayPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        overlayPaint.setColor(OVERLAY_COLOR);

        holePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        holePaint.setXfermode(new PorterDuffXfermode(PorterDuff.Mode.CLEAR));

        cornerPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        cornerPaint.setColor(CORNER_COLOR);
        cornerPaint.setStyle(Paint.Style.STROKE);
        cornerPaint.setStrokeWidth(5f);
        cornerPaint.setStrokeCap(Paint.Cap.ROUND);
        cornerPaint.setStrokeJoin(Paint.Join.ROUND);

        linePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        linePaint.setStrokeWidth(3f);
        linePaint.setStyle(Paint.Style.STROKE);

        dotPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        dotPaint.setColor(CORNER_COLOR);
        dotPaint.setStyle(Paint.Style.FILL);
    }

    @Override
    protected void onSizeChanged(int w, int h, int oldw, int oldh) {
        super.onSizeChanged(w, h, oldw, oldh);
        int size = (int) (Math.min(w, h) * 0.72f);
        int left = (w - size) / 2;
        int top = (int) ((h - size) / 2.3f);
        scanRect = new RectF(left, top, left + size, top + size);
        lineY = scanRect.top;
        handler.removeCallbacks(animRunnable);
        handler.post(animRunnable);
    }

    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        if (scanRect == null) return;

        // Darker top and bottom
        canvas.drawRect(0, 0, getWidth(), scanRect.top, overlayPaint);
        canvas.drawRect(0, scanRect.bottom, getWidth(), getHeight(), overlayPaint);
        canvas.drawRect(0, scanRect.top, scanRect.left, scanRect.bottom, overlayPaint);
        canvas.drawRect(scanRect.right, scanRect.top, getWidth(), scanRect.bottom, overlayPaint);

        // Draw scan line gradient
        if (lineY >= scanRect.top && lineY <= scanRect.bottom) {
            LinearGradient lineGradient = new LinearGradient(
                scanRect.left, lineY, scanRect.right, lineY,
                new int[]{0x0000D4FF, 0xFF00D4FF, 0xFF00FFEE, 0xFF00D4FF, 0x0000D4FF},
                new float[]{0f, 0.2f, 0.5f, 0.8f, 1f},
                Shader.TileMode.CLAMP
            );
            linePaint.setShader(lineGradient);
            canvas.drawLine(scanRect.left + 8, lineY, scanRect.right - 8, lineY, linePaint);

            // Glow below the line
            Paint glowPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
            glowPaint.setStrokeWidth(12f);
            glowPaint.setAlpha(30);
            LinearGradient glowGrad = new LinearGradient(
                scanRect.left, lineY, scanRect.right, lineY,
                new int[]{0x0000D4FF, 0x2000D4FF, 0x0000D4FF},
                null, Shader.TileMode.CLAMP
            );
            glowPaint.setShader(glowGrad);
            canvas.drawLine(scanRect.left + 8, lineY + 6, scanRect.right - 8, lineY + 6, glowPaint);
        }

        // Corner length
        float c = scanRect.width() * 0.12f;
        float r = scanRect.left;
        float t = scanRect.top;
        float ri = scanRect.right;
        float b = scanRect.bottom;
        float rad = 12f;

        // Corner alpha pulse
        int alpha = (int) (200 + 55 * (pulseScale - 0.92f) / 0.2f);
        alpha = Math.min(255, Math.max(180, alpha));
        cornerPaint.setAlpha(alpha);

        // Top-left corner
        canvas.drawLine(r + rad, t, r + c, t, cornerPaint);
        canvas.drawLine(r, t + rad, r, t + c, cornerPaint);
        canvas.drawArc(new RectF(r, t, r + rad * 2, t + rad * 2), 180, 90, false, cornerPaint);

        // Top-right corner
        canvas.drawLine(ri - c, t, ri - rad, t, cornerPaint);
        canvas.drawLine(ri, t + rad, ri, t + c, cornerPaint);
        canvas.drawArc(new RectF(ri - rad * 2, t, ri, t + rad * 2), 270, 90, false, cornerPaint);

        // Bottom-left corner
        canvas.drawLine(r + rad, b, r + c, b, cornerPaint);
        canvas.drawLine(r, b - c, r, b - rad, cornerPaint);
        canvas.drawArc(new RectF(r, b - rad * 2, r + rad * 2, b), 90, 90, false, cornerPaint);

        // Bottom-right corner
        canvas.drawLine(ri - c, b, ri - rad, b, cornerPaint);
        canvas.drawLine(ri, b - c, ri, b - rad, cornerPaint);
        canvas.drawArc(new RectF(ri - rad * 2, b - rad * 2, ri, b), 0, 90, false, cornerPaint);

        // Corner dots
        dotPaint.setAlpha(alpha);
        float dotR = 5f;
        canvas.drawCircle(r, t, dotR, dotPaint);
        canvas.drawCircle(ri, t, dotR, dotPaint);
        canvas.drawCircle(r, b, dotR, dotPaint);
        canvas.drawCircle(ri, b, dotR, dotPaint);
    }

    @Override
    protected void onDetachedFromWindow() {
        super.onDetachedFromWindow();
        handler.removeCallbacks(animRunnable);
    }
}
