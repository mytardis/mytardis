import { BeatLoader } from 'react-spinners';
import React from 'react';
import PropTypes from 'prop-types';

const Spinner = ({ override }) => (
  <BeatLoader css={override} color="#9B9B9B" size={10} />
);
Spinner.defaultProps = {
  override: {},
};
Spinner.propTypes = {
  override: PropTypes.object,
};
export default Spinner;
