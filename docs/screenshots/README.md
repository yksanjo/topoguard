# Screenshots Directory

This directory contains screenshots of the TopoGuard user interface.

## How to Generate Screenshots

1. Start the TopoGuard server:
   ```bash
   uvicorn api.main:app --reload --port 8000
   ```

2. Generate sample data:
   ```bash
   python scripts/generate_sample_data.py --transactions 1000
   python scripts/run_detection.py --input data/sample_transactions.json
   ```

3. Open the dashboard in your browser:
   ```
   http://localhost:8000
   ```

4. Capture screenshots using one of these methods:

   **Method 1: Browser DevTools**
   - Press F12 to open DevTools
   - Press Cmd+Shift+P (Mac) or Ctrl+Shift+P (Windows)
   - Type "screenshot" and select "Capture full size screenshot"

   **Method 2: Automated with Playwright**
   ```bash
   pip install playwright
   playwright install chromium
   python scripts/capture_screenshots.py
   ```

   **Method 3: Manual Screenshot Tools**
   - Mac: Cmd+Shift+4 for selection, Cmd+Shift+3 for full screen
   - Windows: Snipping Tool or Win+Shift+S
   - Linux: Use screenshot tool (e.g., Flameshot, GNOME Screenshot)

## Required Screenshots

- `dashboard.png` - Main dashboard overview
- `dashboard-overview.png` - Full dashboard with all panels
- `persistence-diagram.png` - 3D persistence diagram visualization
- `transaction-graph.png` - Transaction network graph
- `alerts-panel.png` - Recent alerts panel
- `topological-features.png` - Topological features panel
- `transaction-details.png` - Transaction detail modal
- `api-docs.png` - API documentation interface

## Screenshot Guidelines

- **Resolution**: Minimum 1920x1080 for desktop, 1280x720 for mobile
- **Format**: PNG with transparency where applicable
- **Naming**: Use kebab-case (e.g., `dashboard-overview.png`)
- **Annotations**: Add arrows or highlights to point out key features
- **Privacy**: Redact any sensitive data before committing




