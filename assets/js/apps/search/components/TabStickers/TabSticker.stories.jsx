import React from 'react'
import TabSticker from './TabSticker';
import ExperimentTabSticker from './ExperimentTabSticker';
import ProjectTabSticker from './ProjectTabSticker';
import DatafileTabSticker from './DatafileTabSticker';
import DatasetTabSticker from './DatasetTabSticker';
import { action } from '@storybook/addon-actions';

export default {
  component: TabSticker,
  title: 'Tab Stickers',
};

export const Project = () => (
  <ProjectTabSticker />
)
export const Experiment = () => (
  <ExperimentTabSticker />
)
export const DataSet = () => (
  <DatasetTabSticker />
)
export const Datafile = () => (
  <DatafileTabSticker />
)