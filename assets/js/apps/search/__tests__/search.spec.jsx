import React from "react";
import { configure, shallow } from "enzyme/build";
import Adapter from "enzyme-adapter-react-16/build";
import Search, {
  createDataFileResultData,
  createDatasetResultData,
  createExperimentResultData,
} from "../components/Search";
import Result from "../components/Result";
import Results from "../components/Results";
import SimpleSearchForm from "../components/SimpleSearchForm";
import AdvancedSearchForm from "../components/AdvancedSearchForm";

global.fetch = require("jest-fetch-mock");

configure({ adapter: new Adapter() });

const experimentData = {
  title: "Test Group - Test Experiment 1",
  description: "Uploader: Test Instrument",
  type: "experiment",
  id: "8369",
  url: "/experiment/view/8369/",
};
const datasetData = {
  title: "Test Dataset",
  type: "dataset",
  id: 1234,
  url: "/dataset/1234",
  experiments: [],
  instrument: "Test Instrument",
  created_time: "2017-02-02T00:20:35.882945+00:00",
  update_time: "2017-02-02T00:20:35.882945+00:00",
};
const datafileData = {
  title: "Test_file.tiff",
  type: "datafile",
  id: 1234,
  url: "/datafile/view/1234",
  created_time: "2017-02-02T00:20:35.882945+00:00",
  update_time: "2017-02-02T00:20:35.882945+00:00",
  dataset_description: "Test Dataset",
  dataset_url: "/dataset/1234",
};

const apiResponse = "{\n"
  + "  \"meta\": {\n"
  + "    \"limit\": 20, \n"
  + "    \"next\": null, \n"
  + "    \"offset\": 0, \n"
  + "    \"previous\": null, \n"
  + "    \"total_count\": 1\n"
  + "  }, \n"
  + "  \"objects\": [\n"
  + "    {\n"
  + "      \"hits\": {\n"
  + "        \"datafiles\": [{\n"
  + "           \"_id\": \"525\", \n"
  + "           \"_index\": \"datafile\", \n"
  + "           \"_score\": 3.7592819, \n"
  + "           \"_source\": {\n"
  + "           \"created_time\": \"2015-06-17T02:05:46+00:00\", \n"
  + "           \"dataset\": {\n"
  + "             \"experiments\": [\n"
  + "               {\n"
  + "                 \"id\": 7, \n"
  + "                 \"objectacls\": [\n"
  + "                   {\n"
  + "                     \"entityId\": \"13\", \n"
  + "                     \"pluginId\": \"django_user\"\n"
  + "                   }\n"
  + "                  ], \n"
  + "                 \"public_access\": 1\n"
  + "               } \n"
  + "             ], \n"
  + "             \"id\": 13\n"
  + "           }, \n"
  + "           \"filename\": \"02_MCB01.tif\", \n"
  + "           \"modification_time\": null\n"
  + "          }, \n"
  + "          \"_type\": \"doc\"\n"
  + "        }], \n"
  + "        \"datasets\": [{\n"
  + "            \"_id\": \"41079\", \n"
  + "            \"_index\": \"dataset\", \n"
  + "            \"_score\": 4.3889866, \n"
  + "            \"_source\": {\n"
  + "              \"created_time\": \"2017-02-02T00:20:35.882945+00:00\", \n"
  + "              \"description\": \"Experiment_notes\", \n"
  + "              \"experiments\": [\n"
  + "                {\n"
  + "                  \"id\": 6292, \n"
  + "                  \"objectacls\": [\n"
  + "                    {\n"
  + "                      \"entityId\": \"1033\", \n"
  + "                      \"pluginId\": \"django_user\"\n"
  + "                    } \n"
  + "                  ], \n"
  + "                  \"public_access\": 100, \n"
  + "                  \"title\": \"CT dose reduction \"\n"
  + "                }\n"
  + "              ], \n"
  + "              \"id\": 41079, \n"
  + "              \"instrument\": {\n"
  + "                \"id\": 146, \n"
  + "                \"name\": \"Genevieve_PC\"\n"
  + "              }, \n"
  + "              \"modified_time\": \"2019-04-30T23:21:04.112514+00:00\"\n"
  + "            }, \n"
  + "            \"_type\": \"doc\"\n"
  + "          }], \n"
  + "        \"experiments\": [{\n"
  + "            \"_id\": \"3883\", \n"
  + "            \"_index\": \"experiments\", \n"
  + "            \"_score\": 2.622984, \n"
  + "            \"_source\": {\n"
  + "              \"created_by\": {\n"
  + "                \"username\": \"testuser\"\n"
  + "              }, \n"
  + "              \"created_time\": \"2015-12-04T01:31:13.938888+00:00\", \n"
  + "              \"description\": \"\", \n"
  + "              \"end_time\": null, \n"
  + "              \"id\": 3883, \n"
  + "              \"institution_name\": \"Monash University\", \n"
  + "              \"objectacls\": [\n"
  + "                {\n"
  + "                  \"entityId\": \"13\", \n"
  + "                  \"pluginId\": \"django_user\"\n"
  + "                } \n"
  + "              ], \n"
  + "              \"public_access\": 100, \n"
  + "              \"start_time\": null, \n"
  + "              \"title\": \"Electron micrographs of hPrx3.\", \n"
  + "              \"update_time\": \"2015-12-04T05:29:16.000803+00:00\"\n"
  + "            }, \n"
  + "            \"_type\": \"doc\"\n"
  + "          }]\n"
  + "      }, \n"
  + "      \"resource_uri\": \"/api/v1/search_simple-search/1/\"\n"
  + "    }\n"
  + "  ]\n"
  + "}";

describe("Search Component", () => {
  it("Render Search Component", () => {
    const search = shallow(<Search />);
    expect(search.exists()).toBeTruthy();
  });
});
describe("Results Component", () => {
  it("Render Results Component", () => {
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

describe("Result Component", () => {
  let showResults;
  beforeEach(() => {
    showResults = (() => {
    });
    return showResults;
  });
  it("Test Render Result component", () => {
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
  it("Test Render Simple Search Form", () => {
    const simpleSearchForm = shallow(<SimpleSearchForm showResults={showResults} searchText="test" />);
    expect(simpleSearchForm).toBeTruthy();
  });
  it("Test Render Advance Search Form", () => {
    const advanceSearchForm = shallow(
      <AdvancedSearchForm searchText="test" showResults={showResults} instrumentList={[]} />,
    );
    expect(advanceSearchForm).toBeTruthy();
  });
});
