import React, { useState } from 'react';

import Results from './Results';
import SimpleSearchForm from './SimpleSearchForm';

const queryString = require('query-string');

const parsed = queryString.parse(window.location.search);

export function createExperimentResultData(hits, newResults) {
  hits.forEach((hit) => {
    const createdTime = new Date(hit._source.created_time).toDateString();
    const updateTime = new Date(hit._source.update_time).toDateString();
    let renderedDescription = hit._source.description;
    if (renderedDescription === '') {
      renderedDescription = 'No description available for this experiment';
    }
    newResults = [...newResults, {
      title: hit._source.title,
      description: renderedDescription,
      type: 'experiment',
      id: hit._source.id,
      url: `/experiment/view/${hit._source.id}/`,
      institution_name: hit._source.institution_name,
      created_time: createdTime,
      update_time: updateTime,
      created_by: hit._source.created_by.username,
    },
    ];
  });
  return newResults;
}
export function createDatasetResultData(hits, newResults) {
  hits.forEach((hit) => {
    const createdTime = new Date(hit._source.created_time).toDateString();
    const updateTime = new Date(hit._source.modified_time).toDateString();
    newResults = [...newResults, {
      title: hit._source.description,
      type: 'dataset',
      id: hit._source.id,
      url: `/dataset/${hit._source.id}`,
      experiments: hit._source.experiments,
      instrument: hit._source.instrument.name,
      created_time: createdTime,
      update_time: updateTime,
    },
    ];
  });
  return newResults;
}
export function createDataFileResultData(hits, newResults) {
  hits.forEach((hit) => {
    const createdTime = new Date(hit._source.created_time).toDateString();
    const updateTime = new Date(hit._source.modification_time).toDateString();
    newResults = [...newResults, {
      title: hit._source.filename,
      type: 'datafile',
      id: hit._id,
      url: `/datafile/view/${hit._id}`,
      created_time: createdTime,
      update_time: updateTime,
      dataset_description: hit._source.dataset.description,
      dataset_url: `/dataset/${hit._source.dataset.id}`,
    },
    ];
  });
  return newResults;
}

function Search() {
  const [results, setResults] = useState([]);
  const [counts, setCounts] = useState([]);
  const searchText = !parsed.q ? '' : parsed.q;
  const showResults = ((result) => {
    let newResults = [];
    const _counts = {
      experimentsCount: 0,
      datasetsCount: 0,
      datafilesCount: 0,
    };
    const experimentsHits = result.hits.experiments;
    // create experiment result
    newResults = createExperimentResultData(experimentsHits, newResults);
    _counts.experimentsCount = experimentsHits.length;
    // create dataset result
    const datasetHits = result.hits.datasets;
    newResults = createDatasetResultData(datasetHits, newResults);
    _counts.datasetsCount = datasetHits.length;
    // create datafile results
    const datafileHits = result.hits.datafiles;
    newResults = createDataFileResultData(datafileHits, newResults);
    _counts.datafilesCount = datafileHits.length;
    setResults(newResults);
    setCounts(_counts);
  });
  return (
    <div className="row justify-content-center">
      <div className="col-sm-8">
        <SimpleSearchForm showResults={showResults} searchText={searchText} />
        <Results results={results} counts={counts} />
      </div>
    </div>
  );
}

export default Search;
