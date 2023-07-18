import React from 'react'
import FilterSidebar from './FilterSidebar';
import { Provider } from 'react-redux';
import {action} from '@storybook/addon-actions';
import { filtersData } from "./filters/filters-section/FiltersSection.stories";
import makeMockStore from "../util/makeMockStore";

export default {
  component: FilterSidebar,
  title: 'Filter sidebar',
  decorators: [story => <Provider store={store}><div style={{ padding: '3rem' }}>{story()}</div></Provider>],
  excludeStories: /.*Data$/,
};

// Mock redux store for this story.
const store = makeMockStore(
  {
    search: {
    },
    filters: filtersData
  }
)

export const Default = () => (
  <FilterSidebar />
)