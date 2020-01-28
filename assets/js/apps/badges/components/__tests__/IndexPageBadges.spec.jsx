import React from 'react';
import ReactDOM from 'react-dom';
import { act } from '@testing-library/react';
import IndexPageBadges from '../IndexPageBadges';

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
it('can render badges on index page', async () => {
  const fakeExperimentData = {
    update_time: '2020-01-13T14:00:08.908600',
    dataset_count: 1,
    datafile_count: 100,
    public_access: 1,
  };
  jest.spyOn(global, 'fetch').mockImplementation(() => Promise.resolve({
    json: () => Promise.resolve(fakeExperimentData),
  }));

  await act(async () => {
    ReactDOM.render(<IndexPageBadges experimentID="123" />, container);
  });
  expect(container.textContent).toContain('13th January 2020');
  expect(container.querySelector('span').attributes.getNamedItem('title').value)
    .toEqual('Last updated: Mon, Jan 13, 2020 2:00 PM');
  expect(container.querySelector('span').attributes.getNamedItem('content').value)
    .toEqual('2020-01-13T03:00:08.908Z');
  expect(container.querySelector('ul').childNodes[1].firstChild.textContent.trim()).toEqual('1');
  expect(container.querySelector('ul').childNodes[1].firstChild.title).toEqual('1 dataset');
  expect(container.querySelector('ul').childNodes[2].firstChild.textContent.trim()).toEqual('100');
  expect(container.querySelector('ul').childNodes[2].firstChild.title).toEqual('100 files');
  // remove the mock to ensure tests are completely isolated
  global.fetch.mockRestore();
});
