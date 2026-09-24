"""Original score: The Celestial Challenge. No samples or borrowed melodies.
Regenerate with Python + NumPy; output is standard mono 22.05kHz PCM for both apps.
"""
from pathlib import Path
import math
import wave
import numpy as np

RATE = 22050
BEAT = 60 / 76
BAR = BEAT * 4
BARS = 64
DURATION = BAR * BARS
ROOT = Path(__file__).resolve().parents[1]

def compose():
    audio = np.zeros(round(DURATION * RATE), dtype=np.float64)
    def voice(onset, pitch, length, gain, instrument):
        start = round(onset * RATE)
        n = min(round(length * RATE), len(audio) - start)
        if n <= 0: return
        t = np.arange(n) / RATE
        f = 440 * 2 ** ((pitch - 69) / 12)
        phase = 2 * np.pi * f * t
        if instrument == 'strings':
            tone = sum(np.sin(phase * h + .002 * np.sin(t * 4.7)) / h**2 for h in range(1, 5))
            env = np.minimum(t / .7, 1) * np.minimum((length-t)/.8, 1)
        elif instrument == 'flute':
            tone = np.sin(phase + .012*np.sin(t*31)) + .1*np.sin(phase*2)
            env = np.minimum(t/.12, 1) * np.minimum((length-t)/.25, 1)
        elif instrument == 'bell':
            tone = np.sin(phase) + .2*np.sin(phase*2.76)*np.exp(-t*4)
            env = np.minimum(t/.009,1)*np.exp(-t*2.4)*np.minimum((length-t)/.2,1)
        else:
            tone = np.sin(phase)+.24*np.sin(phase*2)+.06*np.sin(phase*3)
            env = np.minimum(t/.012,1)*np.exp(-t*3)*np.minimum((length-t)/.15,1)
        audio[start:start+n] += gain * tone * np.maximum(0,env)
    # Eight distinct harmonic scenes: arrival, inquiry, discovery, ascent,
    # moonlit interlude, resolve, final challenge and a quiet returning cadence.
    progressions = [
        [(50,57,62,65),(46,53,60,65),(53,60,64,69),(48,55,62,64),(43,50,58,62),(46,53,57,62),(45,52,61,64),(50,57,62,65)],
        [(55,62,65,69),(48,55,60,64),(53,60,65,69),(46,53,62,65),(55,62,67,70),(52,59,64,67),(45,52,61,67),(50,57,62,65)],
        [(53,60,65,69),(48,55,64,67),(46,53,62,65),(50,57,65,69),(43,50,58,65),(48,55,62,67),(45,52,61,64),(50,57,62,65)],
        [(58,65,70,74),(53,60,69,72),(55,62,70,74),(50,57,65,69),(46,53,62,65),(48,55,64,67),(45,52,61,67),(50,57,62,65)],
        [(43,50,57,62),(46,53,60,65),(48,55,62,67),(50,57,64,69),(43,50,58,62),(52,59,64,67),(45,52,61,64),(50,57,62,65)],
        [(50,57,62,66),(55,62,66,69),(52,59,64,67),(45,52,61,64),(50,57,62,66),(47,54,62,66),(43,50,59,62),(45,52,61,64)],
        [(50,57,62,65),(53,60,65,69),(58,65,69,74),(55,62,67,70),(52,59,64,67),(46,53,62,65),(45,52,61,67),(50,57,62,65)],
        [(53,60,65,69),(48,55,64,67),(46,53,60,65),(43,50,58,62),(50,57,62,65),(48,55,60,64),(45,52,61,64),(50,57,62,65)]
    ]
    melodies = [
        [74,77,72,69,70,74,77,76,74,69,72,65,67,70,73,74],
        [79,77,74,72,77,81,79,77,79,82,76,79,73,76,77,74],
        [77,81,84,79,82,77,74,77,79,74,72,76,73,76,74,69],
        [82,86,84,81,79,82,77,74,77,74,72,79,76,73,74,77],
        [67,74,70,65,72,67,69,76,74,70,71,67,73,69,65,62],
        [74,78,81,78,79,76,73,76,78,81,78,74,71,74,73,76],
        [77,81,84,81,86,82,79,82,83,79,77,74,76,73,77,74],
        [77,81,79,76,77,74,70,67,69,74,72,67,73,69,65,62]
    ]
    for section, progression in enumerate(progressions):
        for bar, chord in enumerate(progression):
            onset = (section*8+bar)*BAR
            density = .75 if section in (0,4,7) else 1
            for pitch in chord: voice(onset,pitch,BAR*1.35,.034*density,'strings')
            voice(onset,chord[0]-12,BAR*.95,.05,'strings')
            pattern = [0,2,1,3,2,1] if bar % 2 == 0 else [1,3,2,0,2]
            for i,index in enumerate(pattern):
                voice(onset+BEAT*(.15+i*.55),chord[index]+12,BEAT*1.6,.043*density,'harp')
            for i in range(2):
                voice(onset+BEAT*(.45+i*1.7),melodies[section][bar*2+i],BEAT*(1.3 if i==0 else 1.7),.049,'flute' if section in (1,3,4,5) else 'bell')
            if section in (2,3,6) and bar % 2 == 0:
                voice(onset+BEAT*2.7,chord[2]+24,BEAT*2,.022,'bell')
    # Wrap reverb tails around the loop rather than ending with an abrupt dry cutoff.
    dry = audio.copy()
    for delay,gain in [(.19,.15),(.37,.09),(.61,.055)]: audio += np.roll(dry, round(delay*RATE))*gain
    # Smooth the quiet opening/closing seam without a click; no repeated tiny phrase.
    fade = round(.5*RATE)
    audio[:fade] *= np.linspace(0,1,fade)
    audio[-fade:] *= np.linspace(1,0,fade)
    peak = np.max(np.abs(audio))
    audio *= .58 / max(peak,1e-9)
    pcm = np.rint(audio * 32767).astype('<i2')
    path = ROOT/'Apple/App/Audio/magical-library.wav'
    with wave.open(str(path),'wb') as stream:
        stream.setnchannels(1);stream.setsampwidth(2);stream.setframerate(RATE);stream.writeframes(pcm.tobytes())
    print(f'Original soundtrack: {DURATION:.2f}s; {BARS} bars; 8 developing sections; peak {np.max(abs(pcm))}')

if __name__ == '__main__': compose()
