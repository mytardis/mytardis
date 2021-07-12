import React, { Fragment } from 'react';
import PropTypes from 'prop-types';


const ExperimentListDropDown = ({ onChange, experimentListData }) => (
  <Fragment>
    <form id="other-experiment-selection" className="form-horizontal">
      <fieldset>
        <div className="form-group">
          <label className="col-md-2 col-form-label" htmlFor="input01">Experiment</label>
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
      </fieldset>
    </form>
    <p className="help-text">
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
