import PropTypes from 'prop-types';
import React, { Fragment } from 'react';
import styled from '@emotion/styled';
import { Button } from 'react-bootstrap';
import moment from 'moment';

const Hover = styled.card({
  ':hover': {
    transform: 'scale(1.01)',
    boxShadow: '0 10px 20px rgba(0,0,0,.12), 0 4px 8px rgba(0,0,0,.06)',
  },
});

const PublicationCard = ({
  publicationType, data, handleDelete, handleRetract, handleResume, colNum,
}) => (
  <Fragment>
    <div className={`col-md-${colNum} col-xs-12 pb-3`}>
      <Hover className="card h-100">
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

          <h5 className="card-title">{data.title}</h5>
          <p className="card-text text-muted">
            {data.description}
          </p>
          {/* eslint-disable-next-line consistent-return */}
          {(() => {
            switch (publicationType) {
              case 'draft': return (
                <>
                  {data.doi ? (
                    <span className="badge badge-info mr-2">
                      <a href="https://dx.doi.org/10.1371/journal.pone.0210842" className="card-link" style={{ color: 'Black' }}>{data.doi}</a>
                    </span>
                  ) : <></>}
                  {data.releaseDate ? (
                    <span className="text-muted" title={`Release Date ${moment(data.release_date, 'YYYY-MM-DD').format('ll')}`}>
                      {`Release Date ${moment(data.release_date, 'YYYY-MM-DD').format('ll')}`}
                    </span>
                  ) : <></>}
                </>
              );
              case 'released': return (
                <>
                  {data.doi
                    ? (
                      <span className="badge badge-info mr-2">
                        <a href="https://dx.doi.org/10.1371/journal.pone.0210842" className="card-link" style={{ color: 'Black' }}>{data.doi}</a>
                      </span>
                    ) : <></>
                    }

                  <span className="text-muted" title={`Released on ${moment(data.release_date, 'YYYY-MM-DD').format('ll')}`}>
                    {`Released on ${moment(data.release_date, 'YYYY-MM-DD').format('ll')}`}
                  </span>
                </>
              );
              case 'retracted': return (
                <>
                  {data.doi ? (
                    <span className="badge badge-info mr-2">
                      <a href="https://dx.doi.org/10.1371/journal.pone.0210842" className="card-link" style={{ color: 'Black' }}>{data.doi}</a>
                    </span>
                  ) : <></>}
                  <div>
                    <span className="text-muted" style={{ whiteSpace: 'nowrap' }} title={`Released on ${moment(data.release_date, 'YYYY-MM-DD').format('ll')}`}>
                      {`Released on ${moment(data.release_date, 'YYYY-MM-DD').format('ll')}`}
                    </span>
                  </div>
                  <div>
                    <span className="text-muted" style={{ whiteSpace: 'nowrap' }} title={`Retracted on ${moment(data.retracted_date, 'YYYY-MM-DD').format('ll')}`}>
                      {`Retracted on ${moment(data.retracted_date, 'YYYY-MM-DD').format('ll')}`}
                    </span>
                  </div>

                </>
              );
              default: return (
                <>
                  {data.doi ? (
                    <span className="badge badge-info mr-2">
                      <a href="https://dx.doi.org/10.1371/journal.pone.0210842" className="card-link" style={{ color: 'Black' }}>{data.doi}</a>
                    </span>
                  ) : <></>}

                  <span className="text-muted" title={`Scheduled Released on ${moment(data.release_date, 'YYYY-MM-DD').format('ll')}`}>
                    {`Scheduled Released on ${moment(data.release_date, 'YYYY-MM-DD').format('ll')}`}
                  </span>
                </>
              );
            }
          })()}
        </div>
        <div className="card-footer">
          {(() => {
            switch (publicationType) {
              case 'draft': return (
                <Fragment>
                  <button type="button" onClick={e => handleResume(e, data.id)} className="btn btn-primary btn-sm mr-2 mb-1">
                    <i className="fa fa-edit mr-1" />
                    Resume Draft
                  </button>
                  <Button onClick={e => handleDelete(e, data.id)} className="btn btn-danger btn-sm mr-2 mb-1">
                    <i className="fa fa-trash mr-1" />
                    Delete Draft
                  </Button>
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
                  <button onClick={e => handleRetract(e, data.id)} type="button" className="btn btn-danger btn-sm mr-2 mb-1">
                    <i className="fa fa-exclamation-triangle mr-1" />
                    Retract
                  </button>
                </Fragment>
              );
              case 'scheduled': return <span />;
              case 'retracted': return <span />;
            }
          })()}
        </div>
      </Hover>
    </div>
  </Fragment>
);
export default PublicationCard;

PublicationCard.defaultProps = {
  handleDelete: () => {},
  handleRetract: () => {},
  handleResume: () => {},
};

PublicationCard.propTypes = {
  colNum: PropTypes.number.isRequired,
  data: PropTypes.object.isRequired,
  handleDelete: PropTypes.func,
  handleResume: PropTypes.func,
  handleRetract: PropTypes.func,
  publicationType: PropTypes.string.isRequired,
};
