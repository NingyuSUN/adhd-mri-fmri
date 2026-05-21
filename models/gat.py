"""
models/gat.py
Graph Attention Network models for fMRI functional connectivity classification.
"""

import torch
import torch.nn.functional as F
from torch.nn import Linear, Dropout
from torch_geometric.nn import GATConv, GCNConv, global_mean_pool


class GAT_v1(torch.nn.Module):
    """
    2-layer GAT with multi-head attention.
    Best overall generalization on multi-site data.

    Node features: each node = one ROI; feature vector = its row of the FC matrix (dim=48).
    """

    def __init__(self, in_channels: int = 48, hidden_channels: int = 64, heads: int = 4):
        super().__init__()
        self.conv1 = GATConv(in_channels, hidden_channels, heads=heads)
        self.conv2 = GATConv(hidden_channels * heads, hidden_channels, heads=1)
        self.fc = Linear(hidden_channels, 2)
        self.dropout = Dropout(0.5)

    def forward(self, x, edge_index, batch):
        x = self.conv1(x, edge_index).relu()
        x = self.dropout(x)
        x = self.conv2(x, edge_index).relu()
        x = global_mean_pool(x, batch)
        return self.fc(x)


class GAT_v2(torch.nn.Module):
    """
    GAT with larger hidden dimension (128).
    Tends to overfit on single-site data (~200 subjects).
    Pair with strong Dropout (0.6) and weight decay.
    """

    def __init__(self, in_channels: int = 48, hidden_channels: int = 128, heads: int = 4):
        super().__init__()
        self.conv1 = GATConv(in_channels, hidden_channels, heads=heads)
        self.conv2 = GATConv(hidden_channels * heads, hidden_channels, heads=1)
        self.fc = Linear(hidden_channels, 2)
        self.dropout = Dropout(0.6)

    def forward(self, x, edge_index, batch):
        x = self.conv1(x, edge_index).relu()
        x = self.dropout(x)
        x = self.conv2(x, edge_index).relu()
        x = global_mean_pool(x, batch)
        x = self.dropout(x)
        return self.fc(x)


class SiteGAT(torch.nn.Module):
    """
    GAT for site prediction (domain-effect baseline).
    Same architecture as GAT_v1 but multi-class output.
    If this achieves high accuracy, the data contains strong site-specific signals.
    """

    def __init__(self, in_channels: int = 48, hidden_channels: int = 64,
                 heads: int = 4, num_classes: int = 8):
        super().__init__()
        self.conv1 = GATConv(in_channels, hidden_channels, heads=heads)
        self.conv2 = GATConv(hidden_channels * heads, hidden_channels, heads=1)
        self.fc = Linear(hidden_channels, num_classes)
        self.dropout = Dropout(0.5)

    def forward(self, x, edge_index, batch):
        x = self.conv1(x, edge_index).relu()
        x = self.dropout(x)
        x = self.conv2(x, edge_index).relu()
        x = global_mean_pool(x, batch)
        return self.fc(x)


class GCN_v2(torch.nn.Module):
    """
    2-layer GCN with FC-row node features.
    Baseline before introducing attention.
    Single-site NYU: AUC ~0.58-0.63.
    """

    def __init__(self, in_channels: int = 48, hidden_channels: int = 64):
        super().__init__()
        self.conv1 = GCNConv(in_channels, hidden_channels)
        self.conv2 = GCNConv(hidden_channels, hidden_channels)
        self.fc = Linear(hidden_channels, 2)
        self.dropout = Dropout(0.3)

    def forward(self, x, edge_index, batch):
        x = self.conv1(x, edge_index).relu()
        x = self.dropout(x)
        x = self.conv2(x, edge_index).relu()
        x = global_mean_pool(x, batch)
        return self.fc(x)


def evaluate(model, loader, device):
    """
    Evaluate a GNN model. Returns (AUC, accuracy, y_true, y_prob, y_pred).
    AUC requires at least two classes in the loader; returns NaN otherwise.
    """
    import numpy as np
    from sklearn.metrics import roc_auc_score, accuracy_score

    model.eval()
    all_probs, all_preds, all_true = [], [], []

    with torch.no_grad():
        for batch in loader:
            batch = batch.to(device)
            out = model(batch.x, batch.edge_index, batch.batch)
            probs = torch.softmax(out, dim=1)[:, 1]
            preds = torch.argmax(out, dim=1)
            all_probs.extend(probs.cpu().numpy())
            all_preds.extend(preds.cpu().numpy())
            all_true.extend(batch.y.view(-1).cpu().numpy())

    all_probs = np.array(all_probs)
    all_preds = np.array(all_preds)
    all_true = np.array(all_true)

    auc = roc_auc_score(all_true, all_probs) if len(np.unique(all_true)) >= 2 else float("nan")
    acc = accuracy_score(all_true, all_preds)
    return auc, acc, all_true, all_probs, all_preds
