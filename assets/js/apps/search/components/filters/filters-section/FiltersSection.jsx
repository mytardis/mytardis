import React, { useEffect } from 'react';
import Tabs from "react-bootstrap/Tabs";
import Tab from 'react-bootstrap/Tab';
import { OBJECT_TYPE_STICKERS } from '../../TabStickers/TabSticker'
import TypeSchemaList from '../type-schema-list/TypeSchemaList';
import { initialiseFilters } from '../../filterSlice';
import { useSelector, useDispatch } from "react-redux";
import PropTypes from "prop-types";


const objectTypes = ["projects", "experiments", "datasets", "datafiles"];

function FilterTab({}) {

}

export function PureFiltersSection({ filtersByKind, isLoading, error }) {
  if (isLoading) {
    return <p>Loading filters...</p>
  }
  if (error) {
    return <p>An error occurred while loading filters.</p>
  }
  if (!filtersByKind || !typeof filtersByKind == "object") {
    return null;
  }
  return (
    <section>
      <h3>Filters</h3>
      <Tabs defaultActiveKey="projects" id="filters-section">
        {
          objectTypes.map(type => {
            const Sticker = OBJECT_TYPE_STICKERS[type],
                  schemaFiltersOptions = { schemas: filtersByKind.schemaParameters[type] },
                  activeSchemas = filtersByKind.typeAttributes[type].schema;
            return (
              <Tab eventKey={type} title={<Sticker />}>
                <TypeSchemaList value={activeSchemas} options={schemaFiltersOptions} />
              </Tab>
            );
          })
        }
      </Tabs>
    </section>
  )
}

PureFiltersSection.propTypes = {
  filtersByKind: PropTypes.object,
  isLoading: PropTypes.bool.isRequired,
  error: PropTypes.object
}

export default function FiltersSection() {
  const dispatch = useDispatch();
  const filters = useSelector((state) => (state.filters));
  useEffect(() => {
    //Load schema filters
    dispatch(initialiseFilters());
  }, [dispatch]);
  return (<PureFiltersSection {...filters} />);
}