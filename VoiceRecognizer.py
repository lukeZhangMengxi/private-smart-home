#!/usr/bin/env python3

import json
import queue
import sys
import sounddevice as sd
import time

from enum import Enum
from vosk import Model, KaldiRecognizer

class Actions(Enum):
    ACTION_LIGHT_ON = {"light on", "lights on", "turn on the light"}
    ACTION_LIGHT_OFF = {"light off", "lights off", "turn off the light"}

class VoiceRecognizer:
    def __init__(self, device_num: int):
        self.device_num = device_num
        self.samplerate = int(sd.query_devices(device_num, "input")["default_samplerate"])
        self.q = queue.Queue()
        self.model = Model(lang="en-us")

    def _callback(self, indata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        self.q.put(bytes(indata))
    
    def start_recognize_speech_for_seconds(self, seconds):
        with sd.RawInputStream(samplerate=self.samplerate, blocksize = 8000, device=self.device_num,
            dtype="int16", channels=1, callback=self._callback):

            end_time = int(time.time()) + seconds
            rec = KaldiRecognizer(self.model, self.samplerate)
            while int(time.time()) < end_time:
                data = self.q.get()
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())["text"]
                else:
                    result = json.loads(rec.PartialResult())["partial"]

                done = False
                for action in Actions:
                    if result in action.value:
                        print(action.name)
                        done = True
                if done:
                    break



def main():
    a = VoiceRecognizer(0)
    a.start_recognize_speech_for_seconds(10)


if __name__ == "__main__":
    main()
