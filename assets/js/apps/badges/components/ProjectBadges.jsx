import React, { Fragment, useState } from 'react';
import ReactDOM from 'react-dom';

import PropTypes from 'prop-types';
import { css } from '@emotion/react';
import PublicAccessBadge from './PublicAccessBadge';
import ExperimentCountBadge from './ExperimentCountBadge';
import DatasetCountBadge from './DatasetCountBadge';
import DatafileCountBadge from './DatafileCountBadge';
import { fetchProjectData } from './utils/FetchData';
import Spinner from './utils/Spinner';


const ProjectBadges = ({ projectID }) => {
  const [projData, setProjData] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const spinnerCss = css`
    margin: auto;
    width: 20%;
    float: right;
    color: 9B9B9B;
  `;
  React.useEffect(() => {
    fetchProjectData(projectID).then((data) => {
      setProjData(data);
      setIsLoading(false);
    });
  }, []);
  return (
    isLoading ? <Spinner override={spinnerCss} />
      : (
        <Fragment>
          <ul className="list-inline float-end list-unstyled">
            <li className="mr-1 list-inline-item">
              <ExperimentCountBadge projectData={projData} />
            </li>
            <li className="mr-1 list-inline-item">
              <DatasetCountBadge experimentData={projData} />
            </li>
            <li className="mr-1 list-inline-item">
              <DatafileCountBadge experimentData={projData} />
            </li>
            <li className="mr-1 list-inline-item">
              <PublicAccessBadge experimentData={projData} />
            </li>
          </ul>
        </Fragment>
      )
  );
};

ProjectBadges.propTypes = {
  projectID: PropTypes.string.isRequired,
};

document.querySelectorAll('.projectbadges')
  .forEach((domContainer) => {
    const projectID = domContainer.id.split('-')[1];
    ReactDOM.render(
      <ProjectBadges projectID={projectID} />, domContainer,
    );
  });

export default ProjectBadges;
