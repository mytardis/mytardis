import React from 'react';
import ReactDOM from 'react-dom';
import { act } from '@testing-library/react';
import IndexPageBadges from "../IndexPageBadges";
import ExperimentViewPageBadges from "../ExperimentViewPageBadges";

global.fetch = require('jest-fetch-mock');

let fakeExperimentData = {
  update_time: '2020-01-13T14:00:08.908600',
  dataset_count: 1,
  datafile_count: 100,
  public_access: 1,
  experiment_size: 1024,
};
let container = null;
beforeEach(() => {
  jest.spyOn(global, 'fetch').mockImplementation(() => Promise.resolve({
    json: () => Promise.resolve(fakeExperimentData),
  }));
  container = document.createElement('div');
  document.body.appendChild(container);
});
afterEach(() => {
  // cleanup on exiting
  container.remove();
  container = null;
});

describe('renders badges on experiment view page', () => {
  it('should render experiment size badge', async () => {
    await act(async () => {
      ReactDOM.render(<ExperimentViewPageBadges experimentID={"123"} />, container);
    });
    expect(container.querySelector('span').textContent)
      .toEqual('Private');
  });
});