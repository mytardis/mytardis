import React from 'react'
import { PureQuickSearchBox } from './QuickSearchBox';
import { action } from '@storybook/addon-actions';

export default {
  component: PureQuickSearchBox,
  title: 'Quick search box',
  decorators: [story => <div style={{ padding: '3rem' }}>{story()}</div>],
  excludeStories: /.*Data$/,
};

export const Default = () => (
  <PureQuickSearchBox
      searchTerm=""
      onSubmit={action("submit")}
      onChange={action("change")} 
  />
);

export const Filled = () => (
  <PureQuickSearchBox
      searchTerm="A search term!"
      onSubmit={action("submit")}
      onChange={action("change")} 
  />
);
