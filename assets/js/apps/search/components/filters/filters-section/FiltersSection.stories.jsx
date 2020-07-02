import React from 'react'
import makeMockStore from "../../../util/makeMockStore";
import { PureFiltersSection } from './FiltersSection';
import { schemaData } from '../type-schema-list/TypeSchemaList.stories';
import { Provider } from "react-redux";

export default {
  component: PureFiltersSection,
  title: 'Filters/Filters section',
  decorators: [story => <div style={{ padding: '3rem', width: "400px" }}>{story()}</div>],
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

export const Default = () => (
  <Provider store={store}>
    <PureFiltersSection filters={filtersData} />
  </Provider>
);