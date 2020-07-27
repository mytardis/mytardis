import React from 'react'
import TabSticker, { ExperimentTabSticker, ProjectTabSticker, DatafileTabSticker, DatasetTabSticker } from './TabSticker';

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