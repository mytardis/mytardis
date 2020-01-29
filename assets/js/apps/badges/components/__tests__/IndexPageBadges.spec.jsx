import React from 'react';
import ReactDOM from 'react-dom';
import { act } from '@testing-library/react';
import renderer from 'react-test-renderer';
import IndexPageBadges from '../IndexPageBadges';

global.fetch = require('jest-fetch-mock');

let fakeExperimentData = {
  update_time: '2020-01-13T14:00:08.908600',
  dataset_count: 1,
  datafile_count: 100,
  public_access: 1,
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
describe('renders badges on index page', () => {
  it('should render correctly', async () => {
    await act(async () => {
      ReactDOM.render(<IndexPageBadges experimentID="123" />, container);
    });
    expect(container).toMatchSnapshot();
  });
  it('should render last updated badge', async () => {
    await act(async () => {
      ReactDOM.render(<IndexPageBadges experimentID="123" />, container);
    });
    expect(container.textContent).toContain('13th January 2020');
    expect(container.querySelector('span').attributes.getNamedItem('title').value)
      .toEqual('Last updated: Mon, Jan 13, 2020 2:00 PM');
  });
  it('should render dataset count badge', async () => {
    await act(async () => {
      ReactDOM.render(<IndexPageBadges experimentID="123" />, container);
    });
    expect(container.querySelector('ul').childNodes[1].firstChild.textContent.trim())
      .toEqual('1');
    expect(container.querySelector('ul').childNodes[1].firstChild.title).toEqual('1 dataset');
  });
  it('should render datafile count badge', async () => {
    await act(async () => {
      ReactDOM.render(<IndexPageBadges experimentID="123" />, container);
    });
    expect(container.querySelector('ul').childNodes[2].firstChild.textContent.trim())
      .toEqual('100');
    expect(container.querySelector('ul').childNodes[2].firstChild.title).toEqual('100 files');
  });
  it('should render Public access badge', async () => {
    await act(async () => {
      ReactDOM.render(<IndexPageBadges experimentID="123" />, container);
    });
    expect(container.querySelector('ul').childNodes[3].firstChild.textContent.trim())
      .toEqual('Private');
    expect(container.querySelector('ul').childNodes[3].firstChild.title.trim())
      .toEqual('No public access');
  });
  // remove the mock to ensure tests are completely isolated
  global.fetch.mockRestore();
});

describe('renders public access badge', () => {
  it('should render badge as private', async () => {
    await act(async () => {
      ReactDOM.render(<IndexPageBadges experimentID="123" />, container);
    });
    expect(container.querySelector('ul').childNodes[3].firstChild.title.trim())
      .toEqual('No public access');
  });
  it('should render badge as public', async () => {
    fakeExperimentData = {
      update_time: '2020-01-13T14:00:08.908600',
      dataset_count: 1,
      datafile_count: 100,
      public_access: 100,
    };
    await act(async () => {
      ReactDOM.render(<IndexPageBadges experimentID="123" />, container);
    });
    expect(container.querySelector('ul').childNodes[3].firstChild.title.trim())
      .toEqual('All data is public');
  });
  it('should render badge as Metadata', async () => {
    fakeExperimentData = {
      update_time: '2020-01-13T14:00:08.908600',
      dataset_count: 1,
      datafile_count: 100,
      public_access: 50,
    };
    await act(async () => {
      ReactDOM.render(<IndexPageBadges experimentID="123" />, container);
    });
    expect(container.querySelector('ul').childNodes[3].firstChild.title.trim())
      .toEqual('Only descriptions are public, not data');
  });
  it('should render badge as [PUBLICATION] Awaiting release', async () => {
    fakeExperimentData = {
      update_time: '2020-01-13T14:00:08.908600',
      dataset_count: 1,
      datafile_count: 100,
      public_access: 25,
    };
    await act(async () => {
      ReactDOM.render(<IndexPageBadges experimentID="123" />, container);
    });
    expect(container.querySelector('ul').childNodes[3].firstChild.title.trim())
      .toEqual('Under embargo and awaiting release');
  });
  global.fetch.mockRestore();
});
