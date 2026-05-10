"""
Vizualno prepoznavanje objektov s kamero.
Uporablja OpenCV za detekcijo barv (HSV) in oblik (kontore),
ter YOLOv8 kot backup za kompleksnejše objekte.
"""

import threading
import cv2
import numpy as np
import config

# YOLO se naloži samo če je omogočen
_yolo_model = None


def _load_yolo():
    """Naloži YOLO model (lazy loading - samo ob prvi uporabi)."""
    global _yolo_model
    if _yolo_model is None and config.YOLO_ENABLED:
        try:
            from ultralytics import YOLO
            _yolo_model = YOLO(config.YOLO_MODEL)
            print("[KAMERA] YOLOv8 model naložen.")
        except Exception as e:
            print(f"[KAMERA] YOLO ni na voljo: {e}")
    return _yolo_model


class DetectedObject:
    """Podatki o zaznanem objektu."""

    def __init__(self, color, shape, x, y, w, h, area, frame_width):
        self.color = color              # Ime barve ("rdeca", "modra", ...)
        self.shape = shape              # Ime oblike ("trikotnik", "kvadrat", "krog")
        self.x = x                      # X pozicija centra
        self.y = y                      # Y pozicija centra
        self.w = w                      # Širina bounding boxa
        self.h = h                      # Višina bounding boxa
        self.area = area                # Površina konture
        self.frame_width = frame_width  # Širina celotnega okvirja

    @property
    def position(self):
        """Vrne pozicijo objekta: 'levo', 'sredina', ali 'desno'."""
        relative_x = self.x / self.frame_width
        if relative_x < config.FRAME_CENTER_MIN:
            return "levo"
        elif relative_x > config.FRAME_CENTER_MAX:
            return "desno"
        else:
            return "sredina"

    @property
    def offset_from_center(self):
        """
        Vrne odmik od centra slike (-1.0 do 1.0).
        -1.0 = skrajno levo, 0.0 = sredina, 1.0 = skrajno desno
        """
        return (self.x / self.frame_width - 0.5) * 2

    def __repr__(self):
        color_display = config.COLOR_DISPLAY_NAMES.get(self.color, self.color)
        shape_display = config.SHAPE_DISPLAY_NAMES.get(self.shape, self.shape)
        return (f"Objekt({color_display} {shape_display}, "
                f"pozicija={self.position}, odmik={self.offset_from_center:.2f})")


