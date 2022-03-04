import React from 'react'
import makeMockStore from "../../../util/makeMockStore";
import { PureFiltersSection } from './FiltersSection';
import { schemaData,allSchemaIdsData } from '../type-schema-list/TypeSchemaList.stories';
import { Provider } from "react-redux";

export default {
  component: PureFiltersSection,
  title: 'Filters/Filters section',
  decorators: [story => <div style={{ padding: '3rem', width: "400px" }}>{story()}</div>],
  excludeStories: /.*Data$/,
};


export const filtersData = {
  types: {
    byId: {
      project: {
        full_name: "Project",
        collection_name: "projects",
        attributes: {
          byId: {
            name: {
              full_name: "Name",
              id: "name",
              data_type:"STRING",
              filterable: true,
              sortable: true
            },
            createdDate: {
              full_name: "Created date",
              id: "createdDate",
              data_type: "DATETIME",
              filterable: true,
              sortable: true
            },
            institution: {
              full_name: "Institution",
              id: "institution",
              data_type: "STRING",
              filterable: true,
              sortable: true
            },
            schema: {
              full_name: "Schema",
              value: { op: "is", content: ["1"] },
            }
          }, allIds: ["name", "createdDate", "institution", "schema"]
        }
      },
      experiment: {
        full_name: "Experiment",
        collection_name: "experiments",
        attributes: {
          byId: {
            name: {
              full_name: "Name",
              id: "name",
              
              data_type:"STRING",
              filterable: true,
              sortable: true
            },
            createdDate: {
              full_name: "Created date",
              id: "createdDate",
              data_type: "DATETIME",
              filterable: true,
              sortable: true
            },
            institution: {
              full_name: "Institution",
              id: "institution",
              data_type: "STRING",
              filterable: true,
              sortable: true
            },
            schema: {
              full_name: "Schema",
              value: { op: "is", content: ["2"] }
            }
          }, allIds: ["name", "createdDate", "institution", "schema"]
        }
      },
      dataset: {
        full_name: "Dataset",
        collection_name: "datasets",
        attributes: {
          byId: {
            name: {
              full_name: "Name",
              id: "name",
              data_type:"STRING",
              filterable: true,
              sortable: true
            },
            createdDate: {
              full_name: "Created date",
              id: "createdDate",
              data_type: "DATETIME",
              filterable: true,
              sortable: true
            },
            institution: {
              full_name: "Institution",
              id: "institution",
              data_type: "STRING",
              filterable: true,
              sortable: true
            },
            schema: {
              full_name: "Schema",
              value: { op: "is", content: ["1"] },
              filterable: true
            }
          }, allIds: ["name", "createdDate", "institution", "schema"]
        }
      },
      datafile: {
        full_name: "Datafile",
        collection_name: "datafiles",
        attributes: {
          byId: {
            name: {
              full_name: "Name",
              id: "name",
              data_type:"STRING",
              filterable: true,
              sortable: true
            },
            createdDate: {
              full_name: "Created date",
              id: "createdDate",
              data_type: "DATETIME",
              filterable: true,
              sortable: true
            },
            institution: {
              full_name: "Institution",
              id: "institution",
              data_type: "STRING",
              filterable: true,
              sortable: true
            },
            schema: {
              value: { op: "is", content: ["1", "2"] },
              full_name: "Schema"
            }
          }, allIds: ["name", "createdDate", "institution", "schema"]
        }
      }
    },
    allIds: ["project", "experiment", "dataset", "datafile"]
  },
  schemas: {
    byId: schemaData,
    allIds: allSchemaIdsData
  },
  typeSchemas: {
    project: allSchemaIdsData,
    experiment: allSchemaIdsData,
    dataset: allSchemaIdsData,
    datafile: allSchemaIdsData
  },
  activeFilters: {
    project: [{
      kind: "typeAttribute",
      target: ["project", "schema"]
    }],
    experiment: [{
      kind: "typeAttribute",
      target: ["experiment", "schema"]
    }],
    dataset: [{
      kind: "typeAttribute",
      target: ["dataset", "schema"]
    }],
    datafile: [{
      kind: "typeAttribute",
      target: ["datafile", "schema"]
    }]
  },
  isLoading: false,
  error: null
};

const makeMockStoreWithFilterSlice = (filterSlice) => (makeMockStore({filters: filterSlice}));


export const noFiltersData = Object.assign({},filtersData, {
  typeSchemas: null
})

export const loadingData = Object.assign({},filtersData, {
  isLoading: true
})

export const errorData = Object.assign({},filtersData, {
  error: "Error loading filter data"
})

export const Default = () => {
    const store = makeMockStoreWithFilterSlice(filtersData);
    return <Provider store={store}><PureFiltersSection {...filtersData} /></Provider>
};

export const NoFilters = () => {
  const store = makeMockStoreWithFilterSlice(noFiltersData);
  return <Provider store={store}><PureFiltersSection {...noFiltersData} /></Provider>
};

export const Loading = () => {
  const store = makeMockStoreWithFilterSlice(loadingData);
  return <Provider store={store}><PureFiltersSection {...loadingData} /></Provider>
};

export const Error = () => {
  const store = makeMockStoreWithFilterSlice(errorData);
  return <Provider store={store}><PureFiltersSection {...errorData} /></Provider>
};
