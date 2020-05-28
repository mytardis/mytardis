import React from 'react'
import FilterSidebar from './FilterSidebar';
import { action } from '@storybook/addon-actions';

export default {
  component: FilterSidebar,
  title: 'Filter sidebar',
  decorators: [story => <div style={{ padding: '3rem' }}>{story()}</div>],
  excludeStories: /.*Data$/,
};

export const Default = () => (
  <FilterSidebar />
)