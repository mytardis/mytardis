import React, { Fragment } from 'react';
import { css } from '@emotion/core';
import styled from '@emotion/styled';

const cardHover = css`
  border: 1px solid blue ;
  &:hover {
    transform: scale(1.05);
    box-shadow: 0 10px 20px rgba(0,0,0,.12), 0 4px 8px rgba(0,0,0,.06);
  }`;
const Hover = styled.div({
  ':hover': {
    transform: 'scale(1.05)',
    boxShadow: '0 10px 20px rgba(0,0,0,.12), 0 4px 8px rgba(0,0,0,.06)',
  },
});
const PublicationCard = ({ publicationType }) => (
  <Fragment>
    <div className="col mb-4">
      <Hover>
        <div className="card">
          <img src="https://dummyimage.com/600x400/000/fff.jpg&text=No+Image" className="card-img-top" alt="..." />
          <div className="card-body">
            {/* eslint-disable-next-line consistent-return */}
            {(() => {
              switch (publicationType) {
                case 'draft': return <span className="badge badge-secondary">Draft Publication</span>;
                default: return <span className="badge badge-success">Publication Released</span>;
                case 'scheduled': return <span className="badge badge-info">Publication Scheduled</span>;
                case 'retracted': return <span className="badge badge-danger">Publication Retracted</span>;
              }
            })()}

            <h5 className="card-title">X-ray diffraction images of trypsin crystals soaked with SFTI-TCTR(N12,N14) cyclopeptide inhibitor</h5>
            <p className="card-text">
              If you use this data, please cite: Chen, X. et al. Potent, multi-target serine protease inhibition achieved by a simplified β-sheet motif. PLoS One 14, e0210842 (2019). https://dx.doi.org/10.1371/journal.pone.0210842 Processed data available at PDB:6bvh.
            </p>
            <span className="badge badge-info mr-2">
              <a href="https://dx.doi.org/10.1371/journal.pone.0210842" className="card-link" style={{ color: 'Black' }}>DOI</a>
            </span>
            <span className="badge badge-info" title="Released on 31-05-21">
              31-05-21
            </span>

          </div>
          <div className="card-footer">
            {(() => {
              switch (publicationType) {
                case 'draft': return (
                  <Fragment>
                    <button type="button" className="btn btn-primary btn-sm mr-2 mb-1">
                      <i className="fa fa-edit mr-1" />
                      Resume Draft
                    </button>
                    <button type="button" className="btn btn-danger btn-sm mr-2 mb-1">
                      <i className="fa fa-trash mr-1" />
                      Delete Draft
                    </button>
                    <button type="button" className="btn btn-info btn-sm mr-2 mb-1">
                      Mint Doi
                    </button>
                    <button type="button" className="btn btn-success btn-sm mb-1">
                      <i className="fa fa-share-alt mr-1" />
                      Share
                    </button>
                  </Fragment>
                );
                default: return (
                  <Fragment>
                    <button type="button" className="btn btn-danger btn-sm mr-2 mb-1">
                      <i className="fa fa-exclamation-triangle mr-1" />
                      Retract
                    </button>
                  </Fragment>
                );
                case 'scheduled': return <span className="badge badge-info">Publication Scheduled</span>;
                case 'retracted': return <span />;
              }
            })()}

          </div>
        </div>
      </Hover>
    </div>
  </Fragment>
);
export default PublicationCard;
