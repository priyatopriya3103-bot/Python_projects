import cv2
import numpy as np
import time
import os
import subprocess
import sys
from collections import deque
from threading import Thread

# Try to import pygame for audio
AUDIO_AVAILABLE = False
AUDIO_METHOD = None

try:
    import pygame
    AUDIO_AVAILABLE = True
    AUDIO_METHOD = "pygame"
except ImportError:
    pass

# If pygame fails for M4A, try using system commands as fallback
if not AUDIO_AVAILABLE:
    # Check if we can use Windows Media Player via PowerShell
    if sys.platform == "win32":
        AUDIO_AVAILABLE = True
        AUDIO_METHOD = "windows"
        print("Using Windows native audio playback")

if not AUDIO_AVAILABLE:
    print("Warning: No audio playback method available.")
    print("Install pygame with: pip install pygame")


# ============================================================================
# CONFIGURATION
# ============================================================================

# Camera settings
CAMERA_INDEX = 0
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

# Display settings
DISPLAY_WIDTH = 854
DISPLAY_HEIGHT = 480

# Alarm display settings
ALARM_DISPLAY_WIDTH = 600
ALARM_DISPLAY_HEIGHT = 400

# Fire detection settings
FIRE_MIN_AREA = 500          # Minimum contour area to consider as fire
CONSECUTIVE_FRAMES = 1        # Frames of fire detection before triggering alarm
COOLDOWN_FRAMES = 30          # Frames without fire before stopping alarm

# HSV ranges for fire detection (multiple ranges for better coverage)
# Fire typically has orange/red/yellow colors with high saturation and value
FIRE_HSV_RANGES = [
    # Orange-red fire
    {'lower': np.array([0, 100, 200]), 'upper': np.array([15, 255, 255])},
    # Yellow-orange fire  
    {'lower': np.array([15, 100, 200]), 'upper': np.array([35, 255, 255])},
    # Deep red fire
    {'lower': np.array([170, 100, 200]), 'upper': np.array([180, 255, 255])},
]

# Audio settings - using M4A audio file
ALARM_SOUND_PATH = os.path.join(os.path.dirname(__file__), "aag_audio.m4a")


# ============================================================================
# CAMERA SELECTION HELPER
# ============================================================================

def list_available_cameras(max_cameras=10):
    """
    Scan for available cameras and return a list of (index, name) tuples.
    
    Args:
        max_cameras: Maximum number of camera indices to check
        
    Returns:
        List of tuples: [(index, camera_name), ...]
    """
    available_cameras = []
    
    print("\nScanning for available cameras...")
    
    for index in range(max_cameras):
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            # Try to get camera name/backend info
            backend = cap.getBackendName()
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            camera_name = f"Camera {index} ({backend}) - {width}x{height}"
            available_cameras.append((index, camera_name))
            cap.release()
        else:
            cap.release()
    
    return available_cameras


def select_camera():
    """
    Display available cameras and let user select one.
    
    Returns:
        Selected camera index (int)
    """
    cameras = list_available_cameras()
    
    if not cameras:
        print("\n❌ No cameras found!")
        print("Please connect a camera and try again.")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("AVAILABLE CAMERAS")
    print("=" * 50)
    
    for idx, (cam_index, cam_name) in enumerate(cameras):
        print(f"  [{idx + 1}] {cam_name}")
    
    print("=" * 50)
    
    # If only one camera, auto-select it
    if len(cameras) == 1:
        print(f"\n✓ Auto-selecting the only available camera: {cameras[0][1]}")
        return cameras[0][0]
    
    # Let user choose
    while True:
        try:
            choice = input(f"\nSelect camera (1-{len(cameras)}) [default: 1]: ").strip()
            
            if choice == "":
                choice = 1
            else:
                choice = int(choice)
            
            if 1 <= choice <= len(cameras):
                selected_index = cameras[choice - 1][0]
                print(f"\n✓ Selected: {cameras[choice - 1][1]}")
                return selected_index
            else:
                print(f"Please enter a number between 1 and {len(cameras)}")
        except ValueError:
            print("Invalid input. Please enter a number.")
        except KeyboardInterrupt:
            print("\n\nCancelled by user.")
            sys.exit(0)


