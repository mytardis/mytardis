import React from 'react';
import ReactDOM from 'react-dom';
import { act } from '@testing-library/react';
import { configure, mount } from 'enzyme';
import Adapter from 'enzyme-adapter-react-16';

import DatasetTilesLists from '../DatasetTilesLists';

const fakeData = [
  {
    id: 26,
    description: 'My demo dataset 25062019',
    directory: null,
    created_time: '2019-06-25 01:54:04.864000+00:00',
    modified_time: '2020-04-22 02:03:17.802951+00:00',
    immutable: false,
    instrument: null,
    experiments: [
      34,
    ],
    file_count: 1,
    url: '/dataset/26',
    size: 164495,
    size_human_readable: '160.6 KB',
    show_dataset_thumbnails: true,
  },
  {
    id: 30,
    description: 'New Dataset',
    directory: null,
    created_time: '2020-01-13 01:36:34.761466+00:00',
    modified_time: '2020-04-22 02:47:58.368048+00:00',
    immutable: false,
    instrument: null,
    experiments: [
      34,
    ],
    file_count: 1,
    url: '/dataset/30',
    size: 350565,
    size_human_readable: '342.3 KB',
    show_dataset_thumbnails: true,
  }];

global.fetch = require('jest-fetch-mock');

configure({ adapter: new Adapter() });


let container = null;
let shareContainer = null
let component = null;
beforeEach(async () => {
  jest.spyOn(global, 'fetch').mockImplementation(() => Promise.resolve({
    json: () => Promise.resolve(fakeData),
  }));
  container = document.createElement('div');
  document.body.appendChild(container);
  shareContainer = document.createElement('div');
  document.body.appendChild(shareContainer);
  await act(async () => {
    component = mount(<DatasetTilesLists experimentId="1234" shareContainer={shareContainer} />, { attachTo: container });
  });
  component.update();
});
afterEach(() => {
  // cleanup on exiting
  container.remove();
  container = null;
  component.unmount();
  component.detach();
});
describe('render dataset tiles on page load', () => {
  it('should match snapshot', async () => {
    await act(async () => {
      ReactDOM.render(<DatasetTilesLists experimentId={'1234'} shareContainer={shareContainer} />, container);
    });
    expect(container).toMatchSnapshot();
  });
});
