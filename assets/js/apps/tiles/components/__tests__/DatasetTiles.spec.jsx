import React from 'react';
import { act } from '@testing-library/react';
import { configure, mount } from 'enzyme';
import Adapter from 'enzyme-adapter-react-16';
import fetchMock from 'jest-fetch-mock';
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
const fakeExpList = [
  {
    id: 34,
    title: 'My Test Exp',
  },
  {
    id: 38,
    title: 'My Test Exp 2',
  }];

const fakeExpPermissions = {
  download_permissions: true,
  write_permissions: true,
  is_publication: false,
};
const fakeHSMData = {
  online_files: 4,
  total_files: 4,
};

global.fetch = require('jest-fetch-mock');

configure({ adapter: new Adapter() });


let rootContainer = null;
let shareContainer = null;
let component = null;
let mainContainer = null;
beforeEach(async () => {
  fetchMock.mockResponse((request) => {
    if (request.url.endsWith('/dataset/')) {
      return Promise.resolve(JSON.stringify(fakeData));
    }
    if (request.url.endsWith('/experiment_list/')) {
      return Promise.resolve(JSON.stringify(fakeExpList));
    }
    if (request.url.endsWith('/get_experiment_permissions')) {
      return Promise.resolve(JSON.stringify(fakeExpPermissions));
    }
    if (request.url.includes('hsm_dataset')) {
      return Promise.resolve(JSON.stringify(fakeHSMData));
    }
    return {
      status: 404,
      body: 'Not Found',
    };
  });

  rootContainer = global.document.createElement('div');
  rootContainer.setAttribute('id', 'root');
  mainContainer = global.document.createElement('div');
  mainContainer.setAttribute('id', 'datasets-pane');
  rootContainer.appendChild(mainContainer);

  shareContainer = global.document.createElement('div');
  shareContainer.setAttribute('id', 'experiment-tab-transfer-datasets');
  rootContainer.appendChild(shareContainer);
});
afterEach(() => {
  // cleanup on exiting

});
describe('render dataset tiles on page load', () => {
  it('should match snapshot', async () => {
    await act(async () => {
      component = mount(<DatasetTilesLists experimentId="1234" shareContainer={shareContainer} hsmEnabled />, { attachTo: mainContainer });
    });
    component.update();
    expect(rootContainer).toMatchSnapshot();
  });
});
