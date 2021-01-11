import React, { Fragment } from 'react';
import Spinner from '../../badges/components/utils/Spinner';

const Loading = () => (
  <Fragment>
    <span style={{ opacity: 0.5 }}>
      Loading Sub Folders/Files..
      <Spinner />
    </span>
  </Fragment>
);

export default Loading;
