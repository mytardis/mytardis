import React from 'react'
import makeMockStore from "../../../util/makeMockStore";
import { PureFiltersSection } from './FiltersSection';
import { schemaData } from '../type-schema-list/TypeSchemaList.stories';
import { Provider } from "react-redux";

export default {
  component: PureFiltersSection,
  title: 'Filters/Filters section',
  decorators: [story => <Provider store={store}><div style={{ padding: '3rem', width: "400px" }}>{story()}</div>  </Provider>],
  excludeStories: /.*Data$/,
};

const store = makeMockStore({});

export const filtersData = {
  typeAttributes:{
    projects: {
      schema: {op:"is",content:["1"]}
    },
    experiments: {
      schema: {op:"is",content:["2"]}
    },
    datasets: {
      schema: {op:"is",content:["1"]}
    },
    datafiles: {
      schema: {op:"is",content:["1","2"]}
    }
  },
  schemaParameters:{
    projects: schemaData,
    experiments: schemaData,
    datasets: schemaData,
    datafiles: schemaData
  }
}

export const noFiltersData = null;

export const Default = () => (
    <PureFiltersSection filtersByKind={filtersData} isLoading={false} error={null} />
);

export const NoFilters = () => (
  <PureFiltersSection filtersByKind={noFiltersData} isLoading={false} error={null} />
);

export const Loading = () => (
  <PureFiltersSection filtersByKind={noFiltersData} isLoading={true} error={null} />
);

const error = {message:"Error loading filter data"};

export const Error = () => (
  <PureFiltersSection filtersByKind={noFiltersData} isLoading={false} error={error} />
);