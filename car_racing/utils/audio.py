import pygame
import math
import struct
import random
import os

class AudioSystem:
    def __init__(self):
        self.muted = False
        self.mixer_initialized = False
        self.sounds = {}
        self.engine_channel = None
        self.music_channel = None
        
        # Initialize mixer
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            self.mixer_initialized = True
        except Exception as e:
            print(f"Warning: Could not initialize pygame.mixer (no audio device?): {e}")
            self.mixer_initialized = False
            return
            
        # Synthesize/load sounds
        self._setup_sounds()

    @staticmethod
    def _pack_sample(value):
        """Clamp to signed 16-bit range before packing."""
        clamped = max(-32768, min(32767, int(value)))
        return struct.pack('<h', clamped)

    def _setup_sounds(self):
        assets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "sounds")
        
        # Helper to load file or fallback
        sound_configs = {
            'engine': (self._synthesize_engine, "engine.wav"),
            'crash': (self._synthesize_crash, "crash.wav"),
            'score': (self._synthesize_score, "score.wav"),
            'music': (self._synthesize_music_loop, "music.wav"),
            'powerup': (self._synthesize_powerup, "powerup.wav"),
            'shield_break': (self._synthesize_shield_break, "shield_break.wav"),
            'fanfare': (self._synthesize_fanfare, "fanfare.wav")
        }
        
        for name, (synth_fn, filename) in sound_configs.items():
            path = os.path.join(assets_dir, filename)
            if os.path.exists(path):
                try:
                    self.sounds[name] = pygame.mixer.Sound(path)
                except Exception:
                    self.sounds[name] = synth_fn()
            else:
                self.sounds[name] = synth_fn()

    def _synthesize_engine(self):
        sample_rate = 22050
        duration = 0.15
        num_samples = int(duration * sample_rate)
        buffer = bytearray()
        
        for i in range(num_samples):
            t = i / sample_rate
            sine_val = math.sin(2 * math.pi * 65.0 * t)
            square_val = 1.0 if math.sin(2 * math.pi * 130.0 * t) > 0 else -1.0
            value = int(32767 * 0.15 * (sine_val * 0.6 + square_val * 0.4))
            buffer.extend(self._pack_sample(value))
            
        try:
            return pygame.mixer.Sound(buffer=bytes(buffer))
        except Exception:
            return None

    def _synthesize_crash(self):
        sample_rate = 22050
        duration = 0.5
        num_samples = int(duration * sample_rate)
        buffer = bytearray()
        
        for i in range(num_samples):
            decay = (num_samples - i) / num_samples
            noise = random.uniform(-32767, 32767)
            value = int(noise * 0.35 * (decay ** 2))
            buffer.extend(self._pack_sample(value))
            
        try:
            return pygame.mixer.Sound(buffer=bytes(buffer))
        except Exception:
            return None

    def _synthesize_score(self):
        sample_rate = 22050
        duration = 0.25
        num_samples = int(duration * sample_rate)
        buffer = bytearray()
        
        for i in range(num_samples):
            t = i / sample_rate
            decay = (num_samples - i) / num_samples
            if t < 0.08:
                freq = 1046.5
            elif t < 0.16:
                freq = 1318.5
            else:
                freq = 1568.0
                
            sine_val = math.sin(2 * math.pi * freq * t)
            value = int(32767 * 0.22 * sine_val * decay)
            buffer.extend(self._pack_sample(value))
            
        try:
            return pygame.mixer.Sound(buffer=bytes(buffer))
        except Exception:
            return None

    def _synthesize_powerup(self):
        """Synthesizes a rising retro powerup chime sweep."""
        sample_rate = 22050
        duration = 0.35
        num_samples = int(duration * sample_rate)
        buffer = bytearray()
        
        for i in range(num_samples):
            t = i / sample_rate
            decay = (num_samples - i) / num_samples
            # Sweep frequency upward fast from 587.3Hz (D5) to 1174.7Hz (D6)
            freq = 587.33 + (1174.66 - 587.33) * (t / duration)
            sine_val = math.sin(2 * math.pi * freq * t)
            # Add secondary higher harmonic for a bright chime
            sine_val2 = math.sin(2 * math.pi * freq * 1.5 * t)
            
            value = int(32767 * 0.2 * (sine_val * 0.7 + sine_val2 * 0.3) * decay)
            buffer.extend(self._pack_sample(value))
            
        try:
            return pygame.mixer.Sound(buffer=bytes(buffer))
        except Exception:
            return None

    def _synthesize_shield_break(self):
        """Synthesizes a metallic glass-shatter crash."""
        sample_rate = 22050
        duration = 0.4
        num_samples = int(duration * sample_rate)
        buffer = bytearray()
        
        for i in range(num_samples):
            t = i / sample_rate
            decay = (num_samples - i) / num_samples
            noise = random.uniform(-1.0, 1.0)
            metallic = math.sin(2 * math.pi * 3500.0 * t) * math.sin(2 * math.pi * 500.0 * t)
            value = 32767 * 0.24 * (noise * 0.4 + metallic * 0.6) * decay
            buffer.extend(self._pack_sample(value))
            
        try:
            return pygame.mixer.Sound(buffer=bytes(buffer))
        except Exception:
            return None

    def _synthesize_fanfare(self):
        """Synthesizes a major-triad retro-arcade triumphant jingle."""
        sample_rate = 22050
        duration = 0.95
        num_samples = int(duration * sample_rate)
        buffer = bytearray()
        
        # Major chord tones: C5, E5, G5, C6
        notes = [523.25, 659.25, 783.99, 1046.50]
        
        for i in range(num_samples):
            t = i / sample_rate
            # 4 beats
            note_idx = min(3, int(t * 4.5))
            freq = notes[note_idx]
            
            # Triangle approximation + sine mix
            sine_val = math.sin(2 * math.pi * freq * t)
            tri_val = 1.0 - 4.0 * abs(round(t * freq - 0.5) - (t * freq - 0.5))
            mixed = sine_val * 0.5 + tri_val * 0.5
            
            # Decaying pulse per beat
            beat_t = t % (0.95 / 4.5)
            beat_decay = math.exp(-beat_t * 8.0)
            
            value = int(32767 * 0.16 * mixed * beat_decay)
            buffer.extend(self._pack_sample(value))
            
        try:
            return pygame.mixer.Sound(buffer=bytes(buffer))
        except Exception:
            return None

    def _synthesize_music_loop(self):
        sample_rate = 22050
        duration = 4.0
        num_samples = int(duration * sample_rate)
        buffer = bytearray()
        
        chords = [
            (220.0, 277.18, 329.63),
            (174.61, 220.0, 261.63),
            (261.63, 329.63, 392.00),
            (196.00, 246.94, 293.66)
        ]
        
        for i in range(num_samples):
            t = i / sample_rate
            chord_idx = int(t) % 4
            base_f1, base_f2, base_f3 = chords[chord_idx]
            
            bass = math.sin(2 * math.pi * (base_f1 / 2.0) * t)
            
            note_time = (t * 4.0) % 1.0
            if note_time < 0.25:
                arp_f = base_f1
            elif note_time < 0.5:
                arp_f = base_f2
            elif note_time < 0.75:
                arp_f = base_f3
            else:
                arp_f = base_f2 * 2.0
                
            arp = math.sin(2 * math.pi * arp_f * t)
            arp_square = 0.5 * arp + 0.5 * (1.0 if arp > 0 else -1.0)
            
            mixed = (bass * 0.4) + (arp_square * 0.15)
            value = int(32767 * 0.12 * mixed)
            buffer.extend(self._pack_sample(value))
            
        try:
            return pygame.mixer.Sound(buffer=bytes(buffer))
        except Exception:
            return None

    def play_sound(self, name):
        if not self.mixer_initialized or self.muted:
            return
        sound = self.sounds.get(name)
        if sound:
            try:
                sound.play()
            except Exception:
                pass

    def start_engine(self):
        if not self.mixer_initialized:
            return
        sound = self.sounds.get('engine')
        if sound and not self.engine_channel:
            try:
                self.engine_channel = sound.play(loops=-1)
                if self.engine_channel and self.muted:
                    self.engine_channel.set_volume(0.0)
                elif self.engine_channel:
                    self.engine_channel.set_volume(0.2)
            except Exception:
                self.engine_channel = None

    def stop_engine(self):
        if self.engine_channel:
            try:
                self.engine_channel.stop()
            except Exception:
                pass
            self.engine_channel = None

    def start_music(self):
        if not self.mixer_initialized:
            return
        sound = self.sounds.get('music')
        if sound and not self.music_channel:
            try:
                self.music_channel = sound.play(loops=-1)
                if self.music_channel and self.muted:
                    self.music_channel.set_volume(0.0)
                elif self.music_channel:
                    self.music_channel.set_volume(0.4)
            except Exception:
                self.music_channel = None

    def stop_music(self):
        if self.music_channel:
            try:
                self.music_channel.stop()
            except Exception:
                pass
            self.music_channel = None

    def toggle_mute(self):
        self.muted = not self.muted
        if not self.mixer_initialized:
            return
            
        vol_engine = 0.0 if self.muted else 0.2
        vol_music = 0.0 if self.muted else 0.4
        
        if self.engine_channel:
            try:
                self.engine_channel.set_volume(vol_engine)
            except Exception:
                pass
        if self.music_channel:
            try:
                self.music_channel.set_volume(vol_music)
            except Exception:
                pass
                
        for s in self.sounds.values():
            if s:
                try:
                    s.set_volume(0.0 if self.muted else 0.5)
                except Exception:
                    pass
                    
        return self.muted
