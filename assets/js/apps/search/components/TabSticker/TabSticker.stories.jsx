import React from 'react'
import TabSticker from './TabSticker';
import { action } from '@storybook/addon-actions';

export default {
  component: TabSticker,
  title: 'Tab Sticker',
};

export const Default = () => (
  <TabSticker initials="E" />
)