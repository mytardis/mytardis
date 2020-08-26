import React from 'react';
import ReactDOM from 'react-dom';
import { act } from '@testing-library/react';
import DatasetViewPageBadges from '../DatasetViewPageBadges';

global.fetch = require('jest-fetch-mock');

const fakeDatasetData = {
  dataset_datafile_count: 5,
  dataset_experiment_count: 3,
  dataset_size: 14216734,
};
let container = null;
beforeEach(() => {
  jest.spyOn(global, 'fetch').mockImplementation(() => Promise.resolve({
    json: () => Promise.resolve(fakeDatasetData),
  }));
  container = document.createElement('div');
  container.setAttribute('id', 'experiment-1234');
  container.setAttribute('class', 'badges');
  document.body.appendChild(container);
});
afterEach(() => {
  // cleanup on exiting
  container.remove();
  container = null;
});

describe('renders badges on experiment view page', () => {
  it('should render all badges', async () => {
    await act(async () => {
      ReactDOM.render(<DatasetViewPageBadges datasetID="123" />, container);
    });
    expect(container).toMatchSnapshot();
    expect(container.querySelectorAll('span').length)
      .toEqual(6);
  });
  it('should render experiment count badge', async () => {
    await act(async () => {
      ReactDOM.render(<DatasetViewPageBadges datasetID="123" />, container);
    });
    expect(container.querySelectorAll('span')[0].textContent.trim())
      .toEqual('3');
  });
  it('should render datafile count badge', async () => {
    await act(async () => {
      ReactDOM.render(<DatasetViewPageBadges datasetID="123" />, container);
    });
    expect(container.querySelectorAll('span')[2].textContent.trim())
      .toEqual('5');
  });
  it('should render last updated badge', async () => {
    await act(async () => {
      ReactDOM.render(<DatasetViewPageBadges datasetID="123" />, container);
    });
    expect(container.querySelectorAll('span')[4].textContent.trim())
      .toEqual('13.56 MB');
  });
});