class CameraVision:
    """Zajem slike in prepoznavanje objektov."""

    def __init__(self):
        """Odpre kamero in pripravi zajem."""
        self.cap = cv2.VideoCapture(config.CAMERA_INDEX, cv2.CAP_V4L2)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_HEIGHT)
        self.cap.set(cv2.CAP_PROP_FPS, config.CAMERA_FPS)

        if not self.cap.isOpened():
            raise RuntimeError("Ne morem odpreti kamere! Preveri USB priklop.")

        self._confirm_count = 0
        self._confirm_target = None
        self._lock = threading.Lock()
        print("[KAMERA] Inicializirana.")

    def _detect_shape(self, contour):
        """
        Prepozna obliko na podlagi števila oglišč konture.
        Vrne ime oblike ali None.
        """
        # Approksimacija konture s poligonom
        perimeter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.04 * perimeter, True)
        num_vertices = len(approx)

        # Preveri znane oblike
        if num_vertices in config.SHAPE_VERTICES:
            # Za kvadrat/kocko preveri razmerje stranic
            if num_vertices == 4:
                x, y, w, h = cv2.boundingRect(approx)
                aspect_ratio = float(w) / h
                if 0.7 <= aspect_ratio <= 1.3:
                    return config.SHAPE_VERTICES[4]  # kvadrat
                else:
                    return None  # pravokotnik - ni ciljna oblika
            return config.SHAPE_VERTICES[num_vertices]
        elif num_vertices > 6:
            # Preveri cirkularnost
            area = cv2.contourArea(contour)
            circularity = 4 * np.pi * area / (perimeter * perimeter)
            if circularity > 0.7:
                return "krog"

        return None

    def _find_color_objects(self, frame, target_color=None, target_shape=None):
        """
        Poišče objekte določene barve in oblike v okvirju.
        Vrne seznam DetectedObject.
        """
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        frame_height, frame_width = frame.shape[:2]
        detected = []

        # Določi katere barve iskati
        if target_color and target_color in config.COLOR_RANGES:
            colors_to_check = {target_color: config.COLOR_RANGES[target_color]}
        else:
            colors_to_check = config.COLOR_RANGES

        for color_name, ranges in colors_to_check.items():
            # Ustvari masko za barvo (lahko ima več razponov, npr. rdeča)
            combined_mask = None
            for r in ranges:
                lower = np.array(r["lower"])
                upper = np.array(r["upper"])
                mask = cv2.inRange(hsv, lower, upper)
                if combined_mask is None:
                    combined_mask = mask
                else:
                    combined_mask = cv2.bitwise_or(combined_mask, mask)

            # Počisti masko z morfološkimi operacijami
            kernel = np.ones((5, 5), np.uint8)
            combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel)
            combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel)

            # Najdi konture
            contours, _ = cv2.findContours(
                combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            for contour in contours:
                area = cv2.contourArea(contour)
                if area < config.MIN_CONTOUR_AREA:
                    continue

                # Prepoznaj obliko
                shape = self._detect_shape(contour)
                if shape is None:
                    continue

                # Filtriraj po ciljni obliki
                if target_shape and shape != target_shape:
                    continue

                # Izračunaj pozicijo
                M = cv2.moments(contour)
                if M["m00"] == 0:
                    continue
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                x, y, w, h = cv2.boundingRect(contour)

                obj = DetectedObject(
                    color=color_name,
                    shape=shape,
                    x=cx,
                    y=cy,
                    w=w,
                    h=h,
                    area=area,
                    frame_width=frame_width,
                )
                detected.append(obj)

        # Sortiraj po velikosti (največji najprej)
        detected.sort(key=lambda o: o.area, reverse=True)
        return detected

    def _find_yolo_objects(self, frame):
        """
        Uporabi YOLOv8 za detekcijo objektov.
        Vrne seznam DetectedObject (brez barve in specifične oblike).
        """
        model = _load_yolo()
        if model is None:
            return []

        results = model(frame, conf=config.YOLO_CONFIDENCE, verbose=False)
        detected = []
        frame_height, frame_width = frame.shape[:2]

        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                cx = int((x1 + x2) / 2)
                cy = int((y1 + y2) / 2)
                w = int(x2 - x1)
                h = int(y2 - y1)
                area = w * h

                class_id = int(box.cls[0])
                class_name = model.names[class_id]

                obj = DetectedObject(
                    color="neznana",
                    shape=class_name,
                    x=cx,
                    y=cy,
                    w=w,
                    h=h,
                    area=area,
                    frame_width=frame_width,
                )
                detected.append(obj)

        return detected

    def _enhance_frame(self, frame):
        """Ojača barve v sliki (za slabše kamere)."""
        if not config.CAMERA_ENHANCE:
            return frame

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)

        # Poveča saturacijo
        s = np.clip(s.astype(np.float32) * config.CAMERA_SATURATION_MULT,
                     0, 255).astype(np.uint8)

        # Poveča svetlost
        v = np.clip(v.astype(np.float32) + config.CAMERA_BRIGHTNESS_ADD,
                     0, 255).astype(np.uint8)

        enhanced_hsv = cv2.merge([h, s, v])
        return cv2.cvtColor(enhanced_hsv, cv2.COLOR_HSV2BGR)

    def capture_frame(self):
        """Zajame en okvir s kamere in ojača barve. Vrne sliko ali None."""
        with self._lock:
            ret, frame = self.cap.read()
        if not ret:
            return None
        return self._enhance_frame(frame)

    def find_object(self, target_color=None, target_shape=None, require_confirmation=False):
        """
        Poišče ciljni objekt v trenutnem okvirju kamere.
        Najprej poskusi z OpenCV, nato z YOLO kot backup.

        Args:
            target_color: Ime barve (slovensko, npr. "rdeca")
            target_shape: Ime oblike (slovensko, npr. "trikotnik")
            require_confirmation: Če True, vrne objekt šele ko ga vidi CONFIRM_FRAMES zaporednih okvirjev

        Returns:
            DetectedObject ali None če ni najden.
        """
        frame = self.capture_frame()
        if frame is None:
            return None

        # 1. Poskusi z OpenCV (barvni filtri + oblike)
        objects = self._find_color_objects(frame, target_color, target_shape)

        if not require_confirmation:
            if objects:
                return objects[0]
            if config.YOLO_ENABLED and target_color is None:
                yolo_objects = self._find_yolo_objects(frame)
                if yolo_objects:
                    return yolo_objects[0]
            return None

        # Potrditveni način — zahteva CONFIRM_FRAMES zaporednih zaznav
        current_target = (target_color, target_shape)
        if current_target != self._confirm_target:
            self._confirm_count = 0
            self._confirm_target = current_target

        if objects:
            self._confirm_count += 1
            if self._confirm_count >= config.CONFIRM_FRAMES:
                return objects[0]
            return None
        else:
            self._confirm_count = 0
            if config.YOLO_ENABLED and target_color is None:
                yolo_objects = self._find_yolo_objects(frame)
                if yolo_objects:
                    return yolo_objects[0]
            return None

    def find_all_objects(self, target_color=None, target_shape=None):
        """Poišče vse objekte v okvirju. Vrne seznam DetectedObject."""
        frame = self.capture_frame()
        if frame is None:
            return []

        return self._find_color_objects(frame, target_color, target_shape)

    def get_annotated_frame(self, target_color=None, target_shape=None):
        """
        Vrne okvir z označenimi objekti (za debug/vizualizacijo).
        """
        frame = self.capture_frame()
        if frame is None:
            return None

        objects = self._find_color_objects(frame, target_color, target_shape)

        for obj in objects:
            # Nariši pravokotnik
            x, y, w, h = obj.x - obj.w // 2, obj.y - obj.h // 2, obj.w, obj.h
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Nariši oznako
            color_display = config.COLOR_DISPLAY_NAMES.get(obj.color, obj.color)
            shape_display = config.SHAPE_DISPLAY_NAMES.get(obj.shape, obj.shape)
            label = f"{color_display} {shape_display}"
            cv2.putText(frame, label, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            # Nariši center
            cv2.circle(frame, (obj.x, obj.y), 5, (0, 0, 255), -1)

        # Nariši sredinske črte
        h, w = frame.shape[:2]
        left_line = int(w * config.FRAME_CENTER_MIN)
        right_line = int(w * config.FRAME_CENTER_MAX)
        cv2.line(frame, (left_line, 0), (left_line, h), (255, 255, 0), 1)
        cv2.line(frame, (right_line, 0), (right_line, h), (255, 255, 0), 1)

        return frame

    def cleanup(self):
        """Sprosti kamero."""
        self.cap.release()
        cv2.destroyAllWindows()
        print("[KAMERA] Sproščena.")


# ============================================================
# Test kamere (zaženi z: python3 camera_vision.py)
# ============================================================
if __name__ == "__main__":
    print("=== Test kamere in detekcije ===")
    print("Pritisni 'q' za izhod.")
    print("")

    camera = CameraVision()

    try:
        while True:
            # Zajemi okvir z označenimi objekti
            frame = camera.get_annotated_frame()
            if frame is None:
                print("Napaka pri zajemu okvirja!")
                break

            # Poišči vse objekte
            objects = camera.find_all_objects()
            if objects:
                for obj in objects:
                    print(f"  Zaznan: {obj}")

            # Prikaži okno
            cv2.imshow("Robot Kamera - Detekcija", frame)

            # Izhod s tipko 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        print("\nPrekinjen s Ctrl+C")
    finally:
        camera.cleanup()
