import React, { useEffect, useCallback } from 'react';
import Tabs from "react-bootstrap/Tabs";
import Tab from 'react-bootstrap/Tab';
import { OBJECT_TYPE_STICKERS } from '../../TabStickers/TabSticker'
import TypeSchemaList from '../type-schema-list/TypeSchemaList';
import { runSearch } from '../../searchSlice';
import { initialiseFilters, typeAttrSelector, allTypeAttrIdsSelector, updateActiveSchemas, updateTypeAttribute } from '../filterSlice';
import { useSelector, useDispatch, batch } from "react-redux";
import PropTypes from "prop-types";
import { mapTypeToFilter } from "../index";


function TypeAttributeFilter({typeId, attributeId}) {
  const attribute = useSelector(state => (typeAttrSelector(state.filters,typeId,attributeId)));
  const dispatch = useDispatch();
  const setFilterValue = value => {
    batch(() => {
      dispatch(updateTypeAttribute({
        typeId,
        attributeId,
        value
      }));
      dispatch(runSearch());
    });
  };
  const ApplicableFilter = mapTypeToFilter(attribute.data_type);
  return (
    <section>
      <h5>{attribute.full_name}</h5>
      <ApplicableFilter value={attribute.value} onValueChange={setFilterValue} />
    </section>
  )
}

TypeAttributeFilter.propTypes = {
  attribute: PropTypes.shape({
    data_type: PropTypes.string.isRequired,
    id: PropTypes.string.isRequired,
    full_name: PropTypes.string.isRequired  
  }),

}

export function PureFiltersSection({ types, schemas, typeSchemas, isLoading, error }) {
  const dispatch = useDispatch();

  if (isLoading) {
    return <p>Loading filters...</p>
  }
  if (error) {
    return <p>An error occurred while loading filters.</p>
  }
  if (!typeSchemas || !typeof typeSchemas == "object") {
    return null;
  }


  return (
    <section>
      <h3>Filters</h3>
      <Tabs defaultActiveKey="projects" id="filters-section">
        {
          types.allIds.map(type => {
            const Sticker = OBJECT_TYPE_STICKERS[type],
              schemaFiltersOptions = {
                schemas:
                {
                  allIds: typeSchemas[type],
                  byId: schemas.byId
                }
              },
              onActiveSchemaChange = useCallback(
                (value) => {
                  batch(() => {
                    dispatch(updateActiveSchemas({typeId: type ,value}));
                    dispatch(runSearch());
                  });
                }, [dispatch]),
              activeSchemas = useSelector((state) => (
                typeAttrSelector(state.filters, type, "schema").value
              )),
              attributeIds = useSelector(state => (
                // Get all type attributes IDs except for schema.
                allTypeAttrIdsSelector(state.filters,type).filter(filterId => (filterId !== "schema"))
              ));
            return (
              <Tab eventKey={type} title={<Sticker />}>
                {attributeIds.map(
                  id => (
                    <>
                    <TypeAttributeFilter typeId={type} attributeId={id} />
                    <hr />
                    </>
                  )
                )}
                <TypeSchemaList
                  value={activeSchemas}
                  options={schemaFiltersOptions}
                  onValueChange={onActiveSchemaChange}
                />
              </Tab>
            );
          })
        }
      </Tabs>
    </section>
  )
}

PureFiltersSection.propTypes = {
  types: PropTypes.shape({
    byId: PropTypes.object.isRequired,
    allIds: PropTypes.array.isRequired
  }),
  schemas: PropTypes.shape({
    byId: PropTypes.object.isRequired,
    allIds: PropTypes.array.isRequired
  }),
  typeSchemas: PropTypes.object,
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