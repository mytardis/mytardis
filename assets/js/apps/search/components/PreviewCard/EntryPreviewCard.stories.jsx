import React from 'react'
import { action } from '@storybook/addon-actions';
import EntryPreviewCard from './EntryPreviewCard';

export default {
  component: EntryPreviewCard,
  title: 'EntryPreviewCard',
  // decorators: [story => <div style={{ padding: '3rem' }}>{story()}</div>],
  // excludeStories: /.*Data$/,
};

export const Default = () => (
  <EntryPreviewCard />
);