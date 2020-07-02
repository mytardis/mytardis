import React from 'react';
import Tabs from "react-bootstrap/Tabs";
import Tab from 'react-bootstrap/Tab';
import { OBJECT_TYPE_STICKERS } from '../../TabStickers/TabSticker'
import TypeSchemaList from '../type-schema-list/TypeSchemaList';
import { useSelector } from "react-redux";


const objectTypes = ["projects","experiments","datasets","datafiles"];

export default function FiltersSection({filters}) {
    return (
      <Tabs defaultActiveKey="projects" id="filters-section">
        {
          objectTypes.map(type => {
            console.log(options, activeSchemas);
            const Sticker = OBJECT_TYPE_STICKERS[type],
                options = {schemas: filters.schemaParameters[type]},
                activeSchemas = filters.typeAttributes[type].schema;
            return (
              <Tab eventKey={type} title={<Sticker />}>
                <TypeSchemaList value={activeSchemas} options={options} />
              </Tab>
            );
          })
        }
      </Tabs>
    )
}