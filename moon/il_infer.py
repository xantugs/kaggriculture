"""Imitation planner inference: per-tile job probabilities from an observation. numpy if available, else pure Python.
The model dict comes from the Kaggle training notebook (il_model.json)."""
import math

try:
    import numpy as _np
except Exception:
    _np = None


class ILModel:
    def __init__(self, model):
        self.m = model
        W = model['weights']
        self.labels = model['labels']
        self.th = model['thresholds']
        self.xmu, self.xsd = model['xmu'], model['xsd']
        self.gmu, self.gsd = model['gmu'], model['gsd']
        self.Wx, self.bx = W['wx.weight'], W['wx.bias']
        self.Wg = W['wg.weight']
        self.W2, self.b2 = W['l2.weight'], W['l2.bias']
        self.Wo, self.bo = W['out.weight'], W['out.bias']
        if _np is not None:
            self.np = {k: _np.asarray(v, dtype=_np.float64) for k, v in
                       dict(Wx=self.Wx, bx=self.bx, Wg=self.Wg, W2=self.W2, b2=self.b2, Wo=self.Wo, bo=self.bo,
                            xmu=self.xmu, xsd=self.xsd, gmu=self.gmu, gsd=self.gsd).items()}

    def predict_rows(self, X, G):
        """X: 100 tile rows, G: global vector. Returns 100 x NL probabilities."""
        if _np is not None:
            P = self.np
            x = (_np.asarray(X, dtype=_np.float64) - P['xmu']) / P['xsd']
            g = (_np.asarray(G, dtype=_np.float64) - P['gmu']) / P['gsd']
            h = _np.maximum(0.0, x @ P['Wx'].T + P['bx'] + P['Wg'] @ g)
            h = _np.maximum(0.0, h @ P['W2'].T + P['b2'])
            z = h @ P['Wo'].T + P['bo']
            return (1.0 / (1.0 + _np.exp(-z))).tolist()
        g = [(v - m) / s for v, m, s in zip(G, self.gmu, self.gsd)]
        gh = [sum(w * v for w, v in zip(row, g)) for row in self.Wg]
        out = []
        for xr in X:
            x = [(v - m) / s for v, m, s in zip(xr, self.xmu, self.xsd)]
            h = [max(0.0, sum(w * v for w, v in zip(row, x)) + b + gg) for row, b, gg in zip(self.Wx, self.bx, gh)]
            h2 = [max(0.0, sum(w * v for w, v in zip(row, h)) + b) for row, b in zip(self.W2, self.b2)]
            z = [sum(w * v for w, v in zip(row, h2)) + b for row, b in zip(self.Wo, self.bo)]
            out.append([1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, v)))) for v in z])
        return out

    def predict(self, obs, player, features, tile_inputs):
        cats, nums, rcats, G = features(obs, player)
        return self.predict_rows(tile_inputs(cats, nums, rcats, G), G), cats
