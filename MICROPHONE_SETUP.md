# 🎤 Microphone Access Setup Guide

## The Problem

Docker containers **cannot directly access the host microphone** on macOS due to security restrictions. Your carnatic.html was trying to use server-side audio processing, which fails in containerized environments.

## ✅ Solution: Client-Side Audio Processing

I've fixed your application to use **client-side audio processing** with the Web Audio API, which works perfectly in Docker containers.

## 🚀 Quick Start

### Option 1: HTTP (Local Testing Only)

```bash
docker-compose up
# Access: http://localhost:3001
# Note: Microphone may not work due to browser security
```

### Option 2: HTTPS (Recommended for Microphone)

```bash
# Generate SSL certificates and run with HTTPS
python3 ssl_app.py
# Access: https://localhost:5000
# Accept the self-signed certificate warning
```

### Option 3: Standalone (No Docker)

```bash
# Direct microphone access, no container limitations
python3 standalone_carnatic.py
```

## 🔧 Technical Changes Made

### ✅ Fixed carnatic.html

- **Before**: Server-side audio processing (failed in Docker)
- **After**: Client-side Web Audio API processing
- **Result**: Microphone works in browser, not limited by Docker

### ✅ Fixed app.py

- Removed server-side audio stream handling
- Added client-side processing support
- Added HTTPS guidance

### ✅ Enhanced Docker Setup

- Added SSL support configuration
- Client-side processing labels
- Proper port mapping for HTTPS

## 🌐 Browser Requirements

### Microphone Access Requires

1. **HTTPS** (required by modern browsers)
2. **User Permission** (microphone access prompt)
3. **Secure Context** (localhost or valid SSL certificate)

### Browser Support

- ✅ Chrome 66+ (recommended)
- ✅ Firefox 60+
- ✅ Safari 11.1+
- ✅ Edge 79+

## 📱 Mobile Testing

For mobile device testing:

```bash
# 1. Get your local IP
ifconfig | grep inet | grep 192.168

# 2. Run HTTPS server
python3 ssl_app.py

# 3. Access from mobile
https://[YOUR_IP]:5000

# 4. Accept certificate warning
```

## 🎵 Features Now Working

### In Browser (Client-Side)

- ✅ Real-time microphone access
- ✅ Carnatic shruti detection
- ✅ Devanagari display
- ✅ Interactive shruti scale
- ✅ Session analytics
- ✅ Raga context analysis

### In Docker Container

- ✅ Web interface serving
- ✅ Static file hosting
- ✅ WebSocket coordination
- ✅ API endpoints
- ❌ Direct microphone access (not needed anymore)

## 🔍 Troubleshooting

### Microphone Not Working?

1. **Check HTTPS**: Use `https://localhost:5000` not `http://`
2. **Allow Permissions**: Click "Allow" when browser asks for microphone
3. **Check Browser Settings**: Ensure microphone isn't blocked for the site
4. **Try Different Browser**: Chrome usually has best Web Audio API support

### Certificate Warnings?

- Self-signed certificates show warnings
- Click "Advanced" → "Proceed to localhost (unsafe)"
- This is normal for local development

### Still Having Issues?

Use the standalone script:

```bash
python3 standalone_carnatic.py
```

This bypasses all Docker/browser limitations.

## 🎯 Architecture Summary

```
Browser (Client-Side)          Docker Container (Server-Side)
┌─────────────────────┐       ┌─────────────────────┐
│ 🎤 Microphone       │       │ 🌐 Web Server       │
│ 🔊 Web Audio API    │  ←→   │ 📡 WebSocket        │
│ 🎵 Shruti Detection │       │ 📊 API Endpoints    │
│ 🎨 UI Rendering     │       │ 📁 Static Files     │
└─────────────────────┘       └─────────────────────┘
```

**Key Insight**: Audio processing happens in the browser, Docker just serves the web interface!