# ============================================================================
# FIRE DETECTOR CLASS
# ============================================================================

class FireDetector:
    """
    Detects fire in video frames using HSV color thresholding.
    This is a simple but effective approach for prototype/demo purposes.
    """
    
    def __init__(self):
        self.detection_history = deque(maxlen=CONSECUTIVE_FRAMES)
        self.last_detection_time = 0
        
    def detect(self, frame: np.ndarray) -> dict:
        """
        Detect fire in the given frame.
        
        Returns:
            dict with keys:
                - fire_detected: bool
                - confidence: float (0-1)
                - bounding_boxes: list of (x, y, w, h)
                - mask: binary mask of fire regions
                - fire_area: total fire pixel area
        """
        # Convert to HSV color space
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Create combined mask from all fire color ranges
        combined_mask = np.zeros(frame.shape[:2], dtype=np.uint8)
        
        for hsv_range in FIRE_HSV_RANGES:
            mask = cv2.inRange(hsv, hsv_range['lower'], hsv_range['upper'])
            combined_mask = cv2.bitwise_or(combined_mask, mask)
        
        # Apply morphological operations to clean up the mask
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel)
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel)
        
        # Apply Gaussian blur to smooth edges
        combined_mask = cv2.GaussianBlur(combined_mask, (5, 5), 0)
        _, combined_mask = cv2.threshold(combined_mask, 127, 255, cv2.THRESH_BINARY)
        
        # Find contours
        contours, _ = cv2.findContours(
            combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        
        # Filter contours by area and get bounding boxes
        bounding_boxes = []
        total_fire_area = 0
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area >= FIRE_MIN_AREA:
                x, y, w, h = cv2.boundingRect(contour)
                bounding_boxes.append((x, y, w, h))
                total_fire_area += area
        
        # Calculate confidence based on fire area relative to frame
        frame_area = frame.shape[0] * frame.shape[1]
        confidence = min(total_fire_area / (frame_area * 0.1), 1.0)  # Cap at 100%
        
        # Determine if fire is detected
        fire_detected = len(bounding_boxes) > 0
        
        # Update detection history
        self.detection_history.append(fire_detected)
        
        return {
            'fire_detected': fire_detected,
            'confidence': confidence,
            'bounding_boxes': bounding_boxes,
            'mask': combined_mask,
            'fire_area': total_fire_area
        }
    
    def is_fire_confirmed(self) -> bool:
        """
        Check if fire has been detected for enough consecutive frames.
        This reduces false positives from momentary detections.
        """
        if len(self.detection_history) < CONSECUTIVE_FRAMES:
            return False
        return all(self.detection_history)
    
    def reset(self):
        """Reset detection history"""
        self.detection_history.clear()


# ============================================================================
# ALARM MANAGER CLASS
# ============================================================================

class AlarmManager:
    """
    Manages the alarm state and audio playback.
    Supports multiple audio methods: pygame, Windows native
    """
    
    def __init__(self, sound_path: str):
        self.sound_path = sound_path
        self.is_playing = False
        self.alarm_active = False
        self.sound_enabled = True
        self.no_fire_counter = 0
        self.audio_process = None  # For Windows native playback
        self.audio_thread = None
        
        # Load alarm sound based on available method
        self.sound_loaded = False
        
        if not os.path.exists(sound_path):
            print(f"Warning: Alarm sound file not found: {sound_path}")
            print("Place 'aag_audio.m4a' in the fire folder for audio alerts.")
            return
        
        if AUDIO_METHOD == "pygame":
            try:
                # Initialize pygame mixer with settings that work better for various formats
                pygame.mixer.quit()
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
                pygame.mixer.music.load(sound_path)
                self.sound_loaded = True
                print(f"✓ Alarm sound loaded (pygame): {sound_path}")
            except Exception as e:
                print(f"Warning: pygame could not load M4A: {e}")
                print("Falling back to Windows native audio...")
                # Fall back to Windows native
                if sys.platform == "win32":
                    self.sound_loaded = True
                    print(f"✓ Alarm sound ready (Windows native): {sound_path}")
        
        elif AUDIO_METHOD == "windows":
            self.sound_loaded = True
            print(f"✓ Alarm sound ready (Windows native): {sound_path}")
    
    def trigger_alarm(self):
        """Start the alarm"""
        if not self.alarm_active:
            self.alarm_active = True
            self.no_fire_counter = 0
            print("🔥 FIRE ALARM TRIGGERED!")
            self._play_sound()
    
    def stop_alarm(self):
        """Stop the alarm"""
        if self.alarm_active:
            self.alarm_active = False
            print("✓ Alarm stopped - System normal")
            self._stop_sound()
    
    def update(self, fire_confirmed: bool):
        """
        Update alarm state based on fire detection.
        Implements hysteresis to prevent rapid on/off switching.
        """
        if fire_confirmed:
            self.no_fire_counter = 0
            self.trigger_alarm()
        else:
            if self.alarm_active:
                self.no_fire_counter += 1
                if self.no_fire_counter >= COOLDOWN_FRAMES:
                    self.stop_alarm()
    
    def _play_sound(self):
        """Play alarm sound (loops continuously)"""
        if not self.sound_enabled or not self.sound_loaded or self.is_playing:
            return
        
        try:
            if AUDIO_METHOD == "pygame":
                try:
                    pygame.mixer.music.play(-1)  # -1 = loop indefinitely
                    self.is_playing = True
                except:
                    # Fall back to Windows native
                    self._play_windows_audio()
            elif AUDIO_METHOD == "windows":
                self._play_windows_audio()
        except Exception as e:
            print(f"Error playing sound: {e}")
    
    def _play_windows_audio(self):
        """Play audio using Windows Media Player via PowerShell (loops)"""
        if self.is_playing:
            return
        
        self.is_playing = True
        
        def play_loop():
            while self.is_playing and self.alarm_active:
                try:
                    # Use PowerShell to play the audio file
                    cmd = f'''
                    Add-Type -AssemblyName presentationCore
                    $player = New-Object System.Windows.Media.MediaPlayer
                    $player.Open("{self.sound_path}")
                    $player.Play()
                    Start-Sleep -Seconds 10
                    $player.Stop()
                    $player.Close()
                    '''
                    self.audio_process = subprocess.Popen(
                        ["powershell", "-Command", cmd],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                    )
                    self.audio_process.wait()
                except Exception as e:
                    print(f"Windows audio error: {e}")
                    break
        
        self.audio_thread = Thread(target=play_loop, daemon=True)
        self.audio_thread.start()
    
    def _stop_sound(self):
        """Stop alarm sound"""
        if not self.is_playing:
            return
        
        try:
            if AUDIO_METHOD == "pygame":
                try:
                    pygame.mixer.music.stop()
                except:
                    pass
            
            # Stop Windows audio process if running
            if self.audio_process:
                try:
                    self.audio_process.terminate()
                except:
                    pass
                self.audio_process = None
            
            self.is_playing = False
        except Exception as e:
            print(f"Error stopping sound: {e}")
    
    def toggle_sound(self):
        """Toggle sound on/off"""
        self.sound_enabled = not self.sound_enabled
        if not self.sound_enabled:
            self._stop_sound()
        elif self.alarm_active:
            self._play_sound()
        return self.sound_enabled
    
    def cleanup(self):
        """Clean up audio resources"""
        self._stop_sound()
        if AUDIO_AVAILABLE:
            pygame.mixer.quit()


# ============================================================================
# CAMERA VIEW RENDERER (SCREEN 1)
# ============================================================================

class CameraViewRenderer:
    """
    Renders the camera feed with fire detection overlay.
    Shows: Camera + bounding boxes + detection status
    """
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.flash_state = False
        self.flash_counter = 0
    
    def render(self, frame: np.ndarray, detection_result: dict, 
               alarm_active: bool, fps: float) -> np.ndarray:
        """Render camera view with detection overlay"""
        
        # Resize frame to display size
        display = cv2.resize(frame, (self.width, self.height))
        
        # Scale factor for bounding boxes
        scale_x = self.width / frame.shape[1]
        scale_y = self.height / frame.shape[0]
        
        # Draw fire regions
        if detection_result['fire_detected']:
            # Draw bounding boxes
            for (x, y, w, h) in detection_result['bounding_boxes']:
                # Scale coordinates
                sx = int(x * scale_x)
                sy = int(y * scale_y)
                sw = int(w * scale_x)
                sh = int(h * scale_y)
                
                # Draw box with pulsing effect when alarm active
                if alarm_active:
                    self.flash_counter += 1
                    thickness = 3 if self.flash_counter % 10 < 5 else 2
                    color = (0, 0, 255) if self.flash_counter % 20 < 10 else (0, 100, 255)
                else:
                    thickness = 2
                    color = (0, 165, 255)  # Orange
                
                cv2.rectangle(display, (sx, sy), (sx + sw, sy + sh), color, thickness)
                
                # Draw "FIRE" label
                label = "FIRE"
                label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                cv2.rectangle(display, (sx, sy - 25), (sx + label_size[0] + 10, sy), color, -1)
                cv2.putText(display, label, (sx + 5, sy - 7),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Draw header bar
        self._draw_header(display, detection_result, alarm_active, fps)
        
        # Draw footer with status
        self._draw_footer(display, detection_result, alarm_active)
        
        return display
    
    def _draw_header(self, display: np.ndarray, detection_result: dict,
                     alarm_active: bool, fps: float):
        """Draw header with status information"""
        # Semi-transparent header background
        overlay = display.copy()
        cv2.rectangle(overlay, (0, 0), (self.width, 60), (30, 30, 30), -1)
        cv2.addWeighted(overlay, 0.7, display, 0.3, 0, display)
        
        # Title
        cv2.putText(display, "FIRE DETECTION - CAMERA FEED", (15, 35),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # FPS
        fps_color = (100, 255, 100) if fps > 20 else (100, 100, 255)
        cv2.putText(display, f"FPS: {fps:.0f}", (self.width - 100, 35),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, fps_color, 1)
        
        # Detection indicator
        if detection_result['fire_detected']:
            status_color = (0, 0, 255) if alarm_active else (0, 165, 255)
            cv2.circle(display, (self.width - 130, 30), 8, status_color, -1)
        else:
            cv2.circle(display, (self.width - 130, 30), 8, (100, 100, 100), -1)
    
    def _draw_footer(self, display: np.ndarray, detection_result: dict,
                     alarm_active: bool):
        """Draw footer with detailed status"""
        footer_y = self.height - 70
        
        # Semi-transparent footer background
        overlay = display.copy()
        cv2.rectangle(overlay, (0, footer_y), (self.width, self.height), (30, 30, 30), -1)
        cv2.addWeighted(overlay, 0.7, display, 0.3, 0, display)
        
        # Status text
        if alarm_active:
            status = "!! FIRE ALARM ACTIVE !!"
            status_color = (0, 0, 255)
        elif detection_result['fire_detected']:
            status = "Fire Detected - Confirming..."
            status_color = (0, 165, 255)
        else:
            status = "No Fire Detected"
            status_color = (100, 255, 100)
        
        cv2.putText(display, status, (15, footer_y + 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)
        
        # Confidence bar
        confidence = detection_result['confidence']
        bar_width = 200
        bar_height = 15
        bar_x = 15
        bar_y = footer_y + 40
        
        # Background
        cv2.rectangle(display, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height),
                     (60, 60, 60), -1)
        
        # Fill based on confidence
        if confidence > 0:
            fill_width = int(bar_width * confidence)
            # Color gradient based on confidence
            if confidence < 0.3:
                fill_color = (100, 200, 100)  # Green
            elif confidence < 0.6:
                fill_color = (0, 200, 255)    # Yellow
            else:
                fill_color = (0, 0, 255)      # Red
            cv2.rectangle(display, (bar_x, bar_y), (bar_x + fill_width, bar_y + bar_height),
                         fill_color, -1)
        
        cv2.putText(display, f"Confidence: {confidence*100:.0f}%", (bar_x + bar_width + 10, bar_y + 12),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (180, 180, 180), 1)
        
        # Fire area info
        fire_area = detection_result['fire_area']
        cv2.putText(display, f"Fire Area: {fire_area} px", (self.width - 180, footer_y + 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (180, 180, 180), 1)
        
        # Controls hint
        cv2.putText(display, "Q:Quit  S:Sound  R:Reset", (self.width - 200, footer_y + 50),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.35, (120, 120, 120), 1)


# ============================================================================
# ALARM STATUS RENDERER (SCREEN 2)
# ============================================================================

class AlarmStatusRenderer:
    """
    Renders the alarm status display (NO camera feed).
    Shows: Large status text + visual alarm indication
    """
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.flash_phase = 0
        self.pulse_phase = 0
    
    def render(self, alarm_active: bool, fire_detected: bool, 
               sound_enabled: bool) -> np.ndarray:
        """Render alarm status display"""
        
        self.flash_phase += 1
        self.pulse_phase += 0.1
        
        if alarm_active:
            canvas = self._render_alarm_active()
        elif fire_detected:
            canvas = self._render_fire_detected()
        else:
            canvas = self._render_normal()
        
        # Draw sound status
        self._draw_sound_indicator(canvas, sound_enabled)
        
        return canvas
    
    def _render_normal(self) -> np.ndarray:
        """Render normal (no fire) state"""
        # Create dark gradient background
        canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        for y in range(self.height):
            ratio = y / self.height
            r = int(20 * (1 - ratio) + 30 * ratio)
            g = int(30 * (1 - ratio) + 40 * ratio)
            b = int(20 * (1 - ratio) + 30 * ratio)
            canvas[y, :] = [b, g, r]
        
        # Draw checkmark icon
        center_x = self.width // 2
        center_y = self.height // 2 - 40
        
        # Circle background
        cv2.circle(canvas, (center_x, center_y), 60, (50, 100, 50), -1)
        cv2.circle(canvas, (center_x, center_y), 60, (100, 200, 100), 3)
        
        # Checkmark
        pts = np.array([
            [center_x - 30, center_y],
            [center_x - 10, center_y + 25],
            [center_x + 35, center_y - 25]
        ], np.int32)
        cv2.polylines(canvas, [pts], False, (100, 255, 100), 6, cv2.LINE_AA)
        
        # Status text
        text = "SYSTEM NORMAL"
        text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 3)[0]
        text_x = (self.width - text_size[0]) // 2
        cv2.putText(canvas, text, (text_x, center_y + 120),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, (100, 200, 100), 3)
        
        # Subtitle
        subtitle = "No fire detected"
        sub_size = cv2.getTextSize(subtitle, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)[0]
        sub_x = (self.width - sub_size[0]) // 2
        cv2.putText(canvas, subtitle, (sub_x, center_y + 155),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (150, 150, 150), 1)
        
        # Title bar
        self._draw_title(canvas, "Fire Alarm Status", (100, 200, 100))
        
        return canvas
    
    def _render_fire_detected(self) -> np.ndarray:
        """Render fire detected but alarm not yet triggered"""
        canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        # Orange-ish gradient
        for y in range(self.height):
            ratio = y / self.height
            r = int(40 + 20 * ratio)
            g = int(25 + 10 * ratio)
            b = int(10 + 5 * ratio)
            canvas[y, :] = [b, g, r]
        
        center_x = self.width // 2
        center_y = self.height // 2 - 20
        
        # Warning icon
        cv2.circle(canvas, (center_x, center_y), 50, (0, 165, 255), -1)
        cv2.putText(canvas, "!", (center_x - 12, center_y + 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 5)
        
        # Status text
        text = "FIRE DETECTED"
        text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 2)[0]
        text_x = (self.width - text_size[0]) // 2
        cv2.putText(canvas, text, (text_x, center_y + 100),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 200, 255), 2)
        
        subtitle = "Confirming detection..."
        sub_size = cv2.getTextSize(subtitle, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
        sub_x = (self.width - sub_size[0]) // 2
        cv2.putText(canvas, subtitle, (sub_x, center_y + 130),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 150, 100), 1)
        
        self._draw_title(canvas, "Fire Alarm Status", (0, 165, 255))
        
        return canvas
    
    def _render_alarm_active(self) -> np.ndarray:
        """Render active alarm state with flashing effect"""
        canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        # Flashing red background
        flash = (self.flash_phase % 20) < 10
        pulse = (np.sin(self.pulse_phase) + 1) / 2
        
        if flash:
            base_r, base_g, base_b = 60, 10, 10
        else:
            base_r, base_g, base_b = 30, 5, 5
        
        for y in range(self.height):
            ratio = y / self.height
            intensity = 1 + pulse * 0.3
            r = int(base_r * intensity * (1 + ratio * 0.5))
            g = int(base_g * intensity)
            b = int(base_b * intensity)
            canvas[y, :] = [min(b, 255), min(g, 255), min(r, 255)]
        
        center_x = self.width // 2
        center_y = self.height // 2 - 30
        
        # Fire emoji simulation (flame icon)
        self._draw_flame_icon(canvas, center_x, center_y - 30, pulse)
        
        # FIRE ALERT text with glow effect
        alert_text = "FIRE ALERT"
        text_size = cv2.getTextSize(alert_text, cv2.FONT_HERSHEY_SIMPLEX, 1.8, 4)[0]
        text_x = (self.width - text_size[0]) // 2
        text_y = center_y + 80
        
        # Glow
        glow_color = (0, 100, 200) if flash else (0, 50, 150)
        cv2.putText(canvas, alert_text, (text_x - 2, text_y + 2),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.8, glow_color, 8)
        
        # Main text
        text_color = (0, 0, 255) if flash else (0, 50, 200)
        cv2.putText(canvas, alert_text, (text_x, text_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.8, text_color, 4)
        
        # Warning message
        warning = "EVACUATE IMMEDIATELY"
        warn_size = cv2.getTextSize(warning, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
        warn_x = (self.width - warn_size[0]) // 2
        cv2.putText(canvas, warning, (warn_x, text_y + 50),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)
        
        # Flashing border
        border_color = (0, 0, 255) if flash else (0, 0, 150)
        cv2.rectangle(canvas, (5, 5), (self.width - 5, self.height - 5), border_color, 4)
        
        self._draw_title(canvas, "!! FIRE ALARM !!", (0, 0, 255))
        
        return canvas
    
    def _draw_flame_icon(self, canvas: np.ndarray, cx: int, cy: int, pulse: float):
        """Draw a simple flame icon"""
        # Outer flame (orange)
        pts_outer = np.array([
            [cx, cy - 50 - int(pulse * 10)],
            [cx - 30, cy + 20],
            [cx - 15, cy],
            [cx, cy + 30],
            [cx + 15, cy],
            [cx + 30, cy + 20],
        ], np.int32)
        cv2.fillPoly(canvas, [pts_outer], (0, 100, 255))
        
        # Inner flame (yellow)
        pts_inner = np.array([
            [cx, cy - 30 - int(pulse * 5)],
            [cx - 15, cy + 10],
            [cx, cy + 20],
            [cx + 15, cy + 10],
        ], np.int32)
        cv2.fillPoly(canvas, [pts_inner], (0, 200, 255))
        
        # Core (white-yellow)
        pts_core = np.array([
            [cx, cy - 10],
            [cx - 8, cy + 10],
            [cx, cy + 15],
            [cx + 8, cy + 10],
        ], np.int32)
        cv2.fillPoly(canvas, [pts_core], (150, 255, 255))
    
    def _draw_title(self, canvas: np.ndarray, title: str, color: tuple):
        """Draw title bar"""
        cv2.rectangle(canvas, (0, 0), (self.width, 50), (20, 20, 20), -1)
        
        text_size = cv2.getTextSize(title, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
        text_x = (self.width - text_size[0]) // 2
        cv2.putText(canvas, title, (text_x, 35),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
    
    def _draw_sound_indicator(self, canvas: np.ndarray, sound_enabled: bool):
        """Draw sound on/off indicator"""
        x, y = self.width - 80, self.height - 40
        
        if sound_enabled:
            cv2.putText(canvas, "Sound: ON", (x, y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (100, 200, 100), 1)
        else:
            cv2.putText(canvas, "Sound: OFF", (x, y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (100, 100, 200), 1)


# ============================================================================
# MAIN APPLICATION CLASS
# ============================================================================

class FireAlarmSystem:
    """
    Main fire alarm system application.
    Manages camera, detection, rendering, and alarm.
    """
    
    def __init__(self, camera_index=None):
        print("=" * 60)
        print("FIRE ALARM SYSTEM - Prototype")
        print("=" * 60)
        
        # Use provided camera index or default
        if camera_index is None:
            camera_index = CAMERA_INDEX
        
        # Initialize camera
        print(f"Initializing camera (index: {camera_index})...")
        self.cap = cv2.VideoCapture(camera_index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
        
        if not self.cap.isOpened():
            raise RuntimeError("Could not open camera!")
        print("✓ Camera initialized")
        
        # Initialize components
        self.detector = FireDetector()
        self.alarm_manager = AlarmManager(ALARM_SOUND_PATH)
        
        # Initialize renderers
        self.camera_renderer = CameraViewRenderer(DISPLAY_WIDTH, DISPLAY_HEIGHT)
        self.alarm_renderer = AlarmStatusRenderer(ALARM_DISPLAY_WIDTH, ALARM_DISPLAY_HEIGHT)
        
        # State
        self.running = True
        self.fps_history = deque(maxlen=30)
        
        print("✓ System ready")
        print("=" * 60)
    
    def run(self):
        """Main application loop"""
        self._print_instructions()
        
        while self.running:
            frame_start = time.time()
            
            # Capture frame
            ret, frame = self.cap.read()
            if not ret:
                print("Error: Failed to capture frame")
                break
            
            # Flip for mirror effect (optional)
            frame = cv2.flip(frame, 1)
            
            # Detect fire
            detection_result = self.detector.detect(frame)
            
            # Check if fire is confirmed (multiple consecutive frames)
            fire_confirmed = self.detector.is_fire_confirmed()
            
            # Update alarm state
            self.alarm_manager.update(fire_confirmed)
            
            # Calculate FPS
            frame_time = time.time() - frame_start
            self.fps_history.append(1.0 / max(frame_time, 0.001))
            fps = np.mean(self.fps_history)
            
            # Render camera view (Screen 1)
            camera_display = self.camera_renderer.render(
                frame, detection_result, 
                self.alarm_manager.alarm_active, fps
            )
            
            # Render alarm status (Screen 2)
            alarm_display = self.alarm_renderer.render(
                self.alarm_manager.alarm_active,
                detection_result['fire_detected'],
                self.alarm_manager.sound_enabled
            )
            
            # Show windows
            cv2.imshow("Fire Detection - Camera Feed", camera_display)
            cv2.imshow("Fire Alarm Status", alarm_display)
            
            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                self.running = False
            elif key == ord('s'):
                enabled = self.alarm_manager.toggle_sound()
                print(f"Sound {'enabled' if enabled else 'disabled'}")
            elif key == ord('r'):
                self.detector.reset()
                self.alarm_manager.stop_alarm()
                print("System reset")
        
        self.cleanup()
    
    def _print_instructions(self):
        """Print usage instructions"""
        print("\nCONTROLS:")
        print("  Q - Quit application")
        print("  S - Toggle alarm sound on/off")
        print("  R - Reset detection and stop alarm")
        print("\nWINDOWS:")
        print("  [1] Fire Detection - Camera Feed")
        print("      Shows live video with detection overlay")
        print("  [2] Fire Alarm Status")
        print("      Shows alarm state (normal/alert)")
        print("\nDETECTION:")
        print("  - Uses HSV color thresholding for fire detection")
        print("  - Alarm triggers after {} consecutive frames".format(CONSECUTIVE_FRAMES))
        print("  - Point camera at fire/flame-colored objects to test")
        print("\n" + "=" * 60)
    
    def cleanup(self):
        """Clean up resources"""
        print("\nShutting down...")
        self.alarm_manager.cleanup()
        self.cap.release()
        cv2.destroyAllWindows()
        print("✓ Application closed")


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    try:
        # Let user select camera
        selected_camera = select_camera()
        
        # Start the system with selected camera
        system = FireAlarmSystem(camera_index=0)
        system.run()
    except Exception as e:
        print(f"\nError: {e}")
        raise
