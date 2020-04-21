import React, { Fragment, useEffect, useState } from 'react';
import { fetchExperimentList } from './utils/FetchData';


const ExperimentListDropDown = ({ onChange, value }) => {
  const [experimentListData, setExperimentListData] = useState([]);
  useEffect(() => {
    fetchExperimentList().then(result => setExperimentListData(result));
  }, []);
  return (
    <Fragment>
      <form id="other-experiment-selection" className="form-horizontal">
        <fieldset>
          <div className="form-group">
            <label className="col-md-2 col-form-label" htmlFor="input01">Experiment</label>
            <div className="col-md-10">
              <select
                onChange={onChange}
                value={value}
                className="form-control"
                name="experiment_id"
              >
                {experimentListData.map(
                  exp => (
                    <option value={exp.id} key={exp.id}>{exp.title}</option>),
                )}
              </select>
            </div>
          </div>
        </fieldset>
      </form>
      <p className="help-text">
        <strong>Instructons:</strong> Using the above list, select an experiment to copy from,
        then drag datasets to the right to associate them with the current experiment.
      </p>
    </Fragment>
  );
};

export default ExperimentListDropDown;
