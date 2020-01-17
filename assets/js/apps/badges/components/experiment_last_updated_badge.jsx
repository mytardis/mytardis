import React, {useEffect, useState} from "react";

import Badge from 'react-bootstrap/Badge'
import {fetchExperimentData} from './FetchData'

const ExperimentLastUpdatedBadge = ({experimentID}) => {
  const [lastUpdatedTime, setLastUpdatedTime] = useState("");

  useEffect(() => {
    fetchExperimentData(experimentID).then((data) => {
        setLastUpdatedTime(new Date(data.update_time).toDateString())
      })
  },[]);
  return(
    <Badge variant="info" content={"test"} title={"test"}>
      <i className="fa fa-clock-o"></i>&nbsp;
      {lastUpdatedTime}
    </Badge>
  )
};

export default ExperimentLastUpdatedBadge;