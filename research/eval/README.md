# Evaluation set

A hand-labelled set of ~500 photos used to compare models and clustering settings.

## Manifest format

`labels.csv` (not committed if it contains private paths; commit `labels.example.csv` instead):

```csv
path,theme
/Users/me/Photos/2023/IMG_0412.jpg,blue-hour city
/Users/me/Photos/2021/DSC_1180.NEF,summer nature
```

## Metrics

- Cluster purity and NMI against the labelled themes
- Search precision@10 for a fixed list of text queries
- Naming acceptance: share of auto-titles you would keep
- Speed (images/second) and peak memory per model
