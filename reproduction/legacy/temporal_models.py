"""Equal-parameter residual CNN/TCN and subject-level fixed-window inference."""
import numpy as np
import torch
from torch import nn

WINDOW=128
class ChannelNorm(nn.Module):
    def __init__(self,width):
        super().__init__();self.norm=nn.LayerNorm(width)
    def forward(self,x):return self.norm(x.transpose(1,2)).transpose(1,2)

class ResidualBlock(nn.Module):
    def __init__(self,dilation):
        super().__init__()
        self.net=nn.Sequential(nn.Conv1d(32,32,5,padding=2*dilation,dilation=dilation),
            ChannelNorm(32),nn.GELU(),nn.Dropout(.15),
            nn.Conv1d(32,32,5,padding=2*dilation,dilation=dilation),
            ChannelNorm(32),nn.GELU(),nn.Dropout(.15))
    def forward(self,x):return x+self.net(x)

class TemporalNet(nn.Module):
    def __init__(self,kind):
        super().__init__();assert kind in ["cnn","tcn"]
        self.kind=kind;self.dilations=[1,1,1] if kind=="cnn" else [1,2,4]
        self.stem=nn.Sequential(nn.Conv1d(424,32,1),ChannelNorm(32),nn.GELU())
        self.blocks=nn.Sequential(*[ResidualBlock(d) for d in self.dilations])
        self.head=nn.Sequential(nn.Dropout(.3),nn.Linear(64,32),nn.GELU(),nn.Linear(32,1))
    def forward(self,x):
        h=self.blocks(self.stem(x))
        return self.head(torch.cat([h.mean(-1),h.std(-1,unbiased=False)],1)).flatten()

def window_starts(length,window=WINDOW,n=5):
    assert length>=window,"Scan too short; do not silently warp or pad"
    return np.unique(np.linspace(0,length-window,n).astype(np.int64))

class Series:
    def __init__(self,data,offsets):
        self.data=data;self.offsets=offsets;self.lengths=np.diff(offsets)
        assert len(data)==offsets[-1] and offsets[0]==0 and (self.lengths>=WINDOW).all()
    def batch(self,indices,starts):
        assert len(indices)==len(starts)
        output=[]
        for i,start in zip(indices,starts):
            assert 0<=start<=self.lengths[i]-WINDOW
            first=int(self.offsets[i]+start)
            output.append(self.data[first:first+WINDOW].T)
        return torch.from_numpy(np.stack(output).astype(np.float32,copy=False))

@torch.no_grad()
def predict_subjects(model,series,indices):
    model.eval();device=next(model.parameters()).device
    owners=[];starts=[]
    for i in indices:
        ss=window_starts(int(series.lengths[i]))
        owners.extend([int(i)]*len(ss));starts.extend(ss.tolist())
    p=[]
    for first in range(0,len(owners),32):
        xb=series.batch(owners[first:first+32],starts[first:first+32]).to(device)
        p.extend(torch.sigmoid(model(xb)).cpu().numpy().tolist())
    result=[];centre=[];rows=[]
    owners=np.asarray(owners);starts=np.asarray(starts);p=np.asarray(p)
    for i in indices:
        selected=owners==i;ss=starts[selected];pp=p[selected]
        result.append(pp.mean())
        center_start=(series.lengths[i]-WINDOW)//2
        center_index=np.where(ss==center_start)[0]
        assert len(center_index)==1
        centre.append(pp[center_index[0]])
        rows.extend({"index":int(i),"start":int(s),"probability":float(q),"is_center":bool(s==center_start)}
                    for s,q in zip(ss,pp))
    return np.asarray(result),np.asarray(centre),rows

