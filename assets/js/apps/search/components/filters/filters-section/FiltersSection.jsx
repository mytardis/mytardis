import React, { Fragment } from "react";
import Tabs from "react-bootstrap/Tabs";
import Tab from "react-bootstrap/Tab";
import { OBJECT_TYPE_STICKERS } from "../../TabStickers/TabSticker";
import TypeSchemaList from "../type-schema-list/TypeSchemaList";
import { runSearch } from "../../searchSlice";
import { typeSelector, updateTypeAttribute, typeAttrFilterValueSelector } from "../filterSlice";
import { useSelector, useDispatch, batch } from "react-redux";
import PropTypes from "prop-types";
import { mapTypeToFilter } from "../index";
import QuickSearchBox from "../../QuickSearchBox";


function TypeAttributeFilter({ typeId, attributeId }) {
    const attribute = useSelector(state => (typeSelector(state.filters, typeId).attributes.byId[attributeId]));
    const filterValue = useSelector(state => typeAttrFilterValueSelector(state.filters, typeId, attributeId));
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
            <h3 className="h6">{attribute.full_name}</h3>
            <ApplicableFilter id={typeId + "." + attributeId} value={filterValue} onValueChange={setFilterValue} options={attribute.options} />
        </section>
    );
}

TypeAttributeFilter.propTypes = {
    typeId: PropTypes.string.isRequired, 
    attributeId: PropTypes.string.isRequired,
};

export function TypeAttributesList({ typeId }) {
    const attributeIds = useSelector(state => {
        const typeAttributes = typeSelector(state.filters, typeId).attributes;
        // Get all type attributes IDs except for schema.
        return typeAttributes.allIds
            .filter(filterId => (filterId !== "schema"))
        // Then, filter out ones that are marked not filterable.
            .filter(id => typeAttributes.byId[id].filterable)
    });

    return (
    <>
      {
          attributeIds.map(
              id => (
                  <Fragment key={id}>
                      <TypeAttributeFilter typeId={typeId} attributeId={id} />
                      <hr />
                  </Fragment>
              )
          )
      }
    </>
    );
}

TypeAttributesList.propTypes = {
    typeId: PropTypes.string.isRequired
};

export function PureFiltersSection({ types, schemas, typeSchemas, isLoading, error }) {

    if (isLoading) {
        return <p>Loading filters...</p>;
    }
    if (error) {
        return <p>An error occurred while loading filters.</p>;
    }
    if (!typeSchemas || !typeof typeSchemas === "object") {
        return null;
    }


    return (
        <section>
            <Tabs defaultActiveKey="project" id="filters-section">
                {
                    types.allIds.map(type => {
                        const Sticker = OBJECT_TYPE_STICKERS[type];

                        return (
                            <Tab key={type} eventKey={type} title={<Sticker />}>
                                <QuickSearchBox typeId={type} />
                                <hr />
                                <TypeAttributesList typeId={type} />
                                <TypeSchemaList typeId={type} />
                            </Tab>
                        );
                    })
                }
            </Tabs>
        </section>
    );
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
    error: PropTypes.string
};

export default function FiltersSection() {
    const filters = useSelector((state) => (state.filters));
    return (<PureFiltersSection {...filters} />);
}