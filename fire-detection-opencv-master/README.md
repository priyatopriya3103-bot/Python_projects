# 🔥 Fire Alarm Detection System

A **real-time fire detection system** using computer vision with dual-screen display, visual alerts, and audible alarm. Built with Python and OpenCV.

![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)
![OpenCV](https://img.shields.io/badge/OpenCV-4.5+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## ✨ Features

- 🎥 **Real-time fire detection** using HSV color-based computer vision
- 🖥️ **Dual-window display**:
  - **Window 1**: Live camera feed with fire detection overlay, bounding boxes, and confidence meter
  - **Window 2**: Alarm status display with visual alerts (normal/warning/alarm states)
- 📷 **Multi-camera support** - automatically detects and lets you select from available cameras
- 🔊 **Audio alarm** with looping sound when fire is detected (supports `.m4a` and `.wav`)
- 🎛️ **Configurable detection parameters** - tune sensitivity for your environment
- ⚡ **Real-time FPS display** and performance monitoring

---

## 📦 Installation

### Prerequisites

- Python 3.7 or higher
- Webcam or USB camera

### Install Dependencies

```bash
pip install -r requirements.txt
```

Or install manually:

```bash
pip install opencv-python numpy pygame
```

---

## 🚀 Quick Start

1. **Clone or download** this repository

2. **(Optional)** Add your alarm sound file named `aag_audio.m4a` in the same folder

3. **Run the application**:

   ```bash
   python fire_alarm_system.py
   ```

4. **Select your camera** from the list (auto-selects if only one camera)

5. **Test the detection** by showing fire/flame images on your phone to the camera

---

## 🎮 Controls

| Key | Action                         |
| --- | ------------------------------ |
| `Q` | Quit application               |
| `S` | Toggle alarm sound ON/OFF      |
| `R` | Reset detection and stop alarm |

---

## 🖥️ Display Windows

### Window 1: Camera Feed

- Live video with fire detection overlay
- **Green bounding boxes** around detected fire regions
- **Confidence meter** showing detection strength
- **FPS counter** for performance monitoring
- Status indicator (Normal → Detecting → Alarm)

### Window 2: Alarm Status

- Large visual status display
- **Green checkmark** = System Normal
- **Orange warning** = Fire Detected (confirming...)
- **Red flashing alert** = FIRE ALARM ACTIVE with evacuation message

---

## ⚙️ How It Works

### Fire Detection Algorithm

1. Converts camera frame to **HSV color space**
2. Applies multiple **color range filters** for fire colors:
   - Orange-red flames (H: 0-15)
   - Yellow-orange flames (H: 15-35)
   - Deep red flames (H: 170-180)
3. Uses **morphological operations** to clean up the detection mask
4. Finds **contours** and filters by minimum area
5. Calculates **confidence score** based on fire region size

### Alarm Logic

- Fire must be detected for **consecutive frames** to trigger alarm (reduces false positives)
- Alarm stops after **30 frames** without fire detection (cooldown)
- Sound loops continuously while alarm is active

---

## 🔧 Configuration

Edit these constants in `fire_alarm_system.py` to tune detection:

```python
# Detection sensitivity
FIRE_MIN_AREA = 500          # Minimum contour area (pixels) to consider as fire
CONSECUTIVE_FRAMES = 1       # Frames of detection before triggering alarm
COOLDOWN_FRAMES = 30         # Frames without fire before stopping alarm

# Display settings
DISPLAY_WIDTH = 854          # Camera window width
DISPLAY_HEIGHT = 480         # Camera window height
ALARM_DISPLAY_WIDTH = 600    # Alarm status window width
ALARM_DISPLAY_HEIGHT = 400   # Alarm status window height
```

### HSV Color Ranges

Fire colors can be adjusted in `FIRE_HSV_RANGES`:

```python
FIRE_HSV_RANGES = [
    {'lower': np.array([0, 100, 200]), 'upper': np.array([15, 255, 255])},   # Orange-red
    {'lower': np.array([15, 100, 200]), 'upper': np.array([35, 255, 255])},  # Yellow-orange
    {'lower': np.array([170, 100, 200]), 'upper': np.array([180, 255, 255])}, # Deep red
]
```

---

## 🧪 Testing

Test the system **safely** without actual fire:

1. 📱 Display fire/flame images or videos on your phone
2. 🟠 Show bright orange/red colored objects to the camera
3. 🔦 Use the flashlight on your phone with an orange filter
4. 🎬 Play a fireplace video on a tablet

---

## ⚠️ Limitations & Disclaimer

> **This is a PROTOTYPE/DEMO system for educational purposes only!**

- ❌ **NOT suitable** for production safety systems
- ⚡ May produce **false positives** with bright orange/red objects, sunlight, or reflections
- 🌡️ Detection accuracy varies with **lighting conditions**
- 🔥 Do NOT rely on this system for actual fire safety

**For real fire safety, always use certified fire detection equipment!**

---

## 📁 Project Structure

```
fire/
├── fire_alarm_system.py    # Main application (940 lines)
├── aag_audio.m4a           # Alarm sound file (optional)
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

---

## 🛠️ Troubleshooting

| Issue                    | Solution                                      |
| ------------------------ | --------------------------------------------- |
| "No cameras found"       | Connect a webcam and restart                  |
| No alarm sound           | Install pygame: `pip install pygame`          |
| Audio not playing        | Add `aag_audio.m4a` file to the folder        |
| Too many false positives | Increase `FIRE_MIN_AREA` or adjust HSV ranges |
| Detection too slow       | Lower display resolution in config            |

---

## 📝 License

This project is open source and available for educational purposes.

---

## 🤝 Contributing

Feel free to fork, modify, and improve! Pull requests are welcome.

---

**Made with ❤️ using Python and OpenCV**

_If you found this helpful, give it a ⭐!_
