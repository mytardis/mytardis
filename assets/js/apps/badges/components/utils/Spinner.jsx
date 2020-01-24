import { PropagateLoader } from 'react-spinners';
import React from 'react';
import { css } from '@emotion/core';

const Spinner = () => {
  const override = css`
    margin: auto;
    width: 20%;
    float: right;
    color: 9B9B9B;
  `;
  return (
    <PropagateLoader css={override} color="#9B9B9B" size={10} />
  );
};
export default Spinner;
