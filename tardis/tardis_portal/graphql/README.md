## Get experiments with metadata

```
{
  experiments {
    edges {
      node {
        pk
        title
        experimentparametersetSet {
          edges {
            node {
              experimentparameterSet {
                edges {
                  node {
                    name {
                      name
                      order
                    }
                    stringValue
                    numericalValue
                    datetimeValue
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

## Get datasets with metadata and experiments

```
{
  datasets {
    edges {
      node {
        pk
        description
        datasetparametersetSet {
          edges {
            node {
              datasetparameterSet {
                edges {
                  node {
                    name {
                      name
                    }
                    stringValue
                    numericalValue
                    datetimeValue
                  }
                }
              }
            }
          }
        }
        experiments {
          edges {
            node {
              pk
              title
            }
          }
        }
      }
    }
  }
}
```

