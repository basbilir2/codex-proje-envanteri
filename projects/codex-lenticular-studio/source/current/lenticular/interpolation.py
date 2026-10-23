"""Bidirectional motion and guided piecewise affine morphing."""
import math

import cv2
import numpy as np


def linear(a):
    a = np.asarray(a, np.float32)/255
    return np.where(a <= .04045, a/12.92, ((a+.055)/1.055)**2.4)


def encoded(a):
    a = np.clip(a, 0, 1)
    return np.rint(255*np.where(a <= .0031308, a*12.92, 1.055*a**(1/2.4)-.055)).astype(np.uint8)


class Pair:
    def __init__(self, a, b):
        if a.shape != b.shape or a.ndim != 3 or a.shape[2] != 3 or a.dtype != np.uint8 or b.dtype != np.uint8:
            raise ValueError('İki fotoğraf aynı boyutlu RGB kareler olmalı.')
        self.a, self.b = a, b
        self.la, self.lb = linear(a), linear(b)
        self.same = np.array_equal(a, b)
        self.quality = dict(method='same_image', uncertain_fraction=0., warnings=[])

    def endpoint(self, t):
        if isinstance(t, bool) or not isinstance(t, (float, int)) or not math.isfinite(t) or not 0 <= t <= 1:
            raise ValueError('Ara kare zamanı 0–1 arasında olmalı.')
        if self.same or t == 0:
            return self.a.copy()
        if t == 1:
            return self.b.copy()
        return None


