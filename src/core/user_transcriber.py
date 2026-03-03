import difflib
import queue
import sys
import threading
import time

import numpy as np
import sounddevice as sd
import whisper

from src.analysis import sentiment_analyzer
from src.database import db_manager

SAMPLE_RATE = 16000
CHANNELS = 1
BUFFER_DURATION_SECONDS = 2.0
ECHO_SIMILARITY_THRESHOLD = 0.6


def _similarity_ratio(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()


class UserTranscriberService:
    def __init__(self):
        self._raw_audio_queue: queue.Queue = queue.Queue(maxsize=64)
        self._processing_queue: queue.Queue = queue.Queue(maxsize=32)
        self._stop_event = threading.Event()
        self._threads: list[threading.Thread] = []
        self._device_index = self._resolve_input_device()

    def _resolve_input_device(self):
        try:
            default_input = sd.query_devices(kind="input")
            print(f"🎤 Input device: {default_input['name']} (index={default_input['index']})")
            return default_input["index"]
        except Exception as e:
            print(f"⚠️ Failed to resolve input device: {e}")
            return None

    def _audio_callback(self, indata, frames, callback_time, status):
        if status:
            print(f"⚠️ Audio status: {status}", file=sys.stderr)
        try:
            self._raw_audio_queue.put_nowait(indata.copy())
        except queue.Full:
            pass

    def _capture_loop(self):
        buffer_size = int(SAMPLE_RATE * BUFFER_DURATION_SECONDS)
        current_buffer = np.zeros(buffer_size, dtype=np.float32)
        buffer_idx = 0
        with sd.InputStream(
            device=self._device_index,
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            callback=self._audio_callback,
        ):
            while not self._stop_event.is_set():
                try:
                    chunk = self._raw_audio_queue.get(timeout=0.2).flatten()
                    amplitude = float(np.max(np.abs(chunk)))
                    if amplitude > 0.01:
                        bars = int(amplitude * 30)
                        sys.stdout.write(f"\r🎤 Input level: [{'|' * bars:<15}]")
                        sys.stdout.flush()
                    chunk_len = len(chunk)
                    remaining = buffer_size - buffer_idx
                    if chunk_len >= remaining:
                        current_buffer[buffer_idx:] = chunk[:remaining]
                        if np.max(np.abs(current_buffer)) > 0.02:
                            try:
                                self._processing_queue.put_nowait(current_buffer.copy())
                            except queue.Full:
                                pass
                        current_buffer.fill(0)
                        buffer_idx = 0
                        if chunk_len > remaining:
                            leftover = chunk[remaining:]
                            max_len = min(len(leftover), buffer_size)
                            current_buffer[:max_len] = leftover[:max_len]
                            buffer_idx = max_len
                    else:
                        current_buffer[buffer_idx : buffer_idx + chunk_len] = chunk
                        buffer_idx += chunk_len
                except queue.Empty:
                    continue
                except Exception as e:
                    print(f"\n⚠️ Capture loop error: {e}")

    def _is_echo(self, text: str) -> bool:
        recent_logs = db_manager.get_recent_logs(limit=6)
        for _, speaker, ai_text, _ in recent_logs:
            if speaker == "AI" and _similarity_ratio(text, ai_text) > ECHO_SIMILARITY_THRESHOLD:
                return True
        return False

    def _processing_loop(self):
        try:
            model = whisper.load_model("base.en")
            print("✅ Whisper model loaded")
        except Exception as e:
            print(f"❌ Failed to load Whisper model: {e}")
            return
        while not self._stop_event.is_set():
            try:
                audio_buffer = self._processing_queue.get(timeout=0.2)
                result = model.transcribe(audio_buffer, fp16=False, language="en")
                text = result["text"].strip()
                if not text or len(text) < 3:
                    continue
                if self._is_echo(text):
                    continue
                score = sentiment_analyzer.get_score(text)
                db_manager.save_entry("User", text, score)
                print(f"\n👤 User: {text} ({score:.2f})")
            except queue.Empty:
                continue
            except Exception as e:
                print(f"\n⚠️ Processing loop error: {e}")

    def start(self):
        self._stop_event.clear()
        capture = threading.Thread(target=self._capture_loop, daemon=True)
        processing = threading.Thread(target=self._processing_loop, daemon=True)
        capture.start()
        processing.start()
        self._threads = [capture, processing]
        return self._threads

    def stop(self, timeout: float = 2.0):
        self._stop_event.set()
        for thread in self._threads:
            if thread.is_alive():
                thread.join(timeout=timeout)


_service_instance: UserTranscriberService | None = None


def start_transcription():
    global _service_instance
    if _service_instance is None:
        _service_instance = UserTranscriberService()
    return _service_instance.start()


def stop_transcription():
    global _service_instance
    if _service_instance is not None:
        _service_instance.stop()


if __name__ == "__main__":
    db_manager.init_db()
    start_transcription()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_transcription()
