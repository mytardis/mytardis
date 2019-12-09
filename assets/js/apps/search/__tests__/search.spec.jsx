import React from 'react';
import { configure, shallow } from 'enzyme/build';
import Adapter from 'enzyme-adapter-react-16/build';
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
  experiments: [],
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

const apiResponse = `{
   "meta": {
     "limit": 20,
     "next": null,
     "offset": 0,
     "previous": null,
     "total_count": 1
   },
   "objects": [
     {
       "hits": {
         "datafiles": [{
            "_id": "525",
            "_index": "datafile",
            "_score": 3.7592819,
            "_source": {
            "created_time": "2015-06-17T02:05:46+00:00",
            "dataset": {
              "experiments": [
                {
                  "id": 7,
                  "objectacls": [
                    {
                      "entityId": "13",
                      "pluginId": "django_user"
                    }
                   ],
                  "public_access": 1
                }
              ],
              "id": 13
            },
            "filename": "02_MCB01.tif",
            "modification_time": null
           },
           "_type": "doc"
         }],
         "datasets": [{
             "_id": "41079",
             "_index": "dataset",
             "_score": 4.3889866,
             "_source": {
               "created_time": "2017-02-02T00:20:35.882945+00:00",
               "description": "Experiment_notes",
               "experiments": [
                 {
                   "id": 6292,
                   "objectacls": [
                     {
                       "entityId": "1033",
                       "pluginId": "django_user"
                     }
                   ],
                   "public_access": 100,
                   "title": "CT dose reduction "
                 }
               ],
               "id": 41079,
               "instrument": {
                 "id": 146,
                 "name": "Genevieve_PC"
               },
               "modified_time": "2019-04-30T23:21:04.112514+00:00"
             },
             "_type": "doc"
           }],
         "experiments": [{
             "_id": "3883",
             "_index": "experiments",
             "_score": 2.622984,
             "_source": {
               "created_by": {
                 "username": "testuser"
               },
               "created_time": "2015-12-04T01:31:13.938888+00:00",
               "description": "",
               "end_time": null,
               "id": 3883,
               "institution_name": "Monash University",
               "objectacls": [
                 {
                   "entityId": "13",
                   "pluginId": "django_user"
                 }
               ],
               "public_access": 100,
               "start_time": null,
               "title": "Electron micrographs of hPrx3.",
               "update_time": "2015-12-04T05:29:16.000803+00:00"
             },
             "_type": "doc"
           }]
       },
       "resource_uri": "/api/v1/search_simple-search/1/"
     }
   ]
}
`;

describe('Search Component', () => {
  it('Render Search Component', () => {
    const search = shallow(<Search />);
    expect(search.exists()).toBeTruthy();
  });
});
describe('Results Component', () => {
  it('Render Results Component', () => {
    const data = JSON.parse(apiResponse);
    expect(data).toBeTruthy();
    let newResults = [];
    newResults = createExperimentResultData(data.objects[0].hits.experiments, newResults);
    expect(newResults).toBeTruthy();
    newResults = createDatasetResultData(data.objects[0].hits.datasets, newResults);
    expect(newResults).toBeTruthy();
    newResults = createDataFileResultData(data.objects[0].hits.datafiles, newResults);
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
    const experimentResultComponent = shallow(
      <Result key={experimentData.id} result={experimentData} />,
    );
    expect(experimentResultComponent.exists()).toBeTruthy();
    const datasetResultComponent = shallow(
      <Result key={datasetData.id} result={datasetData} />,
    );
    expect(datasetResultComponent.exists()).toBeTruthy();
    const datafileResultComponent = shallow(
      <Result key={datafileData.id} result={datafileData} />,
    );
    expect(datafileResultComponent.exists()).toBeTruthy();
  });
  it('Test Render Simple Search Form', () => {
    const simpleSearchForm = shallow(<SimpleSearchForm showResults={showResults} searchText="test" />);
    expect(simpleSearchForm).toBeTruthy();
  });
  it('Test Render Advance Search Form', () => {
    const advanceSearchForm = shallow(
      <AdvancedSearchForm searchText="test" showResults={showResults} instrumentList={[]} />,
    );
    expect(advanceSearchForm).toBeTruthy();
  });
});
