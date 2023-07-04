import React from 'react';
import ReactDOM from 'react-dom';
import { configure, shallow, mount } from 'enzyme';
import 'regenerator-runtime/runtime';
import Adapter from 'enzyme-adapter-react-16/build';
import { act } from '@testing-library/react';
import Search, {
  createDataFileResultData,
  createDatasetResultData,
  createExperimentResultData,
} from '../components/Search';
import Result from '../components/Result';
import Results from '../components/Results';
import SimpleSearchForm from '../components/SimpleSearchForm';
import AdvancedSearchForm from '../components/AdvancedSearchForm';


global.fetch = require('jest-fetch-mock');

configure({ adapter: new Adapter() });

const experimentData = {
  title: 'Test Group - Test Experiment 1',
  description: 'Uploader: Test Instrument',
  type: 'experiment',
  id: '8369',
  url: '/experiment/view/8369/',
};
const datasetData = {
  title: 'Test Dataset',
  type: 'dataset',
  id: 1234,
  url: '/dataset/1234',
  experiments: [
    {
      id: 78,
      acls: [
        {
          entityId: '73',
          pluginId: 'django_user',
        },
        {
          entityId: '2',
          pluginId: 'django_group',
        },
      ],
      public_access: 1,
      title: 'admin',
    },
  ],
  instrument: 'Test Instrument',
  created_time: '2017-02-02T00:20:35.882945+00:00',
  update_time: '2017-02-02T00:20:35.882945+00:00',
};
const datafileData = {
  title: 'Test_file.tiff',
  type: 'datafile',
  id: 1234,
  url: '/datafile/view/1234',
  created_time: '2017-02-02T00:20:35.882945+00:00',
  update_time: '2017-02-02T00:20:35.882945+00:00',
  dataset_description: 'Test Dataset',
  dataset_url: '/dataset/1234',
};

const apiResponse = {
  meta: {
    limit: 20,
    next: null,
    offset: 0,
    previous: null,
    total_count: 1,
  },
  objects: [
    {
      hits: {
        datafiles: [{
          _id: '525',
          _index: 'datafile',
          _score: 3.7592819,
          _source: {
            created_time: '2015-06-17T02:05:46+00:00',
            dataset: {
              experiments: [
                {
                  id: 7,
                  acls: [
                    {
                      entityId: '13',
                      pluginId: 'django_user',
                    },
                  ],
                  public_access: 1,
                },
              ],
              id: 13,
            },
            filename: '02_MCB01.tif',
            modification_time: null,
          },
          _type: 'doc',
        }],
        datasets: [{
          _id: '41079',
          _index: 'dataset',
          _score: 4.3889866,
          _source: {
            created_time: '2017-02-02T00:20:35.882945+00:00',
            description: 'Experiment_notes',
            experiments: [
              {
                id: 6292,
                acls: [
                  {
                    entityId: '1033',
                    pluginId: 'django_user',
                  },
                ],
                public_access: 100,
                title: 'CT dose reduction ',
              },
            ],
            id: 41079,
            instrument: {
              id: 146,
              name: 'Genevieve_PC',
            },
            modified_time: '2019-04-30T23:21:04.112514+00:00',
          },
          _type: 'doc',
        }],
        experiments: [{
          _id: '3883',
          _index: 'experiments',
          _score: 2.622984,
          _source: {
            created_by: {
              username: 'testuser',
            },
            created_time: '2015-12-04T01:31:13.938888+00:00',
            description: '',
            end_time: null,
            id: 3883,
            institution_name: 'Monash University',
            acls: [
              {
                entityId: '13',
                pluginId: 'django_user',
              },
            ],
            public_access: 100,
            start_time: null,
            title: 'Electron micrographs of hPrx3.',
            update_time: '2015-12-04T05:29:16.000803+00:00',
          },
          _type: 'doc',
        }],
      },
      resource_uri: '/api/v1/search_simple-search/1/',
    },
  ],
};
const instrumentListResponse = {
  meta: {
    limit: 1,
    next: '/api/v1/instrument/?format=json&limit=1&offset=1',
    offset: 0,
    previous: null,
    total_count: 127,
  },
  objects: [
    {
      created_time: null,
      facility: {
        created_time: null,
        id: 118,
        manager_group: {
          id: 1116,
          name: 'ara-facility-managers',
          resource_uri: '/api/v1/group/1116/',
        },
        modified_time: null,
        name: 'ARA Preclinical Imaging',
        resource_uri: '/api/v1/facility/118/',
      },
      id: 316,
      modified_time: null,
      name: '9.4T MRI',
      resource_uri: '/api/v1/instrument/316/',
    },
  ],
};
let container = null;
beforeEach(async () => {
  container = document.createElement('div');
  document.body.appendChild(container);
});
afterEach(() => {
  // cleanup on exiting
  jest.resetAllMocks();
  jest.clearAllMocks().resetModules();
  container.remove();
  container = null;
});
describe('Search Component', () => {
  it('Render Search Component', async () => {
    jest.spyOn(global, 'fetch').mockImplementation(() => Promise.resolve({
      json: () => Promise.resolve(apiResponse),
    }));
    // making test more deterministic with mocking date.now
    jest.spyOn(Date, 'now').mockImplementation(() => 1487076708000);
    await act(async () => {
      ReactDOM.render(<Search />, container);
    });
    expect(container).toMatchSnapshot();
  });
  it('Render Search Component with results', async () => {
    jest.spyOn(global, 'fetch').mockImplementation(() => Promise.resolve({
      json: () => Promise.resolve(apiResponse),
    }));
    let component = null;
    await act(async () => {
      component = mount(<Search />, { attachTo: container });
    });
    await act(async () => {
      const searchInput = component.find('input').first();
      searchInput.simulate('change', { target: { value: 'test' } });
      component.find('button').at(0).simulate('click');
    });
    component.update();
  });
});
describe('Results Component', () => {
  it('Render Results Component', () => {
    let newResults = [];
    newResults = createExperimentResultData(apiResponse.objects[0].hits.experiments, newResults);
    expect(newResults).toBeTruthy();
    newResults = createDatasetResultData(apiResponse.objects[0].hits.datasets, newResults);
    expect(newResults).toBeTruthy();
    newResults = createDataFileResultData(apiResponse.objects[0].hits.datafiles, newResults);
    expect(newResults).toBeTruthy();
    const _counts = {
      experimentsCount: 0,
      datasetsCount: 0,
      datafilesCount: 0,
    };
    const results = shallow(<Results counts={_counts} results={newResults} />);
    expect(results).toBeTruthy();
  });
});

