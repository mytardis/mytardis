import React from 'react'
import { action } from '@storybook/addon-actions';
import EntryPreviewCard from './EntryPreviewCard';

export default {
  component: EntryPreviewCard,
  title: 'EntryPreviewCard',
  // decorators: [story => <div style={{ padding: '3rem' }}>{story()}</div>],
  // excludeStories: /.*Data$/,
};

const projectData = {
  "counts": {
    "datafiles": 2,
    "datasets": 1,
    "experiments": 1
  },
  "description": "If you can see this and are not called Mike(or Noel) then the permissions have gone wrong",
  "end_date": null,
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
      "pn_id": "18",
      "sensitive": "False",
      "value": ""
    },
    {
      "data_type": "NUMERIC",
      "pn_id": "19",
      "sensitive": "False",
      "value": "7.0"
    },
    {
      "data_type": "STRING",
      "pn_id": "15",
      "sensitive": "False",
      "value": "Kiwi"
    },
    {
      "data_type": "STRING",
      "pn_id": "16",
      "sensitive": "False",
      "value": "Orange"
    }
  ],
  "size": "460.3 KB",
  "start_date": "2020-05-07T21:34:44+00:00",
  "userDownloadRights": "partial"
}

const experimentData = {
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
      "pn_id": "1",
      "sensitive": "False",
      "value": "kiwi"
    },
    {
      "data_type": "STRING",
      "pn_id": "3",
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
  "userDownloadRights": "partial"
}

export const Default = () => (
  <EntryPreviewCard type="project" data={projectData} />
);


export const Experiment = () => (
  <EntryPreviewCard type="experiment" data={experimentData} />
);