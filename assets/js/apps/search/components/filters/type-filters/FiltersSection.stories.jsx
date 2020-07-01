import React from 'react'
import { action } from '@storybook/addon-actions';
import makeMockStore from "../../../util/makeMockStore";
import FiltersSection from './FiltersSection'

export default {
  component: FiltersSection,
  title: 'Filters/Filters section',
  decorators: [story => <div style={{ padding: '3rem' }}>{story()}</div>],
  excludeStories: /.*Data$/,
};

export const Default = () => (<FiltersSection />);