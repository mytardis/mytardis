import React from 'react';
import ReactDOM from 'react-dom';
import { act } from '@testing-library/react';
import ExperimentViewPageBadges from '../ExperimentViewPageBadges';

global.fetch = require('jest-fetch-mock');

const fakeExperimentData = {
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
      ReactDOM.render(<ExperimentViewPageBadges
        experimentID="123"
        container={container}
        licenseUpdatedCount={0}
      />, container);
    });
    expect(container).toMatchSnapshot();
    expect(container.querySelectorAll('span').length)
      .toEqual(10);
  });
  it('should render dataset count badge', async () => {
    await act(async () => {
      ReactDOM.render(<ExperimentViewPageBadges
        experimentID="123"
        container={container}
        licenseUpdatedCount={0}
      />, container);
    });
    expect(container.querySelectorAll('span')[0].textContent.trim())
      .toEqual('1');
  });
  it('should render datafile count badge', async () => {
    await act(async () => {
      ReactDOM.render(<ExperimentViewPageBadges
        experimentID="123"
        container={container}
        licenseUpdatedCount={0}
      />, container);
    });
    expect(container.querySelectorAll('span')[2].textContent.trim())
      .toEqual('100');
  });
  it('should render last updated badge', async () => {
    await act(async () => {
      ReactDOM.render(<ExperimentViewPageBadges
        experimentID="123"
        container={container}
        licenseUpdatedCount={0}
      />, container);
    });
    expect(container.querySelectorAll('span')[6].textContent.trim())
      .toEqual('13th January 2020');
  });
  it('should render public access badge', async () => {
    await act(async () => {
      ReactDOM.render(<ExperimentViewPageBadges
        experimentID="123"
        container={container}
        licenseUpdatedCount={0}
      />, container);
    });
    expect(container.querySelectorAll('span')[8].textContent.trim())
      .toEqual('Private');
  });
});
