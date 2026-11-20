"""
Détection de codes-barres : depuis une image téléversée ou depuis la webcam.

La webcam est ouverte dans un processus séparé (fenêtre OpenCV sur la machine
qui exécute le serveur), ce qui évite de bloquer ou de faire planter Dash :
    python -m utils.barcode --webcam
"""
import base64
import logging
import os
import subprocess
import sys
import time

import cv2
import numpy as np
from pyzbar.pyzbar import decode

logger = logging.getLogger("greenbite.barcode")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEBCAM_TIMEOUT = 30  # secondes


def _decode_first(image):
    barcodes = decode(image)
    return barcodes[0].data.decode("utf-8") if barcodes else None


def decode_barcode_from_array(image):
    """Essaie plusieurs prétraitements et rotations pour trouver un code-barres."""
    if image is None:
        return None
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    variants = [
        gray,
        blurred,
        cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2),
        cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1],
    ]
    for variant in variants:
        for k in range(4):
            code = _decode_first(np.rot90(variant, k) if k else variant)
            if code:
                return code
    return None


def decode_barcode_from_upload(contents):
    """Décode le code-barres d'une image envoyée par dcc.Upload (data URL base64)."""
    try:
        _, encoded = contents.split(",", 1)
        data = np.frombuffer(base64.b64decode(encoded), np.uint8)
        image = cv2.imdecode(data, cv2.IMREAD_COLOR)
        return decode_barcode_from_array(image)
    except Exception:
        logger.exception("Impossible de lire l'image téléversée")
        return None


def scan_webcam_interactive(timeout=WEBCAM_TIMEOUT):
    """Ouvre la webcam dans une fenêtre et renvoie le premier code-barres détecté (ou None)."""
    backend = cv2.CAP_DSHOW if sys.platform.startswith("win") else cv2.CAP_ANY
    cap = None
    for index in (0, 1):
        cap = cv2.VideoCapture(index, backend)
        if cap.isOpened():
            break
        cap.release()
        cap = None
    if cap is None:
        print("ERROR:Aucune webcam disponible", file=sys.stderr)
        return None

    window = "GreenBite - Scanner"
    cv2.namedWindow(window, cv2.WINDOW_NORMAL)
    try:
        cv2.setWindowProperty(window, cv2.WND_PROP_TOPMOST, 1)  # fenêtre au premier plan
    except cv2.error:
        pass

    deadline = time.time() + timeout
    code = None
    try:
        while time.time() < deadline:
            ok, frame = cap.read()
            if not ok:
                if cv2.waitKey(30) & 0xFF in (ord("q"), ord("Q"), 27):
                    break
                continue
            barcodes = decode(frame)
            if barcodes:
                barcode = barcodes[0]
                code = barcode.data.decode("utf-8")
                pts = np.array(barcode.polygon, np.int32).reshape((-1, 1, 2))
                cv2.polylines(frame, [pts], True, (0, 200, 0), 3)
                cv2.imshow(window, frame)
                cv2.waitKey(800)
                break

            remaining = int(deadline - time.time())
            cv2.putText(frame, f"Q / Echap / croix : fermer   ({remaining}s)", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 4)
            cv2.putText(frame, f"Q / Echap / croix : fermer   ({remaining}s)", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.imshow(window, frame)

            # Fermeture au clavier (Q ou Échap)
            if cv2.waitKey(1) & 0xFF in (ord("q"), ord("Q"), 27):
                break
            # Fermeture avec la croix : sinon imshow rouvrirait la fenêtre à l'image suivante
            try:
                if cv2.getWindowProperty(window, cv2.WND_PROP_VISIBLE) < 1:
                    break
            except cv2.error:
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
        cv2.waitKey(1)  # laisse Windows détruire réellement la fenêtre
    if code is None:
        print("CANCELLED")
    return code


def scan_barcode_with_webcam():
    """
    Lance le scanner webcam dans un sous-processus et renvoie (code, message_erreur).
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "utils.barcode", "--webcam"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=WEBCAM_TIMEOUT + 15,
        )
    except subprocess.TimeoutExpired:
        return None, "Le scanner webcam a mis trop de temps à répondre."
    except Exception as exc:
        return None, f"Impossible de lancer le scanner webcam : {exc}"

    for line in result.stdout.splitlines():
        if line.startswith("BARCODE:"):
            return line.split(":", 1)[1].strip(), None
    for line in result.stderr.splitlines():
        if line.startswith("ERROR:"):
            return None, line.split(":", 1)[1].strip()
    if "CANCELLED" in result.stdout:
        return None, "Scan annulé : aucun code-barres lu."
    return None, "Aucun code-barres détecté (délai dépassé ou fenêtre fermée)."


if __name__ == "__main__":
    if "--webcam" in sys.argv:
        detected = scan_webcam_interactive()
        if detected:
            print(f"BARCODE:{detected}")
    elif len(sys.argv) > 1:
        # Usage : python -m utils.barcode chemin/vers/image.jpg
        print(decode_barcode_from_array(cv2.imread(sys.argv[1])))
