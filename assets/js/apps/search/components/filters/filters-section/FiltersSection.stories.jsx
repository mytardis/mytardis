import React from 'react'
import makeMockStore from "../../../util/makeMockStore";
import { PureFiltersSection } from './FiltersSection';
import { schemaData,allSchemaIdsData } from '../type-schema-list/TypeSchemaList.stories';
import { Provider } from "react-redux";
import { error } from 'jquery';

export default {
  component: PureFiltersSection,
  title: 'Filters/Filters section',
  decorators: [story => <Provider store={store}><div style={{ padding: '3rem', width: "400px" }}>{story()}</div>  </Provider>],
  excludeStories: /.*Data$/,
};

const store = makeMockStore({});

export const filtersData = {
  types: {
    byId: {
        projects: {
          attributes: {
          schema: {op:"is",content:["1"]}
        }
      },
      experiments: {
        attributes: {
          schema: {op:"is",content:["2"]}
        }
      },
      datasets: {
        attributes: {
          schema: {op:"is",content:["1"]}
        }
      },
      datafiles: {
        attributes: {
          schema: {op:"is",content:["1","2"]}
        }
      }
    },
    allIds: ["projects","experiments","datasets","datafiles"]
  },
  schemas: {
    byId: schemaData,
    allIds: allSchemaIdsData
  },
  typeSchemas: {
      projects: allSchemaIdsData,
      experiments: allSchemaIdsData,
      datasets: allSchemaIdsData,
      datafiles: allSchemaIdsData
  },
  isLoading: false,
  error: null
};

export const noFiltersData = Object.assign({},filtersData, {
  typeSchemas: null
})

export const loadingData = Object.assign({},filtersData, {
  isLoading: true
})

export const errorData = Object.assign({},filtersData, {
  error: "Error loading filter data"
})

export const Default = () => (
    <PureFiltersSection {...filtersData} />
);

export const NoFilters = () => (
  <PureFiltersSection {...noFiltersData} />
);

export const Loading = () => (
  <PureFiltersSection {...loadingData} />
);

export const Error = () => (
  <PureFiltersSection {...errorData} />
);