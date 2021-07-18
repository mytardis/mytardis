import React, { Fragment } from 'react';
import PropTypes from 'prop-types';


const ExperimentListDropDown = ({ onChange, experimentListData }) => (
  <Fragment>
    <form id="other-experiment-selection" className="form-horizontal">
      <div className="row">
        <div className="col-md-2">
          <label className="form-label" htmlFor="experiment_id">Experiment</label>
        </div>
        <div className="col-md-10">
          <select
            onChange={onChange}
            className="form-select"
            name="experiment_id"
          >
            {experimentListData.map(
              exp => (
                <option value={exp.id} key={exp.id}>{exp.title}</option>),
            )}
          </select>
        </div>
      </div>
    </form>
    <p className="mt-3">
      <strong>Instructons:</strong>
      {' '}
      Using the above list, select an experiment to copy from,
      then drag datasets to the right to associate them with the current experiment.
    </p>
  </Fragment>
);
ExperimentListDropDown.propTypes = {
  onChange: PropTypes.func.isRequired,
  experimentListData: PropTypes.array.isRequired,
};
export default ExperimentListDropDown;
