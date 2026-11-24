import numpy as np, wave, subprocess, sys
SR=24000
NOTES={'C':-9,'D':-7,'E':-5,'F':-4,'G':-2,'A':0,'B':2}
def freq(n):
    if n=='R': return 0
    name=n[0]; acc=0; i=1
    if len(n)>2 and n[1] in '#b': acc=1 if n[1]=='#' else -1; i=2
    octv=int(n[i:])
    return 440*2**((NOTES[name]+acc+(octv-4)*12)/12)
def tone(f,dur,vol=0.35):
    t=np.arange(int(SR*dur))/SR
    if f==0: return np.zeros_like(t)
    w=np.sin(2*np.pi*f*t)+0.35*np.sin(4*np.pi*f*t)+0.15*np.sin(6*np.pi*f*t)
    env=np.minimum(1,t/0.01)*np.exp(-t*2.2)
    rel=np.minimum(1,(dur-t)/0.04)
    return vol*w*env*np.clip(rel,0,1)/1.5
def drums(n_beats,bpm,pattern='4'):
    beat=60/bpm; out=np.zeros(int(SR*beat*n_beats)+SR)
    t=np.arange(int(SR*0.18))/SR
    kick=0.6*np.sin(2*np.pi*(55+90*np.exp(-t*30))*t)*np.exp(-t*18)
    tl=np.arange(int(SR*0.06))/SR
    hat=0.12*np.random.default_rng(1).standard_normal(len(tl))*np.exp(-tl*60)
    for b in range(n_beats):
        s=int(b*beat*SR); out[s:s+len(kick)]+=kick
        h=int((b+0.5)*beat*SR); out[h:h+len(hat)]+=hat
    return out
def song(melody,bpm,name,bass=None,beat=True):
    b=60/bpm; parts=[tone(freq(n),d*b) for n,d in melody]; mel=np.concatenate(parts)
    total_beats=int(sum(d for _,d in melody)+0.999)
    mix=np.zeros(len(mel)+SR); mix[:len(mel)]+=mel
    if bass:
        bs=np.concatenate([tone(freq(n),d*b,0.25) for n,d in bass]); mix[:min(len(bs),len(mix))]+=bs[:len(mix)]
    if beat:
        dr=drums(total_beats,bpm); mix[:min(len(dr),len(mix))]+=dr[:len(mix)]
    mix=mix/np.max(np.abs(mix))*0.85
    pcm=(mix*32767).astype(np.int16)
    with wave.open(name+'.wav','wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    subprocess.run(['ffmpeg','-y','-loglevel','error','-i',name+'.wav','-c:a','libopus','-b:a','24k','-ac','1','-ar','24000','-frame_duration','60',name+'.ogg'],check=True)
    print(name, round(len(pcm)/SR,1),'s', bpm,'bpm')
def P(s): # "E4:1 D4:0.5 ..."
    return [(x.split(':')[0],float(x.split(':')[1])) for x in s.split()]
# Chúc mừng sinh nhật (Happy Birthday, giai điệu phổ thông, public domain)
hb=P("G4:0.75 G4:0.25 A4:1 G4:1 C5:1 B4:2 G4:0.75 G4:0.25 A4:1 G4:1 D5:1 C5:2 G4:0.75 G4:0.25 G5:1 E5:1 C5:1 B4:1 A4:2 F5:0.75 F5:0.25 E5:1 C5:1 D5:1 C5:3")
song(hb,110,'sinh_nhat')
# Kìa con bướm vàng (dân ca, giai điệu Frère Jacques)
bv=P("C5:1 D5:1 E5:1 C5:1 C5:1 D5:1 E5:1 C5:1 E5:1 F5:1 G5:2 E5:1 F5:1 G5:2 G5:0.5 A5:0.5 G5:0.5 F5:0.5 E5:1 C5:1 G5:0.5 A5:0.5 G5:0.5 F5:0.5 E5:1 C5:1 C5:1 G4:1 C5:2 C5:1 G4:1 C5:2")
song(bv,128,'buom_vang')
# Twinkle Twinkle Little Star (public domain)
tw=P("C5:1 C5:1 G5:1 G5:1 A5:1 A5:1 G5:2 F5:1 F5:1 E5:1 E5:1 D5:1 D5:1 C5:2 G5:1 G5:1 F5:1 F5:1 E5:1 E5:1 D5:2 G5:1 G5:1 F5:1 F5:1 E5:1 E5:1 D5:2 C5:1 C5:1 G5:1 G5:1 A5:1 A5:1 G5:2 F5:1 F5:1 E5:1 E5:1 D5:1 D5:1 C5:2")
song(tw,120,'ngoi_sao')
# Jingle Bells (public domain)
jb=P("E5:1 E5:1 E5:2 E5:1 E5:1 E5:2 E5:1 G5:1 C5:1.5 D5:0.5 E5:4 F5:1 F5:1 F5:1.5 F5:0.5 F5:1 E5:1 E5:1 E5:0.5 E5:0.5 E5:1 D5:1 D5:1 E5:1 D5:2 G5:2 E5:1 E5:1 E5:2 E5:1 E5:1 E5:2 E5:1 G5:1 C5:1.5 D5:0.5 E5:4 F5:1 F5:1 F5:1.5 F5:0.5 F5:1 E5:1 E5:1 E5:0.5 E5:0.5 G5:1 G5:1 F5:1 D5:1 C5:4")
song(jb,140,'giang_sinh')
# Nhạc nhảy QBK (giai điệu tự sáng tác)
riff="A4:0.5 C5:0.5 E5:0.5 A5:0.5 G5:0.5 E5:0.5 D5:0.5 E5:0.5 "
dance=P((riff+"F4:0.5 A4:0.5 C5:0.5 F5:0.5 E5:0.5 C5:0.5 B4:0.5 C5:0.5 ")*4+"A5:1 G5:1 E5:1 C5:1 D5:1 E5:1 A4:2")
bass=P(("A2:2 A2:2 F2:2 F2:2 ")*4+"A2:4 E2:4")
song(dance,124,'nhac_nhay',bass=bass)
