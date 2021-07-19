import React, { useState } from 'react';
import PropTypes from 'prop-types';

function Result({ result }) {
  const [dataToggleClass, setDataToggleClass] = useState(false);
  const dataToggler = () => {
    setDataToggleClass(!dataToggleClass);
  };
  const getDatasetData = datasetResult => (
    <div className="accordion-group" style={{ marginLeft: 20 }}>
      <div className="accordion-heading">
        <div className="accordion-body">
          <span style={{ fontSize: 11, fontStyle: 'italic' }}>
            {`This dataset belongs to the following ${datasetResult.experiments.length} experiment(s):`}
          </span>
          <ul>
            {datasetResult.experiments.map(res => (
              <li key={res.id}><a href={`/experiment/view/${res.id}/`}>{res.title}</a></li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
  const getExperimentData = experimentResult => (
    <div className="accordion-group" style={{ marginLeft: 20 }}>
      <div className="accordion-heading">
        <div className="accordion-body">
          <div>{experimentResult.description}</div>
        </div>
      </div>
    </div>
  );
  const getDataFileData = datafileResult => (
    <div className="accordion-group" style={{ marginLeft: 20 }}>
      <div className="accordion-heading">
        <div className="accordion-body">
          <span style={{ fontSize: 11, fontStyle: 'italic' }}>
            This datafile is from following dataset:
          </span>
          <div>
            <span style={{ fontWeight: 'bold', marginLeft: 5 }}>
              <a href={datafileResult.dataset_url}>{datafileResult.dataset_description}</a>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
  return (
    <div className="result" id={`${result.type}-${result.id}`}>
      <div className="panel panel-default">
        <div className="panel-body">
          {result.type === 'dataset'
          && (
          <div>
            <button
              type="button"
              onClick={dataToggler}
              className="btn btn-link"
              data-bs-target="#data"
              name="showChild"
            >
              <i className={dataToggleClass ? 'fa fa-plus' : 'fa fa-minus'} />
            </button>
            <a style={{ fontWeight: 'bold' }} href={result.url}>{result.title}</a>
            <ul
              className="nav nav-pills badgelist float-end"
              style={{ display: 'inline-block' }}
            >
              <li className="float-end">
                <span
                  className="badge bg-info me-2"
                  title={`Date Created: ${result.created_time}`}
                >
                  <i className="fa fa-clock-o" />
                  <span>
                    {result.created_time}
                  </span>
                </span>
              </li>
              {result.instrument
              && (
              <li className="float-end">
                <span
                  className="badge bg-info me-2"
                  title={`Instrument Name: ${result.instrument}`}
                >
                  {/* upgrade to font-awesome 5 will bring this icon */}
                  <i className="fa fa-microscope" />
                  <span>
                    {result.instrument}
                  </span>
                </span>
              </li>
              )}
            </ul>
            <div id="data">
              {!dataToggleClass && getDatasetData(result)}
            </div>
          </div>
          )
          }
          {result.type === 'experiment'
          && (
          <div>
            <button
              type="button"
              onClick={dataToggler}
              className="btn btn-link"
              data-bs-target="#data"
              name="showChild"
            >
              <i className={dataToggleClass ? 'fa fa-plus' : 'fa fa-minus'} />
            </button>
            <a style={{ fontWeight: 'bold', display: 'inline-block' }} href={result.url}>{result.title}</a>
            <ul className="nav nav-pills badgelist float-end" style={{ display: 'inline-block' }}>
              <li className="float-end">
                <span
                  className="badge bg-info me-2"
                  title={`Date Created: ${result.created_time}`}
                >
                  <i className="fa fa-clock-o" />
                  <span>
                    {result.created_time}
                  </span>
                </span>
              </li>
              <li className="float-end">
                <span
                  className="badge bg-info me-2"
                  title={`Created by: ${result.created_by}`}
                >
                  <i className="fa fa-user" />
                  <span>
                    {result.created_by}
                  </span>
                </span>
              </li>
              {result.institution_name
              && (
                <li className="float-end">
                  <span
                    className="badge bg-info me-2"
                    title={`Institution Name: ${result.institution_name}`}
                  >
                    <i className="fa fa-institution" />
                    <span>
                      {result.institution_name}
                    </span>
                  </span>
                </li>
              )}
            </ul>
            <div id="data">
              {!dataToggleClass && getExperimentData(result)}
            </div>
          </div>
          )
          }
          {result.type === 'datafile'
          && (
          <div>
            <button
              type="button"
              onClick={dataToggler}
              className="btn btn-link"
              data-bs-target="#data"
              name="showChild"
            >
              <i className={dataToggleClass ? 'fa fa-plus' : 'fa fa-minus'} />
            </button>
            <a style={{ fontWeight: 'bold' }} href={result.url}>{result.title}</a>
            <ul className="nav nav-pills badgelist float-end" style={{ display: 'inline-block' }}>
              <li className="float-end">
                <span
                  className="badge bg-info me-2"
                  title={`Date Created: ${result.created_time}`}
                >
                  <i className="fa fa-clock-o" />
                  <span>
                    {result.created_time}
                  </span>
                </span>
              </li>
            </ul>
            <div id="data">{!dataToggleClass && getDataFileData(result)}</div>
          </div>
          )
          }
        </div>
      </div>
    </div>
  );
}
Result.propTypes = {
  result: PropTypes.shape({
    id: PropTypes.number.isRequired,
    type: PropTypes.string.isRequired,
    title: PropTypes.string.isRequired,
    url: PropTypes.string.isRequired,
    created_time: PropTypes.string.isRequired,
    update_time: PropTypes.string.isRequired,
    description: PropTypes.string,
    institution_name: PropTypes.string,
    instrument: PropTypes.string,
    created_by: PropTypes.string,
    dataset_description: PropTypes.string,
    dataset_url: PropTypes.string,
  }).isRequired,
};

export default Result;
