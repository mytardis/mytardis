import React from 'react'
import FilterSidebar from './FilterSidebar';
import { Provider } from 'react-redux'
import {action} from '@storybook/addon-actions'
export default {
  component: FilterSidebar,
  title: 'Filter sidebar',
  decorators: [story => <Provider store={store}><div style={{ padding: '3rem' }}>{story()}</div></Provider>],
  excludeStories: /.*Data$/,
};

// Mock redux store for this story.
const store = {
  getState: () => {
    return {};
  },
  subscribe: () => 0,
  dispatch: action('dispatch'),
};

export const Default = () => (
  <FilterSidebar />
)