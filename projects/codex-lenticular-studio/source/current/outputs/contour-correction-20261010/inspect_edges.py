from pathlib import Path
import numpy as np,cv2,json
SRC=Path(__file__).resolve().parents[1]/'surface-upgrade-20261009-220345/native-portrait-final'
d=np.load(SRC/'depth_proximity.npy');h,w=d.shape
d=cv2.resize(d,(round(w*768/max(h,w)),round(h*768/max(h,w))),interpolation=cv2.INTER_AREA)
lo=[];hi=[]
for a,b in ((d[:,:-1],d[:,1:]),(d[:-1,:],d[1:,:])):
    jump=np.abs(a-b);keep=jump>.06
    lo.extend(np.minimum(a,b)[keep]);hi.extend(np.maximum(a,b)[keep])
lo=np.array(lo);hi=np.array(hi);cuts=[.20164476335048676,.4554727077484131]
for _ in range(4):
    covered=np.any([(lo<c)&(hi>c) for c in cuts],axis=0)
    a,b=lo[~covered],hi[~covered];weight=(b-a)**2
    candidates=np.linspace(float(d.min())+.01,float(d.max())-.01,256)
    scores=np.array([np.sum(weight[(a+.2*(b-a)<c)&(b-.2*(b-a)>c)]) for c in candidates])
    if not len(a):break
    best=np.argmax(scores);cut=float(candidates[best]);hits=(a<cut)&(b>cut)
    print(dict(cut=cut,edges=int(hits.sum()),remaining=len(a),score=float(scores[best]),range=[float(d.min()),float(d.max())]))
    cuts.append(cut)
print('cuts',sorted(cuts))
