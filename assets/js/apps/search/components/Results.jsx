import React from 'react';
import PropTypes from 'prop-types';

import Result from './Result';

function Results({ results, counts }) {
  return (
    <div style={{ marginTop: 15 }}>
      <div className="container" style={{ marginBottom: 10 }}>
        <h2>Search Results </h2>
      </div>
      <div id="tabbed-pane" className="container">
        <ul className="nav nav-tabs" style={{ fontWeight: 600 }} id="searchTab" role="tablist">
          <li className="nav-item">
            <a
              className="nav-link active"
              id="experiments-tab"
              data-bs-toggle="tab"
              href="#experiments"
              role="tab"
              aria-controls="experiments"
              aria-selected="true"
            >
              <i className="fa fa-flask fa-2x" />
              Experiments
              <span className="badge badge-secondary count-badge">{counts.experimentsCount}</span>
            </a>
          </li>
          <li className="nav-item">
            <a
              className="nav-link"
              id="datasets-tab"
              data-bs-toggle="tab"
              href="#datasets"
              role="tab"
              aria-controls="profile"
              aria-selected="false"
            >
              <i className="fa fa-folder fa-2x" />
              Datasets
              <span className="badge badge-secondary count-badge">{counts.datasetsCount}</span>
            </a>
          </li>
          <li className="nav-item">
            <a
              className="nav-link"
              id="datafiles-tab"
              data-bs-toggle="tab"
              href="#datafiles"
              role="tab"
              aria-controls="contact"
              aria-selected="false"
            >
              <i className="fa fa-file fa-2x" />
              Datafiles
              <span className="badge badge-secondary count-badge">{counts.datafilesCount}</span>
            </a>
          </li>
        </ul>
        <div className="tab-content" id="myTabContent">
          <div className="tab-pane fade show active" id="experiments" role="tabpanel" aria-labelledby="experiments-tab">
            <div className="result-list">
              { counts.experimentsCount === 0
                ? <span>No matching experiment found.</span> : <span /> }
              {results.map(
                (result) => {
                  let res = '';
                  if (result.type === 'experiment') {
                    res = <Result key={result.id} result={result} />;
                  }
                  return res;
                },
              )}
            </div>
          </div>
          <div className="tab-pane fade" id="datasets" role="tabpanel" aria-labelledby="datasets-tab">
            <div className="result-list">
              { counts.datasetsCount === 0
                ? <span>No matching dataset found.</span> : <span />
              }
              {results.map(
                (result) => {
                  let res = '';
                  if (result.type === 'dataset') {
                    res = <Result key={result.id} result={result} />;
                  }
                  return res;
                },
              )}
            </div>
          </div>
          <div className="tab-pane fade" id="datafiles" role="tabpanel" aria-labelledby="datafiles-tab">
            <div className="result-list">
              { counts.datafilesCount === 0
                ? <span>No matching datafile found.</span> : <span />
              }
              {results.map(
                (result) => {
                  let res = '';
                  if (result.type === 'datafile') {
                    res = <Result key={result.id} result={result} />;
                  }
                  return res;
                },
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
Results.propTypes = {
  results: PropTypes.arrayOf(
    PropTypes.shape({
      title: PropTypes.string.isRequired,
      type: PropTypes.string.isRequired,
      id: PropTypes.number.isRequired,
      url: PropTypes.string.isRequired,
      institution_name: PropTypes.string,
      created_time: PropTypes.string.isRequired,
      update_time: PropTypes.string.isRequired,
      created_by: PropTypes.string.isRequired,
    }),
  ).isRequired,
  counts: PropTypes.object.isRequired,
};

export default Results;
