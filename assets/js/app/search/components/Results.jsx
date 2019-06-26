import React from "react";
import PropTypes from "prop-types";

import Result from "./Result";

function Results({ results, counts }) {
  return (
    <div style={{ marginTop: 15 }}>
      <div className="container" style={{ marginBottom: 10 }}>
        <h2>Search Results </h2>
      </div>
      <div id="tabbed-pane" className="container">
        <ul className="nav nav-tabs" style={{ fontWeight: 600 }}>
          <li className="active">
            <a href="#1a" data-toggle="tab">
              <i className="fa fa-flask fa-2x" />
              Experiments
              <span className="badge badge-light">{counts.experimentsCount}</span>
            </a>
          </li>
          <li>
            <a href="#2a" data-toggle="tab">
              <i className="fa fa-folder fa-2x" />
              Datasets
              <span className="badge badge-light">{counts.datasetsCount}</span>
            </a>
          </li>
          <li>
            <a href="#3a" data-toggle="tab">
              <i className="fa fa-file fa-2x" />
              Datafiles
              <span className="badge badge-light">{counts.datafilesCount}</span>
            </a>
          </li>
        </ul>
        <div className="tab-content">
          <div className="tab-pane active" id="1a">
            <div className="result-list">
              { counts.experimentsCount === 0
                ? <span>No matching experiment found.</span> : <span /> }
              {results.map(
                (result) => {
                  let res = "";
                  if (result.type === "experiment") {
                    res = <Result key={result.id} result={result} />;
                  } else {
                    res = <span />;
                  }
                  return res;
                },
              )}
            </div>
          </div>
          <div className="tab-pane" id="2a">
            <div className="result-list">
              { counts.datasetsCount === 0
                ? <span>No matching dataset found.</span> : <span />
              }
              {results.map(
                (result) => {
                  let res = "";
                  if (result.type === "dataset") {
                    res = <Result key={result.id} result={result} />;
                  } else {
                    res = <span />;
                  }
                  return res;
                },
              )}
            </div>
          </div>
          <div className="tab-pane" id="3a">
            <div className="result-list">
              { counts.datafilesCount === 0
                ? <span>No matching datafile found.</span> : <span />
              }
              {results.map(
                (result) => {
                  let res = "";
                  if (result.type === "datafile") {
                    res = <Result key={result.id} result={result} />;
                  } else {
                    res = <span />;
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
      id: PropTypes.string.isRequired,
      url: PropTypes.string.isRequired,
      institution_name: PropTypes.string.isRequired,
      created_time: PropTypes.instanceOf(Date).isRequired,
      update_time: PropTypes.instanceOf(Date).isRequired,
      created_by: PropTypes.string.isRequired,
    }),
  ).isRequired,
  counts: PropTypes.shape({
    experimentsCount: PropTypes.number.isRequired,
    datasetsCount: PropTypes.number.isRequired,
    datafilesCount: PropTypes.number.isRequired,
  }).isRequired,
};

export default Results;
