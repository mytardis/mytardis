import React from 'react';
import styled from '@emotion/styled';

const ProgressBar = ({ activeStep }) => {
  const ProgressBarList = styled.ul`
        margin-bottom: 30px;
        overflow: hidden;
        counter-reset: step;
  `;

  const ProgressBarListItem = styled.li`
        list-style-type: none;
        text-transform: uppercase;
        width: 23.3%;
        float: left;
        position: relative;
        font-size: 10px;
        text-align: center;
        &.active:before, &.active:after {
            background:  #27AE60;
            color: white;
        }
        &:before {
            content: counter(step);
            counter-increment: step;
            width: 30px;
            line-height: 30px;
            display: block;
            font-size: 25px;
            color: white;
            background: grey;
            border-radius: 15px;
            margin: 0 auto 5px auto;
            z-index: 99999;
            position: relative
        }
        }
        &:after {
            content: '';
            width: 90%;
            height: 2px;
            background: grey;
            position: absolute;
            left: -46%;
            top: 15px;
        }
        &:first-child:after {
            content: none;
        }
  `;
  const items = ['Select Dataset', 'Extra Information', 'Attribution', 'License and Release'];
  return (
    <>
      <ProgressBarList id="progressbar">
        { items.map((value, index) => {
          if (index + 1 < activeStep) {
            return <ProgressBarListItem className="active">{value}</ProgressBarListItem>;
          }
          if (index + 1 === activeStep) {
            return <ProgressBarListItem className="active" style={{ fontWeight: 'bold' }}>{value}</ProgressBarListItem>;
          }
          return <ProgressBarListItem>{value}</ProgressBarListItem>;
        })}
      </ProgressBarList>
    </>
  );
};
export default ProgressBar;
