from __future__ import annotations

from pathlib import Path

import pygame

from settings import ASSETS_DIR


class AudioManager:
    MUSIC_TRACKS = {
        "system_main_menu": ASSETS_DIR / "audio" / "system_audio" / "system_main_menu.mp3",
        "world_ambience": ASSETS_DIR / "audio" / "world_audio" / "world_ambience.mp3",
    }
    SOUND_EFFECTS = {
        "hero_footsteps": ASSETS_DIR / "audio" / "hero_audio" / "hero_footsteps.mp3",
        "hero_running": ASSETS_DIR / "audio" / "hero_audio" / "hero_running.mp3",
        "hero_attack": ASSETS_DIR / "audio" / "hero_audio" / "hero_attack.wav",
        "hero_dash": ASSETS_DIR / "audio" / "hero_audio" / "hero_dash.wav",
        "hero_jump": ASSETS_DIR / "audio" / "hero_audio" / "hero_jump.wav",
        "hero_item_pickup": ASSETS_DIR / "audio" / "hero_audio" / "hero_item_pickup.mp3",
        "hero_lvlup": ASSETS_DIR / "audio" / "hero_audio" / "hero_lvlup.mp3",
        "hero_quest_accepted": ASSETS_DIR / "audio" / "hero_audio" / "hero_quest_accepted.mp3",
        "checkpoint_activation": ASSETS_DIR / "audio" / "world_audio" / "checkpoint_activation.wav",
        "teleport_sound": ASSETS_DIR / "audio" / "world_audio" / "teleport_sound.wav",
        "enemy_attack": ASSETS_DIR / "audio" / "enemy_audio" / "enemy_attack.wav",
        "beetle_healing": ASSETS_DIR / "audio" / "enemy_audio" / "beetle_healing.wav",
        "enemy_steps": ASSETS_DIR / "audio" / "enemy_audio" / "enemy_steps.wav",
        "spider_web_attack": ASSETS_DIR / "audio" / "enemy_audio" / "spider_web_attack.wav",
        "wasp_range_attack": ASSETS_DIR / "audio" / "enemy_audio" / "wasp_range_attack.wav",
        "boss_attack": ASSETS_DIR / "audio" / "boss_audio" / "boss_attact.wav",
        "boss_die": ASSETS_DIR / "audio" / "boss_audio" / "boss_die.wav",
        "boss_leap": ASSETS_DIR / "audio" / "boss_audio" / "boss_leap.wav",
        "boss_range_attack": ASSETS_DIR / "audio" / "boss_audio" / "boss_range_attack.wav",
        "boss_steps": ASSETS_DIR / "audio" / "boss_audio" / "boss_steps.wav",
        "boss_roar_splash": ASSETS_DIR / "audio" / "boss_audio" / "boss_roar_splash.wav",
        "campfire_ambience": ASSETS_DIR / "audio" / "world_audio" / "campfire_ambience.mp3",
    }

    def __init__(self, music_volume=0.7, sfx_volume=0.8):
        self.available = False
        self.music_volume = self._clamp_volume(music_volume)
        self.sfx_volume = self._clamp_volume(sfx_volume)
        self.current_music_key = None
        self.sound_cache: dict[str, pygame.mixer.Sound | None] = {}
        self.loop_channels: dict[str, dict] = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            pygame.mixer.set_num_channels(max(32, pygame.mixer.get_num_channels()))
            self.available = True
            pygame.mixer.music.set_volume(self.music_volume)
        except pygame.error:
            self.available = False

    def set_music_volume(self, value):
        self.music_volume = self._clamp_volume(value)
        if self.available:
            pygame.mixer.music.set_volume(self.music_volume)
        return self.music_volume

    def set_sfx_volume(self, value):
        self.sfx_volume = self._clamp_volume(value)
        for loop_info in self.loop_channels.values():
            channel = loop_info.get("channel")
            if channel is None:
                continue
            channel.set_volume(self.sfx_volume * loop_info.get("volume", 1.0))
        return self.sfx_volume

    def play_music(self, key, loops=-1):
        if not self.available:
            return False
        track_path = self.MUSIC_TRACKS.get(str(key))
        if track_path is None or not Path(track_path).exists():
            return False
        if self.current_music_key == key and pygame.mixer.music.get_busy():
            return True
        try:
            pygame.mixer.music.load(str(track_path))
            pygame.mixer.music.set_volume(self.music_volume)
            pygame.mixer.music.play(loops)
            self.current_music_key = key
            return True
        except pygame.error:
            return False

    def stop_music(self):
        if not self.available:
            return
        pygame.mixer.music.stop()
        self.current_music_key = None

    def play_sound(self, key, volume=1.0):
        if not self.available:
            return False
        sound = self._get_sound(key)
        if sound is None:
            return False
        channel = sound.play()
        if channel is None:
            return False
        channel.set_volume(self.sfx_volume * self._clamp_volume(volume))
        return True

    def ensure_loop(self, key, loop_id, volume=1.0):
        if not self.available:
            return False
        sound = self._get_sound(key)
        if sound is None:
            return False
        normalized_loop_id = str(loop_id)
        normalized_volume = self._clamp_volume(volume)
        existing = self.loop_channels.get(normalized_loop_id)
        if existing is not None:
            channel = existing.get("channel")
            if channel is not None and channel.get_busy() and existing.get("sound_key") == key:
                channel.set_volume(self.sfx_volume * normalized_volume)
                existing["volume"] = normalized_volume
                return True
            self.stop_loop(normalized_loop_id)
        channel = sound.play(loops=-1)
        if channel is None:
            return False
        channel.set_volume(self.sfx_volume * normalized_volume)
        self.loop_channels[normalized_loop_id] = {
            "channel": channel,
            "sound_key": key,
            "volume": normalized_volume,
        }
        return True

    def stop_loop(self, loop_id):
        loop_info = self.loop_channels.pop(str(loop_id), None)
        if loop_info is None:
            return
        channel = loop_info.get("channel")
        if channel is not None:
            channel.stop()

    def stop_all_loops(self):
        for loop_id in list(self.loop_channels):
            self.stop_loop(loop_id)

    def _get_sound(self, key):
        normalized_key = str(key)
        if normalized_key in self.sound_cache:
            return self.sound_cache[normalized_key]
        sound_path = self.SOUND_EFFECTS.get(normalized_key)
        if sound_path is None or not Path(sound_path).exists():
            self.sound_cache[normalized_key] = None
            return None
        try:
            self.sound_cache[normalized_key] = pygame.mixer.Sound(str(sound_path))
        except pygame.error:
            self.sound_cache[normalized_key] = None
        return self.sound_cache[normalized_key]

    def _clamp_volume(self, value):
        return max(0.0, min(1.0, float(value)))
