import React from 'react'
import { action } from '@storybook/addon-actions';
import EntryPreviewCard from './EntryPreviewCard';
import makeMockStore from "../../util/makeMockStore";
import { Provider } from 'react-redux';

const store = makeMockStore({
  search: {
    showSensitiveData: false
  }
});

export default {
  component: EntryPreviewCard,
  title: 'EntryPreviewCard',
  decorators: [story =>
    <Provider store={store}>
      <div style={{
        border: '2px solid black'
      }}>{story()}</div>
    </Provider>
  ],
};

const project = {
  "type": "project",
  "url": "idk/",
  "counts": {
    "datafiles": 2,
    "datasets": 1,
    "experiments": 1
  },
  "description": "If you can see this and are not called Mike(or Noel) then the permissions have gone wrong",
  "end_time": null,
  "id": 1,
  "institution": [
    {
      "name": "Mikes ACL Institution"
    }
  ],
  "lead_researcher": {
    "username": "mlav736"
  },
  "name": "Mikes_ACL_Project",
  "parameters": [
    {
      "data_type": "STRING",
      "pn_name": "18",
      "value": ""
    },
    {
      "data_type": "NUMERIC",
      "pn_name": "19",
      "value": "7.0"
    },
    {
      "data_type": "STRING",
      "pn_name": "15",
      "value": "Kiwi"
    },
    {
      "data_type": "STRING",
      "pn_name": "16",
      "value": "Orange"
    }
  ],
  "size": "460.3 KB",
  "start_time": "2020-05-07T21:34:44+00:00",
  "userDownloadRights": "partial"
}

const experiment = {
  "url": "idk/",
  "counts": {
    "datafiles": 2,
    "datasets": 1
  },
  "created_by": {
    "username": "mlav736"
  },
  "created_time": "2020-05-07T22:56:36.596706+00:00",
  "description": "here we go again",
  "end_time": null,
  "id": 4,
  "parameters": [
    {
      "data_type": "STRING",
      "pn_name": "1",
      "value": "kiwi"
    },
    {
      "data_type": "STRING",
      "pn_name": "3",
      "sensitive": "True",
      "value": "forbidden fruit"
    }
  ],
  "project": {
    "id": 1
  },
  "size": "460.3 KB",
  "start_time": null,
  "title": "Test_ACLs",
  "update_time": "2020-06-09T02:09:56.872730+00:00",
  "type": "experiment",
  "userDownloadRights": "partial"
}


const dataSet = {
  "url": "idk/",
  "counts": {
    "datafiles": 2
  },
  "created_time": "2020-05-07T23:00:05+00:00",
  "description": "Some ACL-testing dataset",
  "experiments": [
    {
      "id": 4,
      "project": {
        "id": 1
      }
    }
  ],
  "id": 1,
  "instrument": {
    "id": 1,
    "name": "Mikes_ACL_Machine"
  },
  "modified_time": "2020-06-09T02:10:18.426980+00:00",
  "parameters": [
    {
      "data_type": "STRING",
      "pn_name": "4",
      "value": "My Name"
    },
    {
      "data_type": "STRING",
      "pn_name": "5",
      "value": "is"
    }
  ],
  "size": "460.3 KB",
  "tags": "bricks safe as",
  "type": "dataset",
  "userDownloadRights": "partial"
}

const dataFile = {
  "url": "idk/",
  "type": "datafile",
  "created_time": null,
  "dataset": {
    "experiments": [
      {
        "id": 4,
        "project": {
          "id": 1
        }
      }
    ],
    "id": 1
  },
  "filename": "Mikes_test_datafile_1",
  "id": 1,
  "modification_time": null,
  "parameters": [
    {
      "data_type": "STRING",
      "pn_name": "12",
      "value": "My name is"
    }
  ],
  "size": "460.3 KB",
  "userDownloadRights": "full"
}

const projectWithNoChildren = Object.assign({}, project, {
  counts: {
    experiments: 0,
    datasets: 0,
    datafiles: 0
  }
})

const projectWithNoDate = Object.assign({}, project, {
  start_time: null
})

export const Project = () => (
  <EntryPreviewCard type="project" data={project} />
);

export const Experiment = () => (
  <EntryPreviewCard type="experiment" data={experiment} />
);

export const DataSet = () => (
  <EntryPreviewCard type="dataset" data={dataSet} />
);

export const DataFile = () => (
  <EntryPreviewCard type="datafile" data={dataFile} />
);

export const NoPreviewData = () => (
  <EntryPreviewCard type="datafile" data={null} />
);

export const NoChildren = () => (
  <EntryPreviewCard type="project" data={projectWithNoChildren} />
)

export const NoDate = () => (
  <EntryPreviewCard type="project" data={projectWithNoDate} />
)