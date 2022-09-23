#!/usr/bin/env python3

import json
import queue
import sys
import sounddevice as sd
import soundfile as sf
import time

from enum import Enum
from vosk import Model, KaldiRecognizer


class Actions(Enum):
    ACTION_LIGHT_ON = {
        "lights on", "lights are",
        "light on", "like on", "like all", "like oh", "later on"
        "turn on the light", "turn on the night", "turn on the like", "her on the light", "her on the like", "her on the night"
    }
    ACTION_LIGHT_OFF = {
        "light off", "light of", "right off",
        "lights off",
        "turn off the light", "turn off the like"
    }


class VoiceAck:

    def __init__(self, after_woke_up_wav, after_understood_wav, after_confused_wav):
        (self.after_woke_up_data, self.after_woke_up_sr) = sf.read(after_woke_up_wav, dtype='float32')
        (self.after_understood_data, self.after_understood_sr) = sf.read(after_understood_wav, dtype='float32')
        (self.after_confused_data, self.after_confused_sr) = sf.read(after_confused_wav, dtype='float32')

    def voice_ack_after_woke_up(self):
        sd.play(self.after_woke_up_data, self.after_woke_up_sr)
        sd.wait()

    def voice_ack_after_understood(self):
        sd.play(self.after_understood_data, self.after_understood_sr)
        sd.wait()

    def voice_ack_after_confused(self):
        sd.play(self.after_confused_data, self.after_confused_sr)
        sd.wait()


class VoiceRecognizer:

    def __init__(self, device_num: int):
        self.device_num = device_num
        self.samplerate = int(sd.query_devices(device_num, "input")["default_samplerate"])
        self.q = queue.Queue()
        self.model = Model(lang="en-us")
        self.voice_ack = VoiceAck(
            after_woke_up_wav="resources/hello.wav",
            after_understood_wav="resources/yes.wav",
            after_confused_wav="resources/i-dont-understand.wav"
        )

    def _callback(self, indata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        self.q.put(bytes(indata))
    
    def start_recognize_speech_for_seconds(self, seconds):
        with sd.RawInputStream(samplerate=self.samplerate, blocksize = 8000, device=self.device_num,
            dtype="int16", channels=1, callback=self._callback):

            end_time = int(time.time()) + seconds
            rec = KaldiRecognizer(self.model, self.samplerate)

            ### Start detecting voice
            self.voice_ack.voice_ack_after_woke_up()
            unsertood = False

            while int(time.time()) < end_time:
                data = self.q.get()
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())["text"]
                else:
                    result = json.loads(rec.PartialResult())["partial"]
                
                # print("-----> " + result)

                for action in Actions:
                    if result in action.value:
                        print(action.name)
                        ### Figured out the voice action
                        self.voice_ack.voice_ack_after_understood()
                        unsertood = True
                if unsertood:
                    break
            
            if not unsertood:
                ### Did not figure out the voice action
                self.voice_ack.voice_ack_after_confused()


def main():
    a = VoiceRecognizer(0)
    a.start_recognize_speech_for_seconds(12)


if __name__ == "__main__":
    main()
