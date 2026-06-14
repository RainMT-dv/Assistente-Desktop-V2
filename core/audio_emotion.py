"""Audio emotion detector based on acoustic features."""

from typing import Tuple

import numpy as np

try:
    from scipy import signal
    _SCIPY_AVAILABLE = True
except ImportError:
    _SCIPY_AVAILABLE = False


class AudioEmotionDetector:
    """Detects user emotion from audio features."""

    def __init__(self, config: dict = None):
        """
        Initialize the audio emotion detector.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.min_speech_duration = self.config.get("min_speech_duration", 0.3)
        self.energy_threshold = self.config.get("energy_threshold", 0.05)

    def extract_features(self, samples: np.ndarray, sample_rate: int = 16000) -> dict:
        """
        Extract 5 acoustic features from audio.

        Args:
            samples: Audio samples as numpy array
            sample_rate: Sample rate in Hz

        Returns:
            Dictionary with 5 normalized features (0.0 to 1.0)
        """
        # Convert to float and normalize
        samples_float = samples.astype(np.float64)
        if samples.dtype == np.int16:
            samples_float = samples_float / 32768.0

        duration = len(samples) / sample_rate

        # 1. Energy (RMS) - normalized
        energy = np.sqrt(np.mean(samples_float ** 2))
        energy_norm = min(energy * 180, 1.0)

        # 2. Zero Crossing Rate - normalized
        zcr = np.sum(np.abs(np.diff(np.sign(samples_float)))) / (2 * len(samples_float))
        zcr_norm = min(zcr * 4, 1.0)

        # 3. Spectral Centroid
        if _SCIPY_AVAILABLE and len(samples) >= 2048:
            fft_size = min(2048, len(samples))
            freqs = np.fft.rfftfreq(fft_size, 1 / sample_rate)
            fft_mag = np.abs(np.fft.rfft(samples_float[:fft_size]))
            centroid = np.sum(freqs * fft_mag) / (np.sum(fft_mag) + 1e-10)
            centroid_norm = min(centroid / 400, 1.0)
        else:
            centroid_norm = 0.5

        # 4. Pitch Variance (using autocorrelation)
        pitch_variance = self._estimate_pitch_variance(samples_float, sample_rate)
        pitch_var_norm = min(pitch_variance / 40, 1.0)

        # 5. Speech Rate (voiced frames estimation)
        frame_size = int(0.03 * sample_rate)  # 30ms frames
        hop_size = int(0.01 * sample_rate)    # 10ms hop
        voiced_frames = 0

        for i in range(0, len(samples_float) - frame_size, hop_size):
            frame = samples_float[i:i + frame_size]
            frame_energy = np.sum(frame ** 2)
            frame_zcr = np.sum(np.abs(np.diff(np.sign(frame)))) / (2 * len(frame))
            # Voiced if energy is high and ZCR is low
            if frame_energy > 0.001 and frame_zcr < 0.1:
                voiced_frames += 1

        total_frames = max(1, len(samples_float) // hop_size)
        speech_rate = (voiced_frames * 0.15) / duration if duration > 0 else 0
        speech_rate_norm = min(speech_rate / 6, 1.0)

        return {
            "energy": energy_norm,
            "zcr": zcr_norm,
            "spectral_centroid": centroid_norm,
            "pitch_variance": pitch_var_norm,
            "speech_rate": speech_rate_norm,
            "duration": duration,
        }

    def _estimate_pitch_variance(self, samples: np.ndarray, sample_rate: int) -> float:
        """Estimate pitch variance using autocorrelation."""
        frame_size = 1024
        min_lag = int(sample_rate / 500)  # 500Hz max
        max_lag = int(sample_rate / 50)   # 50Hz min

        pitches = []
        for i in range(0, len(samples) - frame_size * 2, frame_size):
            frame = samples[i:i + frame_size]
            # Autocorrelation
            corr = np.correlate(frame, frame, mode='full')
            corr = corr[len(corr) // 2:]

            # Find peak in range
            if len(corr) > max_lag:
                peak_region = corr[min_lag:max_lag]
                if len(peak_region) > 0:
                    peak_idx = np.argmax(peak_region)
                    if peak_region[peak_idx] > 0:
                        lag = min_lag + peak_idx
                        pitch = sample_rate / lag
                        pitches.append(pitch)

        if len(pitches) < 2:
            return 0.0

        # Return variance
        return np.var(pitches)

    def detect(self, samples: np.ndarray, sample_rate: int = 16000) -> Tuple[str, float]:
        """
        Detect emotion from audio samples.

        Args:
            samples: Audio samples as numpy array
            sample_rate: Sample rate in Hz

        Returns:
            Tuple of (emotion_str, confidence_float)
        """
        features = self.extract_features(samples, sample_rate)

        duration = features["duration"]
        energy = features["energy"]

        # Skip if too short or too quiet
        if duration < self.min_speech_duration or energy < self.energy_threshold:
            return ("neutral", 0.0)

        # Calculate arousal and valence
        arousal = (features["energy"] + features["speech_rate"] + features["zcr"]) / 3
        valence = features["pitch_variance"] - features["zcr"] * 0.5

        # Decision tree
        if arousal > 0.7 and valence > 0.3:
            emotion = "excited"
            confidence = min(0.6 + arousal * 0.3, 0.95)
        elif arousal > 0.7 and valence <= 0.3:
            emotion = "angry"
            confidence = min(0.5 + arousal * 0.3, 0.95)
        elif arousal < 0.3 and features["pitch_variance"] < 0.2 and features["speech_rate"] < 0.3:
            emotion = "sad"
            confidence = min(0.5 + (1 - arousal) * 0.3, 0.95)
        elif arousal < 0.3:
            emotion = "calm"
            confidence = min(0.5 + (1 - arousal) * 0.2, 0.95)
        elif 0.3 <= arousal <= 0.7 and features["pitch_variance"] > 0.5 and features["spectral_centroid"] > 0.4:
            emotion = "happy"
            confidence = min(0.4 + features["pitch_variance"] * 0.3, 0.95)
        else:
            emotion = "neutral"
            confidence = min(0.6, 0.95)

        return (emotion, confidence)


if __name__ == "__main__":
    print("[INFO] Testando AudioEmotionDetector...")

    detector = AudioEmotionDetector()

    # Test with synthetic data
    sample_rate = 16000

    # Generate different types of synthetic audio
    tests = [
        ("neutral", np.random.normal(0, 0.1, 16000)),
        ("excited", np.random.normal(0, 0.5, 16000) + np.sin(2 * np.pi * 200 * np.arange(16000) / sample_rate) * 0.3),
        ("calm", np.random.normal(0, 0.05, 16000)),
    ]

    for name, audio in tests:
        audio_int16 = (audio * 32767).astype(np.int16)
        emotion, conf = detector.detect(audio_int16, sample_rate)
        features = detector.extract_features(audio_int16, sample_rate)
        print(f"  Test {name}: detected={emotion} (conf={conf:.2f}), energy={features['energy']:.2f}, arousal={(features['energy']+features['speech_rate']+features['zcr'])/3:.2f}")

    print("[INFO] AudioEmotionDetector pronto")
