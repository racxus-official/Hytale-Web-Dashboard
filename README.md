# Hytale Web Dashboard (FREE Version)

A modern, portable, and cross-platform web interface designed to manage and monitor your Hytale Server. 

---

## 🐧 Platform Origins
This project was **originally developed on Linux**. While it is fully compatible with Windows, it maintains a Linux-first logic for stability and performance. If you encounter Windows-specific issues, please follow the contact instructions below.

## ✨ Features
- **Cross-Platform**: Native support for Linux (`.sh`) and Windows (`.bat`).
- **Real-time Monitoring**: Track normalized CPU usage (0-100%), RAM consumption, and online players.
- **Portable Design**: No hardcoded paths. The dashboard automatically syncs its configuration to its current folder location every time it starts.
- **Integrated Launcher**: Fully supports official Hytale staged updates, AOT cache, and asset management.
- **Web Console**: Send commands and read server logs directly from your browser.

## 🚀 How to Install & Run

### Prerequisites
- **Python 3.x**: Ensure Python is installed and added to your system PATH.
- **Java**: Required to run the actual Hytale Server jar.

### 🐧 Linux Setup
1. Clone the repository to your server.
2. Place your `Server/` folder and `Assets.zip` in the root directory of this project.
3. Run the launcher:
   ```bash
   bash start_dashboard.sh
🪟 Windows Setup
Download or clone the project.

Place your Server/ folder and Assets.zip in the root directory.

Double-click the start_dashboard.bat file.

The script will automatically create a virtual environment (venv) and install all necessary Python dependencies (Flask, psutil, etc.).

The dashboard will automatically open at http://localhost:5000 once initialized.

### contact me via instagram @racxus tks