describe('Result Component', () => {
  let showResults;
  beforeEach(() => {
    showResults = (() => {
    });
    return showResults;
  });
  it('Test Render Result component', () => {
    const experimentResultComponent = mount(
      <Result key={experimentData.id} result={experimentData} />,
    );
    expect(experimentResultComponent.exists()).toBeTruthy();
    const datasetResultComponent = mount(
      <Result key={datasetData.id} result={datasetData} />,
    );
    // show datset result panel
    const button = datasetResultComponent.find('button');
    button.simulate('click');
    datasetResultComponent.update();
    expect(datasetResultComponent.exists()).toBeTruthy();
    expect(datasetResultComponent.find('li').length).toEqual(2);
    const datafileResultComponent = mount(
      <Result key={datafileData.id} result={datafileData} />,
    );
    expect(datafileResultComponent.exists()).toBeTruthy();
  });
  it('Test Render Simple Search Form', async () => {
    jest.spyOn(global, 'fetch').mockImplementation(() => Promise.resolve({
      json: () => Promise.resolve(apiResponse),
    }));
    let component = null;
    jest.spyOn(Date, 'now').mockImplementation(() => 1487076708000);
    await act(async () => {
      component = mount(<SimpleSearchForm showResults={showResults} searchText="test" />, { attachTo: container });
      expect(component).toBeTruthy();
    });
    expect(component.debug()).toMatchSnapshot();
    await act(async () => {
      component.find('button').at(0).simulate('click');
    });
    component.update();
    // expect fetch to be called
    expect(fetch.mock.calls.length).toEqual(3);
    expect(fetch.mock.calls[2][0]).toEqual('/api/v1/search_simple-search/?query=test');
  });
  it('Test Render Advanced Search Form', async () => {
    jest.spyOn(global, 'fetch').mockImplementationOnce(() => Promise.resolve({
      json: () => Promise.resolve(instrumentListResponse),
    }));
    const advanceSearchForm = mount(
      <AdvancedSearchForm searchText="test" showResults={showResults} instrumentList={[]} />,
    );
    expect(advanceSearchForm).toBeTruthy();
    // mock api response
    jest.spyOn(global, 'fetch').mockImplementation(() => Promise.resolve({
      json: () => Promise.resolve(apiResponse),
    }));
    await act(async () => {
      advanceSearchForm.find('button').at(3).simulate('click');
    });
    advanceSearchForm.update();
  });
});
