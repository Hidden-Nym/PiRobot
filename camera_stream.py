"""
Streama kamero preko HTTP, da jo lahko gledaš v brskalniku.
Zaženi na Pi-ju: python3 camera_stream.py
Odpri v brskalniku: http://<IP-PI>:8080
"""

import sys
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
import cv2
from camera_vision import CameraVision

# Barva/oblika za detekcijo (opcijsko iz argumentov)
TARGET_COLOR = sys.argv[1] if len(sys.argv) > 1 else None
TARGET_SHAPE = sys.argv[2] if len(sys.argv) > 2 else None

camera = None


class StreamHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(b'''<html><body style="margin:0;background:#000;display:flex;justify-content:center;align-items:center;height:100vh">
                <img src="/stream" style="max-width:100%;max-height:100vh">
            </body></html>''')
        elif self.path == '/stream':
            self.send_response(200)
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=frame')
            self.end_headers()
            try:
                while True:
                    frame = camera.get_annotated_frame(TARGET_COLOR, TARGET_SHAPE)
                    if frame is None:
                        time.sleep(0.1)
                        continue
                    _, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                    self.wfile.write(b'--frame\r\n')
                    self.wfile.write(b'Content-Type: image/jpeg\r\n\r\n')
                    self.wfile.write(jpeg.tobytes())
                    self.wfile.write(b'\r\n')
            except (BrokenPipeError, ConnectionResetError):
                pass
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Tiho


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


if __name__ == '__main__':
    camera = CameraVision()
    port = 8080

    if TARGET_COLOR:
        print(f"[STREAM] Filtriram: barva={TARGET_COLOR}, oblika={TARGET_SHAPE}")
    else:
        print("[STREAM] Prikaz vseh zaznanih objektov.")

    print(f"[STREAM] Odpri v brskalniku: http://0.0.0.0:{port}")
    print("[STREAM] Ctrl+C za ustavitev.")

    server = ThreadedHTTPServer(('0.0.0.0', port), StreamHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[STREAM] Ustavljam...")
    finally:
        camera.cleanup()
        server.server_close()
