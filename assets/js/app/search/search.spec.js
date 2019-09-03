import React from 'react'
import { configure } from 'enzyme';
import Adapter from 'enzyme-adapter-react-16';
import Search, {
  createExperimentResultData,
  createDatasetResultData,
  createDataFileResultData
} from "./components/Search";
import Result from './components/Result'
import Results from './components/Results'
import { shallow } from 'enzyme'
configure({ adapter: new Adapter() });
const result = {
  title: "Test Group - Test Experiment 1",
  description: "Uploader: Test Instrument",
  type: "experiment",
  id: '8369',
  url: "/experiment/view/8369/",
};

describe('Search Component', () => {
  it('Render Search Component',() => {
    const search = shallow(<Search/>);
    expect(search.exists()).toBeTruthy()
  })

});
describe('Results Component', () => {
  it('Render Results Component', () => {
    //const results = shallow(<Results counts={} results={}/>)
  })
});

describe('Result Component', () => {
  it('Test Result component',() => {
    const wrapper = shallow(<Result key={result.id} result={result} />);
    expect(wrapper.exists()).toBeTruthy()
  });
  it('Test createExperimentResultData function', () => {
    const apiResponse =
      '{\n' +
      '  "meta": {\n' +
      '    "limit": 20, \n' +
      '    "next": null, \n' +
      '    "offset": 0, \n' +
      '    "previous": null, \n' +
      '    "total_count": 1\n' +
      '  }, \n' +
      '  "objects": [\n' +
      '    {\n' +
      '      "hits": {\n' +
      '        "datafiles": [{\n' +
      '           "_id": "525", \n' +
      '           "_index": "datafile", \n' +
      '           "_score": 3.7592819, \n' +
      '           "_source": {\n' +
      '           "created_time": "2015-06-17T02:05:46+00:00", \n' +
      '           "dataset": {\n' +
      '             "experiments": [\n' +
      '               {\n' +
      '                 "id": 7, \n' +
      '                 "objectacls": [\n' +
      '                   {\n' +
      '                     "entityId": "13", \n' +
      '                     "pluginId": "django_user"\n' +
      '                   }\n' +
      '                  ], \n' +
      '                 "public_access": 1\n' +
      '               } \n' +
      '             ], \n' +
      '             "id": 13\n' +
      '           }, \n' +
      '           "filename": "02_MCB01.tif", \n' +
      '           "modification_time": null\n' +
      '          }, \n' +
      '          "_type": "doc"\n' +
      '        }], \n' +
      '        "datasets": [{\n' +
      '            "_id": "41079", \n' +
      '            "_index": "dataset", \n' +
      '            "_score": 4.3889866, \n' +
      '            "_source": {\n' +
      '              "created_time": "2017-02-02T00:20:35.882945+00:00", \n' +
      '              "description": "Experiment_notes", \n' +
      '              "experiments": [\n' +
      '                {\n' +
      '                  "id": 6292, \n' +
      '                  "objectacls": [\n' +
      '                    {\n' +
      '                      "entityId": "1033", \n' +
      '                      "pluginId": "django_user"\n' +
      '                    } \n' +
      '                  ], \n' +
      '                  "public_access": 100, \n' +
      '                  "title": "CT dose reduction "\n' +
      '                }\n' +
      '              ], \n' +
      '              "id": 41079, \n' +
      '              "instrument": {\n' +
      '                "id": 146, \n' +
      '                "name": "Genevieve_PC"\n' +
      '              }, \n' +
      '              "modified_time": "2019-04-30T23:21:04.112514+00:00"\n' +
      '            }, \n' +
      '            "_type": "doc"\n' +
      '          }], \n' +
      '        "experiments": [{\n' +
      '            "_id": "3883", \n' +
      '            "_index": "experiments", \n' +
      '            "_score": 2.622984, \n' +
      '            "_source": {\n' +
      '              "created_by": {\n' +
      '                "username": "testuser"\n' +
      '              }, \n' +
      '              "created_time": "2015-12-04T01:31:13.938888+00:00", \n' +
      '              "description": "", \n' +
      '              "end_time": null, \n' +
      '              "id": 3883, \n' +
      '              "institution_name": "Monash University", \n' +
      '              "objectacls": [\n' +
      '                {\n' +
      '                  "entityId": "13", \n' +
      '                  "pluginId": "django_user"\n' +
      '                } \n' +
      '              ], \n' +
      '              "public_access": 100, \n' +
      '              "start_time": null, \n' +
      '              "title": "Electron micrographs of hPrx3.", \n' +
      '              "update_time": "2015-12-04T05:29:16.000803+00:00"\n' +
      '            }, \n' +
      '            "_type": "doc"\n' +
      '          }]\n' +
      '      }, \n' +
      '      "resource_uri": "/api/v1/search_simple-search/1/"\n' +
      '    }\n' +
      '  ]\n' +
      '}';
    const data = JSON.parse(apiResponse);
    expect(data).toBeTruthy();
    let newResults = [];
    newResults = createExperimentResultData(data.objects[0].hits.experiments,newResults);
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
    const results = shallow(<Results counts={_counts} results={newResults}/>);
    expect(results).toBeTruthy()
  })

});