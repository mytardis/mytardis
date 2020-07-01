import React from 'react';
import Tabs from "react-bootstrap/Tabs";
import Tab from 'react-bootstrap/Tab';

export default function FiltersSection() {
    return (
      <Tabs defaultActiveKey="projects" id="filters-section">
        <Tab eventKey="projects" title="Projects">
        </Tab>
        <Tab eventKey="experiments" title="Experiments">
        </Tab>
        <Tab eventKey="datasets" title="Datasets">
        </Tab>
        <Tab eventKey="datafiles" title="Datafiles">
        </Tab>      
      </Tabs>
    )
}
