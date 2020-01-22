import React from 'react';
import ReactDOM from 'react-dom';
import { act } from '@testing-library/react';
import ExperimentLastUpdatedBadge from '../ExperimentLastUpdateBadge';

global.fetch = require('jest-fetch-mock');


let container = null;
beforeEach(() => {
  container = document.createElement('div');
  document.body.appendChild(container);
});
afterEach(() => {
  // cleanup on exiting
  container.remove();
  container = null;
});
it('can render last updated badge', async () => {
  const fakeExperimentData = {
    update_time: '2020-01-13T14:00:08.908600',
  };
  jest.spyOn(global, 'fetch').mockImplementation(() => Promise.resolve({
    json: () => Promise.resolve(fakeExperimentData),
  }));

  await act(async () => {
    ReactDOM.render(<ExperimentLastUpdatedBadge experimentID="123" />, container);
  });
  expect(container.textContent).toContain('13th January 2020');
  expect(container.querySelector('span').attributes.getNamedItem('title').value)
    .toEqual('Last updated: Mon, Jan 13, 2020 2:00 PM');
  expect(container.querySelector('span').attributes.getNamedItem('content').value)
    .toEqual('2020-01-13T03:00:08.908Z');
  // remove the mock to ensure tests are completely isolated
  global.fetch.mockRestore();
});
