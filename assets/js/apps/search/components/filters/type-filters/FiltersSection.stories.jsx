import React from 'react'
import { action } from '@storybook/addon-actions';
import makeMockStore from "../../../util/makeMockStore";
import FiltersSection from './FiltersSection';
import { schemaData } from '../type-schema-list/TypeSchemaList.stories';
import { Provider } from "react-redux";

export default {
  component: FiltersSection,
  title: 'Filters/Filters section',
  decorators: [story => <div style={{ padding: '3rem', width: "400px" }}>{story()}</div>],
  excludeStories: /.*Data$/,
};

const store = makeMockStore({});

const filtersData = {
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
    <FiltersSection filters={filtersData} />
  </Provider>
);