class MotionInterpolator(Pair):
    def __init__(self, a, b):
        super().__init__(a, b)
        self.h, self.w = a.shape[:2]
        self.x, self.y = np.meshgrid(np.arange(self.w, dtype=np.float32), np.arange(self.h, dtype=np.float32))
        ga, gb = [cv2.cvtColor(im, cv2.COLOR_RGB2GRAY) for im in (a, b)]
        self.shift, response = cv2.phaseCorrelate(ga.astype(np.float32), gb.astype(np.float32))
        dx, dy = self.shift
        warped = cv2.warpAffine(a, np.float32([[1,0,dx],[0,1,dy]]), (self.w,self.h), borderMode=cv2.BORDER_REPLICATE)
        self.translation = response > .6 and np.mean(np.abs(warped.astype(float)-b)) < 3
        if self.same:
            return
        if self.translation:
            self.quality = dict(method='verified_global_translation', uncertain_fraction=0., warnings=[])
            return
        dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
        self.ab = dis.calc(ga, gb, None)
        self.ba = dis.calc(gb, ga, None)
        back = cv2.remap(self.ba, self.x+self.ab[:,:,0], self.y+self.ab[:,:,1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        self.confidence = np.exp(-np.linalg.norm(self.ab+back, axis=2)/2).astype(np.float32)
        uncertain = float(np.mean(self.confidence < .5))
        self.quality = dict(method='bidirectional_DIS_flow', uncertain_fraction=uncertain,
            warnings=['Hareket eşleşmesi zayıf; nesne kenarlarını kontrol edin.'] if uncertain > .1 else [])

    def frame(self, t):
        endpoint = self.endpoint(t)
        if endpoint is not None:
            return endpoint
        if self.translation:
            dx, dy = self.shift
            wa = cv2.warpAffine(self.la, np.float32([[1,0,dx*t],[0,1,dy*t]]), (self.w,self.h), borderMode=cv2.BORDER_REPLICATE)
            wb = cv2.warpAffine(self.lb, np.float32([[1,0,-dx*(1-t)],[0,1,-dy*(1-t)]]), (self.w,self.h), borderMode=cv2.BORDER_REPLICATE)
            return encoded((1-t)*wa+t*wb)
        # Invert the intermediate forward map with fixed-point refinement.
        ax, ay = self.x.copy(), self.y.copy()
        bx, by = self.x.copy(), self.y.copy()
        for _ in range(4):
            fa = cv2.remap(self.ab, ax, ay, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
            fb = cv2.remap(self.ba, bx, by, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
            ax, ay = self.x-t*fa[:,:,0], self.y-t*fa[:,:,1]
            bx, by = self.x-(1-t)*fb[:,:,0], self.y-(1-t)*fb[:,:,1]
        wa = cv2.remap(self.la, ax, ay, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        wb = cv2.remap(self.lb, bx, by, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        ca = cv2.remap(self.confidence, ax, ay, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        reverse = cv2.remap(self.ab, self.x+self.ba[:,:,0], self.y+self.ba[:,:,1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        cb = cv2.remap(np.exp(-np.linalg.norm(self.ba+reverse,axis=2)/2).astype(np.float32), bx, by, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        ca *= (1-t)*((ax>=0)&(ax<=self.w-1)&(ay>=0)&(ay<=self.h-1))
        cb *= t*((bx>=0)&(bx<=self.w-1)&(by>=0)&(by<=self.h-1))
        denominator = ca+cb
        result = (wa*ca[:,:,None]+wb*cb[:,:,None])/np.maximum(denominator[:,:,None],1e-6)
        # Unresolved visibility is disclosed in quality; retain the nearer endpoint's warp.
        result[denominator<1e-4] = (wa if t<.5 else wb)[denominator<1e-4]
        return encoded(result)


class MeshMorph(Pair):
    def __init__(self, a, b, points):
        super().__init__(a, b)
        h, w = a.shape[:2]
        corners = [[0,0,0,0],[1,0,1,0],[1,1,1,1],[0,1,0,1]]
        values = np.asarray(points, dtype=float)
        if values.size and (values.ndim != 2 or values.shape[1] != 4 or not np.isfinite(values).all() or np.any((values<0)|(values>1))):
            raise ValueError('Morph noktaları [Ax,Ay,Bx,By] biçiminde 0–1 arasında olmalı.')
        if not len(points) and not self.same:
            raise ValueError('Morph için iki fotoğrafta en az bir eşleşen nokta seçin; hareket için Hareket motorunu kullanın.')
        rows = np.array(corners+list(points), dtype=np.float32)
        scale = np.array([w-1,h-1],np.float32)
        self.pa, self.pb = rows[:,:2]*scale, rows[:,2:]*scale
        middle = (self.pa+self.pb)/2
        if len(np.unique(middle,axis=0)) != len(middle):
            raise ValueError('Morph noktaları üst üste geliyor; farklı noktalar seçin.')
        subdiv = cv2.Subdiv2D((0,0,w,h))
        for p in middle:
            subdiv.insert(tuple(map(float,p)))
        self.triangles = []
        for triangle in subdiv.getTriangleList().reshape(-1,3,2):
            ids = np.linalg.norm(middle[:,None,:]-triangle[None,:,:],axis=2).argmin(0)
            if np.max(np.linalg.norm(middle[ids]-triangle,axis=1)) < .1:
                self.triangles.append(ids)
        for ids in self.triangles:
            # Signed area is quadratic in t; check extrema, not only endpoints.
            def area(t):
                p = (1-t)*self.pa[ids]+t*self.pb[ids]
                return float(np.cross(p[1]-p[0],p[2]-p[0]))
            c, end, mid = area(0), area(1), area(.5)
            aa = 2*(end+c-2*mid); bb = end-c-aa
            ts = [0,1]
            if abs(aa)>1e-8 and 0 < -bb/(2*aa) < 1:
                ts.append(-bb/(2*aa))
            if abs(c)<.01 or any(area(t)*c<=.01 for t in ts):
                raise ValueError('Morph noktaları yüzeyi katlıyor. Nokta eşleşmesini düzeltin.')
        self.quality = dict(method='guided_piecewise_affine_morph', uncertain_fraction=0., warnings=[])

    def frame(self, t):
        endpoint = self.endpoint(t)
        if endpoint is not None:
            return endpoint
        h,w = self.a.shape[:2]
        target = (1-t)*self.pa+t*self.pb
        result, coverage = np.zeros_like(self.la), np.zeros((h,w),np.float32)
        for ids in self.triangles:
            dest = target[ids]
            x,y,ww,hh = cv2.boundingRect(dest)
            x0,y0,x1,y1 = max(0,x),max(0,y),min(w,x+ww),min(h,y+hh)
            if x1<=x0 or y1<=y0:
                continue
            local = dest-np.array([x0,y0],np.float32)
            mask = np.zeros((y1-y0,x1-x0),np.float32)
            cv2.fillConvexPoly(mask,np.rint(local).astype(np.int32),1.)
            ma = cv2.getAffineTransform(self.pa[ids],local)
            mb = cv2.getAffineTransform(self.pb[ids],local)
            aa = cv2.warpAffine(self.la,ma,(x1-x0,y1-y0),borderMode=cv2.BORDER_REFLECT_101)
            bb = cv2.warpAffine(self.lb,mb,(x1-x0,y1-y0),borderMode=cv2.BORDER_REFLECT_101)
            result[y0:y1,x0:x1] += ((1-t)*aa+t*bb)*mask[:,:,None]
            coverage[y0:y1,x0:x1] += mask
        if np.any(coverage==0):
            raise ValueError('Morph yüzeyi tuvali tamamen kaplamadı; noktaları düzeltin.')
        return encoded(result/coverage[:,:,None])
