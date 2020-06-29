import React from 'react'
import TabSticker from './TabSticker';
import { action } from '@storybook/addon-actions';

export default {
  component: TabSticker,
  title: 'Tab Sticker',
};

export const Project = () => (
  <TabSticker initials="P" />
)
export const Experiment = () => (
  <TabSticker initials="E" />
)
export const DataSet = () => (
  <TabSticker initials="DS" />
)
export const Datafile = () => (
  <TabSticker initials="DF" />
)