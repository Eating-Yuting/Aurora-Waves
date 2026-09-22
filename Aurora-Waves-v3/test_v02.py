# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib", "numpy"]
# ///
"""Regression test: v02 smoothing must not fill telemetry gaps."""
import numpy as np
from aurora_waves_v02 import curtain_samples, veil_geometry, runs
from aurora_waves import load_wind


def main():
    # Synthetic values are used only for this test, never for the artwork.
    t=np.arange(9)*300.
    v=np.tile([330.,2.,50000.,4.,-2.],(9,1));v[3:6]=np.nan
    dense_t,dense,smooth=curtain_samples(t,v,width=241)
    gap=(dense_t>t[2])&(dense_t<t[6])
    assert np.isnan(dense[gap]).all()
    assert np.isnan(smooth[3:6]).all()
    assert np.allclose(smooth[:3],v[:3]) and np.allclose(smooth[6:],v[6:])
    assert runs([True,False,True])==[(0,1),(2,3)]
    _,single,_=curtain_samples(t,np.where(np.arange(9)[:,None]==4,v[0],np.nan),width=241)
    assert np.isfinite(single).all(axis=1).sum()==1
    # The three independent encodings respond in the documented direction.
    edge,reach,bright=veil_geometry(np.array([[300,2,50000,0,-5],[380,2,50000,6,5]]))
    assert edge[0]<edge[1] and reach[0]<reach[1] and bright[0]<bright[1]
    rt,rv,_=load_wind();dt,dv,sv=curtain_samples(rt,rv)
    for a,b in runs(~np.isfinite(rv).all(axis=1)):
        assert np.isnan(dv[(dt>=rt[a])&(dt<=rt[b-1])]).all()
    assert np.isfinite(sv).all(axis=1).sum()==np.isfinite(rv).all(axis=1).sum()
    print('PASS: v02 keeps gaps, handles isolated bins, and preserves encoding directions')


if __name__=='__main__': main()
